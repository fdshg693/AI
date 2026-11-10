---
type: Plan Step
status: planning-research
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

### Junction 除外が必要な走査箇所（01 の観点 C で列挙したもの）

- `tools/internal/plugin_meta/**`（カタログ・マーケットプレイス生成）
- `tools/internal/skill/**`（meta フィールド検査・版数バンプ）
- `site/skills-site/scripts/*.mjs`（`build-catalog.mjs`、`publication-core.mjs`）
- `tools/skill-tools/skill_tools/**`（ローカルソースの走査）
- `agent-tooling/agent_tooling/core/discovery.py`、`sources/agents_md.py`（ネスト AGENTS.md の探索）
- `tools/agents-rules/agents_rules/**`（AGENTS.md の収集）
- `.prettierignore`、`pyproject.toml` の pytest／ruff 設定、`lefthook.yml` の glob、codegraph の除外設定、`.vscode/settings*.jsonc` の検索除外

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
- **データ消失リスク**: Junction を `Remove-Item -Recurse` で消すと参照先の中身が消えることがある。`clean` は Junction 自体だけを外す API（`[System.IO.Directory]::Delete(path, false)` 相当や `cmd /c rmdir`）を使い、実験で確かめる。`git clean -fdx` も同様に 01 で確かめた結果に従う。
- Junction は作成時に絶対パスを持つ。アンブレラを移動・コピーすると壊れるので、`check` で検出して `sync` で作り直せるようにする。
- ファイルは Junction にできない。ファイル単体を参照したいときは、ディレクトリ単位で参照するか、`@` import（Claude Code の指示ファイル）で済ませる。シンボリックリンクは開発者モードが前提になるので使わない。
- 走査の修正は、移動が始まる前に入れてテストを通しておく。05 の途中で Junction を作った瞬間に生成物が二重計上されるのを防ぐため。

## ルール更新ポイント

- `maintenance/docs/repo-layout.md`（本ステップで新規。05 の前なら `docs/repo-wide/repo-layout.md` に置き、05 で一緒に移す）: `.links.yaml` の仕様と禁止事項、`just links-sync` を使い直接 `mklink` しないこと。
- ルート `AGENTS.md`: 「Junction は `.links.yaml` で宣言し `just links-sync` で作る。`rm -rf`／`Remove-Item -Recurse` で消さず `just links-clean` を使う」を追記。

## 進め方

- **実行主体**: メインが仕様とツールを書く。走査箇所の修正は箇所ごとに独立しているので、サブエージェントへ並列委任してよい（共通 util の API はメインが先に決める）。
- **TODO 化**: (1) 仕様と links ツール、(2) Python 走査箇所の修正、(3) JS 走査箇所と除外設定、(4) `temp/` の実験リポジトリで sync/check/clean とスキャナの二重計上なしを確認、の 4 TODO。
