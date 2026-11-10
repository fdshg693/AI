---
type: Plan Step
status: implementing-done
---

# Step 4: Junction マニフェスト仕様と links ツール、スキャナの Junction 除外

> [00-overview.md](00-overview.md) の続き。01 の観点 A（Git × Junction）と C（スキャナ × Junction）の結果を受けて確定させる。05 の移動より前に作れば、05 の途中から使える。

## やること

- Junction を宣言するマニフェスト `.links.yaml` の仕様を決める。どのリポジトリ（アンブレラ・各サブモジュール）にも置ける形にする。
- アンブレラに `links` ツールを作る。宣言から Junction を作成（`sync`）、状態を検査（`check`：参照先が無い・宣言外の Junction がある・実体ディレクトリが既にある）、除去（`clean`）する。作成した Junction のパスは、そのリポジトリの `.git/info/exclude` の管理ブロックへ書く。
- リポジトリ内で `**/SKILL.md` などを再帰走査する全ツールを、Junction を辿らないように直す（二重計上・無限ループの防止）。

## 読むべきファイル

### マニフェスト仕様を決めるため

- 01 の調査結果（Git が Junction をどう扱うか、`.git/info/exclude` で十分か）
- `tools/internal/AGENTS.md`、`tools/internal/justfile`（内部ツールの置き方・レシピの命名）
- `docs/repo-wide/justfile-conventions.md`、`docs/repo-wide/repo-ssot-pattern.md`

### Junction 除外が必要な走査箇所（01 の観点 C で列挙したもの。file:line は [progress/01-research-results.md](progress/01-research-results.md)）

- `tools/internal/skill/util/skill_frontmatter.py` の `find_skill_md_files`（`os.walk`。`set_*`・`check_skill_repo_tools.py`・`skill_tool_graph.py` が呼ぶ）
- `tools/internal/plugin_meta/generate/*`（`iterdir` 1 段。`skills/` 直下の Junction だけ拾う）
- `tools/skill-tools/skill_tools/source/__init__.py`（git の無いときの `os.walk` 経路と include 候補、`_resolve` の `is_relative_to`）、`install/installer.py`、`install/manifest.py`（`is_symlink()` 防御が Junction をすり抜ける）
- `agent-tooling/.../adapters/claude/common/skill_frontmatter.py`、`recommend_skills.py`、`sources/claude_rules.py`、`checks/agent_context.py`、`hooks/scenarios/scoped_rules/discovery.py`（`rglob`）と、その生成物 `hooks/generated/**`。`core/sessions.py`（`os.path.islink`）
- `site/skills-site/scripts/patch-csp-header.mjs`（dist が対象なので低優先）。`publication-core.mjs` は既に安全
- `tools/agents-rules/agents_rules/**`、`agent-tooling/agent_tooling/core/discovery.py`、`sources/agents_md.py`（01 では未調査。本ステップで走査方法を確認する）
- 修正不要と判明: prettier・ruff（辿らない）、rg 既定・textgraph・codegraph・lefthook（git の一覧と exclude に従う）

## 触るファイル

- 新規: アンブレラの目印ファイル `.umbrella-root`
- 新規: `tools/internal/links/`（05 で `maintenance/scripts/links/` へ移る。最初から移動先に作るかは 05 の順序で決める）、`tools/internal/justfile` に `links-sync`／`links-check`／`links-clean` レシピ、ルート `justfile` に入口レシピ
- 新規: `.links.yaml` のスキーマ説明（`maintenance/docs/repo-layout.md` の 1 節）
- 変更: 上の走査箇所。共通の「Junction／reparse point なら辿らない」判定を Python 側は 1 か所の util に置き、JS 側も同様にする
- 変更: `.prettierignore`、`pyproject.toml`（ruff `extend-exclude`、pytest `norecursedirs`）など、01 で辿ると判明したツールの除外設定

## 決定事項・注意点／落とし穴

- マニフェストの形（案）: `links:` の各要素は `path`（宣言したリポジトリのルートからの相対）、`target`（アンブレラのルートからの相対）、`why`（1 行）。アンブレラのルートは、アンブレラにコミットする目印ファイル（`.umbrella-root`）を持つ最も近い祖先として求める（`.gitmodules` は 07 まで無いので使わない）。
- exclude の書き先は `git rev-parse --git-path info/exclude` で求める。サブモジュールの `.git` はファイルなので `.git/info/exclude` を直書きしない。
- `check` は、既存の Junction の参照先が「自分が属するアンブレラのルート配下」かを検査する。フォルダのコピーや移動で、元の場所を指したままの Junction を検出するため。worktree は使わない（ユーザー回答）ので、worktree 対応は作らない。
- 06 で生成するコピー（`.cline/skills` 等）も二重計上の原因になる。生成先を、Junction と同じ除外の仕組みでスキャナから外す。
- 参照先がアンブレラ内に無い場合（サブモジュール単体 clone）は、`sync` は警告して飛ばす。失敗にしない（依頼の「利用者の責任」）。
- 禁止事項をツールで検査する: 祖先を指す、Junction の中を指す、他の宣言と重なる、`path` に実体ファイルが既にある。
- **exclude 登録は必須（01-A）**: Git は Junction を実ディレクトリとして辿り、中身を 100644 でステージする。`sync` は exclude（`git rev-parse --path-format=absolute --git-path info/exclude`）へ `/path/` 形式で書けた場合だけ Junction を作る。`check` は「exclude に無い Junction」をエラーにする（exclude が無いと、中身の一部が ignore のとき `git clean -fd`／`-fdX` が参照先のファイルを個別に消すことを実験で確認）。exclude があれば `git clean -fdx`／`-fdX` で消えるのは Junction だけで参照先は無事。消えた Junction は `sync` で作り直す。
- **checkout／switch の危険（01-A）**: exclude 済みの Junction と同じパスを実ディレクトリとして追跡しているコミットへ `switch` すると、参照先の同名ファイルが無警告で上書きされ、戻ると参照先から削除される。05 は「実ディレクトリだったパスを Junction にする」再編なので必ず当たる。対策: (1) Junction のパスは過去に追跡されていたパスと重ねない、(2) 古いコミットを checkout する前に `just links-clean`、後で `just links-sync` する手順を repo-layout に書く、(3) `post-checkout` フックで「追跡ファイルと Junction の衝突」を検出して警告する（どちらを入れるかは本ステップで決める）。`--no-overwrite-ignore` を付ければ中断するが設定キーにはできない。`git stash -a` は Junction を実ディレクトリのコピーに化けさせるので使わない。
- **データ消失リスク**: Junction を `Remove-Item -Recurse`／`rm -rf`／`shutil.rmtree` で消さない。`clean` は `cmd /c rmdir <link>`、`[System.IO.Directory]::Delete(path, false)`、Python なら `is_junction()` を確認してから `os.rmdir` を使う（`cmd /c rmdir` で参照先が無事なことは 01 で確認済み）。
- **Python の Junction 判定（01-C）**: `Path.is_symlink()`／`os.path.islink()` は Junction で False、`os.walk(followlinks=False)`・`rglob` も辿る。共通 util は `is_link_like(p) = p.is_symlink() or p.is_junction()` と、`os.walk` の `dirnames` から link-like を除く walk を提供する。`Path.walk()` 既定は辿らないので置き換え先に使える。JS 側は `fs.readdirSync` の Dirent が Junction で `isSymbolicLink()` true なので既存の判定で足りる。tinyglobby／fast-glob を使う箇所は `followSymbolicLinks:false` を明示する。
- **走査箇所の優先度（01-C）**: 書き込みを伴う `find_skill_md_files`（`set_*` 系が同じ実体に二重書き込みする恐れ）と、コピー・削除を伴う skill-tools の `installer.py`／`manifest.py` が最優先。次に agent-tooling の `rglob` 系（実行時フック）と `sessions.py` の `islink`。git の一覧に頼る経路（skill-tools 通常経路、textgraph、codegraph、lefthook、rg 既定）は exclude があれば安全なので修正不要。prettier・ruff は辿らないので除外設定は不要。pytest は祖先 Junction で止まらないので、`testpaths` を限定していることを確認する。
- Junction は作成時に絶対パスを持つ。アンブレラを移動・コピーすると壊れるので、`check` で検出して `sync` で作り直せるようにする。
- ファイルは Junction にできない。ファイル単体を参照したいときは、ディレクトリ単位で参照するか、`@` import（Claude Code の指示ファイル）で済ませる。シンボリックリンクは開発者モードが前提になるので使わない。
- 走査の修正は、移動が始まる前に入れてテストを通しておく。05 の途中で Junction を作った瞬間に生成物が二重計上されるのを防ぐため。

## ルール更新ポイント

- `maintenance/docs/repo-layout.md`（本ステップで新規。05 の前なら `docs/repo-wide/repo-layout.md` に置き、05 で一緒に移す）: `.links.yaml` の仕様と禁止事項、`just links-sync` を使い直接 `mklink` しないこと。
- ルート `AGENTS.md`: 「Junction は `.links.yaml` で宣言し `just links-sync` で作る。`rm -rf`／`Remove-Item -Recurse` で消さず `just links-clean` を使う」を追記。

## 進め方

- **実行主体**: メインが仕様とツールを書く。走査箇所の修正は箇所ごとに独立しているので、サブエージェントへ並列委任してよい（共通 util の API はメインが先に決める）。
- **TODO 化**: (1) 仕様と links ツール、(2) Python 走査箇所の修正、(3) JS 走査箇所と除外設定、(4) `temp/` の実験リポジトリで sync/check/clean とスキャナの二重計上なしを確認、の 4 TODO。
- **コミット**: (1)〜(3) をそれぞれ 1 コミット（`feat(links): ...`／`fix(scanners): ...`）。(4) の実験は `temp/`（gitignore）で行うのでコミットは無い。結果で直した箇所があれば `fix:` で 1 コミット。ステップ完了時にプラン更新を 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（01 完了時）: 01-A・C の結果から、exclude 登録の必須化、checkout／switch 時の参照先破損への対策、Python の Junction 判定（`is_junction()`）、走査箇所の具体化と優先度を「決定事項」「読むべきファイル」に反映した。status を `planning-breakdown` に進めた。
- 2026-11-10（04 完了時）: 実装した。詳細は [progress/04-links-results.md](progress/04-links-results.md)。links ツールと repo-layout は移動前の場所（`tools/internal/links/`、`docs/repo-wide/repo-layout.md`）に置いた。checkout 対策は手順＋lefthook `post-checkout` の事後警告。`is_link_like` は配布単位ごとに同じ実装を持つ（1 か所の util にはしない）。pytest はルート `conftest.py`。06 の生成コピーは Junction 判定では除外できないので 06 へ申し送った。
