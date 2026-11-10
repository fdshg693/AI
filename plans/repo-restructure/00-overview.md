---
type: Plan
status: implementing-in-progress
---

## 実装ステータス

- [x] [01-research-platform-constraints.md](01-research-platform-constraints.md) — Junction・サブモジュール・各ツールの挙動の事前調査
- [x] [02-research-inventory.md](02-research-inventory.md) — 全スキル・ツール・docs の分類表とパス参照の棚卸し
- [x] [03-fix-existing-inconsistencies.md](03-fix-existing-inconsistencies.md) — 移動前に既存の不整合を直す
- [x] [04-links-tooling.md](04-links-tooling.md) — Junction マニフェスト仕様と作成・検証ツール、スキャナの Junction 除外
- [x] [05-semantic-reorg.md](05-semantic-reorg.md) — 単一リポジトリのまま意味的再編（git mv）
- [x] [06-agent-compat.md](06-agent-compat.md) — マルチ AI 対応の分離、ツール別書式サンプルと相違点ドキュメント
- [x] [07-submodule-split.md](07-submodule-split.md) — 履歴付きでサブモジュールへ切り出す
- [ ] [08-subfolder-workspaces.md](08-subfolder-workspaces.md) — サブモジュール単体で開くための Claude Code 用 Junction・指示ファイル
- [ ] [09-docs-and-rules.md](09-docs-and-rules.md) — README・AGENTS.md・docs・探索スキルの最終更新

# リポジトリ再編（意味的分割＋サブモジュール化）実装プラン - 概要

> 元の依頼・検討した案・現状調査は [rough/01-initial-idea.md](rough/01-initial-idea.md)。

## 要件

- モノレポ（アンブレラリポジトリ）は維持したまま、大きな単位を Git サブモジュールに切り出す。サブモジュール単位でコミットできるようにする。
- サブモジュールのフォルダだけを Claude Code で開いて作業できるようにする。必要なスキル・ルール・強く関連する上位／兄弟フォルダは Junction で参照する。サブモジュールを単体で clone した場合に Junction が壊れるのは許容する。
- 意味的に分ける: (a) レポジトリ都合（meta）と汎用、(b) tools 付属スキルと tools 非依存スキル、(c) マルチ AI 対応の仕組みとサンプル、(d) Claude Code スキルを主軸にし、他ツールとの相違点は別軸のドキュメントにまとめる。
- 既存の不整合（実在しないパス参照、綴り誤り、矛盾する README 等）を解消する。

## 目標の構成（01/02 の調査結果で確定。スキル単位の対応表は [progress/02-mapping.md](progress/02-mapping.md)）

```text
AI/                                 アンブレラ（fdshg693/AI のまま）
├─ AGENTS.md / CLAUDE.md / README.md
├─ registry/                        SSOT yaml 群（ai-tools / repo-tools / meta_field / skill-tags / repo-workflows / repo-hooks）。ルートには旧 skill-tools 向けの生成コピー 4 本
├─ .claude/ .claude-plugin/ .agents/ .github/ .cline/ .kilo/ .codex/ .cursor/
│                                   ツールがワークスペース直下から読む設定。ルートに残す（中身は生成物か Junction）
├─ maintenance/                     レポジトリ都合。アンブレラ本体に残す（サブモジュールにしない）
│  ├─ plugin/                       旧 meta-plugins（committing, meta, exploring-this-repo …）
│  ├─ scripts/                      旧 tools/internal（カタログ生成・pre-commit・links ツール）
│  └─ docs/                         旧 docs/repo-wide
├─ plans/
├─ skills/        [submodule]       Claude Code 汎用スキル（tools 非依存）
│  └─ plugins/
│     ├─ cc-knowledge/              旧 claude-plugins/meta（Claude Code の知識・書き方。`claude-` で始まる名前は予約語のため）
│     ├─ coding/ cicd/ topics/ others/ special/ subagents/ no-code/ web-lookup/ doc-tools/
│     └─ ai-tools-knowledge/        旧 codex/copilot/cursor/antigravity/cline/kilo の知識スキル（Claude Code スキルとして）
├─ tools/         [submodule]       CLI 群（tools/<name> の平坦配置は維持。旧 tools/internal/ai-usage → tools/ai-usage）
│  └─ _plugin/my-tools/skills/      tools 付属スキル（旧 claude-plugins/my-tools、skill-tools-cli・task-tracker・parallel-agent-worktree を含む）
├─ agent-compat/  [submodule]       このレポジトリのマルチ AI 対応
│  ├─ agent-tooling/                フック・コンテキスト注入（旧 agent-tooling）
│  ├─ formats/<tool>/               ツール固有書式の最小サンプル（skill / plugin / rule / agent）
│  └─ docs/differences/             Claude Code との書き方の相違点（別軸）
└─ site/          [submodule]       skills-site / tools-site
```

## 実装ステップ

0. **前提条件（2026-11-10 完了）**: `c:\C\ai` で `git init` し、secretlint で全ファイルに問題が無いことを確認して初回コミット `71336a9` を作成した。lefthook も導入済み。`.gitattributes` が LF に正規化するため、作業コピー内の CRLF のファイルは次に触れたときに LF の差分として出る。05 の移動差分と混ざらないよう、03 の前に `git add --renormalize .` を 1 コミットにしておく予定だったが、インデックスは既に全て LF で不要だった（03 で確認。CRLF は作業コピーだけで差分にならない）。
1. [01-research-platform-constraints.md](01-research-platform-constraints.md) — Junction × Git／Claude Code／Python／rg 等の挙動、サブモジュール × マーケットプレイス／CI／uv・pnpm workspace の制約を調べる。観点 D は構成全体の go/no-go 判定
2. [02-research-inventory.md](02-research-inventory.md) — 全 SKILL.md・tools・docs を分類し、移動先対応表とパス参照の一覧を作る（分類は 01 と並行可。移動先の確定は 01 の観点 D に依存）
3. [03-fix-existing-inconsistencies.md](03-fix-existing-inconsistencies.md) — 移動前に壊れた参照・綴り誤り・空フォルダを直す（前提条件のあと、01/02 と並行可）
4. [04-links-tooling.md](04-links-tooling.md) — Junction マニフェスト仕様と `links` ツール。全スキャナを Junction・生成コピーに対して安全にする（01 に依存）
5. [05-semantic-reorg.md](05-semantic-reorg.md) — 対応表どおりに `git mv` し、SSOT・生成器・CI・site・外部契約・追跡外ファイルを追従させる（01・02・03・04 に依存）
6. [06-agent-compat.md](06-agent-compat.md) — マルチ AI 対応を `agent-compat/` に集約し、書式サンプルと相違点ドキュメントを作る（04・05 に依存。05 のバッチ 5 とは同じコミットで行う）
7. [07-submodule-split.md](07-submodule-split.md) — `git filter-repo` で履歴付きに切り出し、`.gitmodules`・CI・lefthook を整える（04・05・06 に依存）
8. [08-subfolder-workspaces.md](08-subfolder-workspaces.md) — 各サブモジュールの CLAUDE.md・`.claude/skills` Junction・links マニフェストを整え、単体で開いて確認する（07 に依存）
9. [09-docs-and-rules.md](09-docs-and-rules.md) — 全体ドキュメントを最終構成に合わせる（08 に依存）

## 主要な決定事項

| 決定                                                                                                                                                                       | 理由                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 意味的再編（05・06）を単一リポジトリ内で先に済ませ、サブモジュール化（07）は最後                                                                                           | 移動が 1 リポジトリで完結し、既存の生成・検査で検証できる。境界を誤ったまま切り出すと、後の移動がリポジトリをまたぐ                                               |
| Junction はコミットしない。サブモジュールごとの宣言ファイル（`.links.yaml`）をコミットし、アンブレラの `links` ツールで作成・検証・除去する                                | Git は Junction を正しく追跡できない。宣言ファイルなら単体 clone 時に参照先が無いことも明示できる                                                                 |
| Junction パスはスクリプトが各リポジトリの exclude ファイルに登録する。書き先は `git rev-parse --git-path info/exclude` で求める                                            | `.gitignore` をコミットで汚さない。サブモジュールの `.git` はファイル（`gitdir:`）なので、パスを直書きできない                                                    |
| アンブレラのルートは、アンブレラにコミットする目印ファイル（例: `.umbrella-root`）で判定する                                                                               | `.gitmodules` は 07 まで存在しないため、04〜06 の間に使えない                                                                                                     |
| Junction の参照先は兄弟・他サブツリーに限る。自分の祖先は指さない。Junction の中の Junction も指さない。参照先は「自分が属するアンブレラのルート配下」でなければならない   | 祖先を指すと再帰走査が無限ループになる。連鎖すると解決順に依存する。フォルダのコピーや移動で、別の場所を指したままの Junction が残る事故を防ぐ                    |
| SSOT yaml はルートから `registry/` に集める（ユーザー回答）                                                                                                                | Junction はディレクトリにしか張れない。サブモジュール単体で開いても SSOT を参照できるようにする                                                                   |
| skills-site の URL 変更は許容し、リダイレクトは作らない（ユーザー回答）                                                                                                    | canonical ID がパス由来のため、移動で URL が変わるのは避けられない                                                                                                |
| git worktree は使わず、作業は直列で行う（ユーザー回答）                                                                                                                    | Junction の絶対パスと worktree・サブモジュールの組み合わせの複雑さを避ける                                                                                        |
| Junction を `rm -rf`／`Remove-Item -Recurse` で消すことを禁止し、`just links-clean` だけで外す                                                                             | 参照先の中身まで消えるおそれがある                                                                                                                                |
| `git mv` の対象外（ignore 対象の `.env`・`.venv`・`logs/`・`fb/`・`state/`・sqlite 等）は、05 で移設し、07 で退避してから置き換える                                        | `git mv` は追跡中のファイルしか動かさない。07 でフォルダを clone に置き換えると消える                                                                             |
| レポジトリ都合のもの（meta-plugins、tools/internal、docs/repo-wide）は `maintenance/` に集め、アンブレラ本体に残す                                                         | アンブレラ自身の保守用であり、切り出しても単体では意味を持たない                                                                                                  |
| 他ツールの「知識スキル」（codex-docs、antigravity-memory 等）は Claude Code スキルとして `skills/` に置く。ツール固有書式のサンプルだけを `agent-compat/formats/` に分ける | 依頼の (c)(d)。中身は普通の SKILL.md であり、置き場所だけがツール別に散っていた                                                                                   |
| `tools/<name>` の平坦配置と `repo-tools.yaml` の `path` 契約は維持する（`tools/internal` だけ外へ出す）                                                                    | 公開インストール手順（`uv tool install --editable tools/<name>`）が契約になっている（[tools-directory-layout](../../maintenance/docs/tools-directory-layout.md)） |
| 横断的な集約生成物（marketplace.json、skill-catalog.json 等）はアンブレラが生成・所有する。各サブモジュールは自分の中の生成物（プラグイン単位の CATALOG.md 等）だけを持つ  | サブモジュールのコミットが他リポジトリのファイルを書き換えると、アトミックに commit できない                                                                      |

## ユーザー回答済みの判断（2026-11-10）

- **作業する clone**: このローカルフォルダ `c:\C\ai` 自身で行う。ただし現時点で `.git` が無い（`git status` が失敗する）ため、Git 管理下に戻す方法を前提条件として確定させる（下の未決事項 3）。
- **SSOT yaml の置き場**: `registry/` に集める（05 のバッチ 2）。外部契約の移行措置は 05 で行う。
- **skills-site の URL**: 変わってよい。リダイレクトは用意しない。
- **git worktree**: 使わない。作業は直列で行う。links ツールは worktree を考慮しなくてよい（参照先がアンブレラ配下かの検査は、コピーや移動の事故対策として残す）。

- **Git 管理**: `git init` で新しく始める（履歴は引き継がない）。07 の切り出しも履歴なしでよい。
- **サブモジュールの粒度**: skills / tools / agent-compat / site の 4 つ。ただし 01 の go/no-go 判定で不可となった場合は、代替構成を添えて再確認する。→ **01 の判定は GO（2026-11-10）**。集約 marketplace のエントリは `git-subdir`（Claude Code・Codex）／`github`+`path`（Copilot）でサブモジュール側リポジトリを直接指す。前提として skill-tools の GitHub ソースのサブモジュール対応が要る（07）。
- **GitHub リポジトリ**: 「AI」の名前で public。

## 未決事項（ユーザー判断が必要）

1. ~~**GitHub リポジトリ名の詳細**~~ → 解決（2026-11-10、07）: アンブレラ `fdshg693/AI`、サブモジュール `AI-skills`／`AI-tools`／`AI-agent-compat`／`AI-site`、すべて public で作成・push した（ユーザー回答: 検査が通れば都度 push してよい）。

## 変更/新規ファイル一覧

（詳細・読むべきファイルは各ステップを参照）

### 新規

- `maintenance/scripts/links/`（Junction 作成・検証・除去ツール）と `justfile` レシピ `links-*`
- 各サブモジュールの `.links.yaml`、`CLAUDE.md`／`AGENTS.md`、`.claude/settings.json`
- `agent-compat/formats/<tool>/`、`agent-compat/docs/differences/`
- `.gitmodules`、`maintenance/docs/repo-layout.md`（新しい構成と境界の規約）

### 変更（移動を含む）

- `claude-plugins/**` → `skills/plugins/**`、`tools/_plugin/**`
- `meta-plugins/**`、`tools/internal/**`、`docs/repo-wide/**` → `maintenance/**`
- `codex-plugins/`、`copilot-plugins/`、`cursor-plugins/`、`_agents/`、`.cline/skills/`、`.kilo/skills/` → `skills/plugins/ai-tools-knowledge/` と `agent-compat/formats/`
- `cline-plugins/personal-info` → `agent-compat/formats/cline/personal-info`（02 で決定）
- ユーザー設定 `~/.claude/settings.json`（`extraKnownMarketplaces`、`statusLine` は既に存在しないパス `C:/CodeRoot/AI/tools/internal/ai-usage/...` を指している。ai-usage は `tools/ai-usage` へ移す）— リポジトリ外。ユーザーに確認してから変更する
- `agent-tooling/` → `agent-compat/agent-tooling/`
- `ai-tools.yaml` ほか SSOT yaml、`pyproject.toml`、`pnpm-workspace.yaml`、`lefthook.yml`、`justfile`、`.github/workflows/*.yml`
- `tools/internal/plugin_meta/**` の生成器、`site/skills-site/scripts/**`、`tools/skill-tools`（パス既定値）
- `README.md`／`README_EN.md`／`AGENTS.md`、`docs/**`、`meta-plugins/skills/exploring-this-repo` ほか meta スキル

### 削除

- `antigravity-plugins/`（README のみ）、`.kilo/skills/kilo-test-guide`（空）、`.kilo/skills/using-kilo-cli`（残骸）、移動後に空になる旧ルートフォルダ

## ルール更新ポイント

- ルート `AGENTS.md`（05 で暫定、09 で確定）: パス参照（`meta-plugins\skills\...` 等）を新パスへ。「Junction は `.links.yaml` で宣言し `just links-sync` で作る。直接 `mklink` しない」を追記。
- `maintenance/docs/repo-layout.md`（04 で新規、09 で確定）: 境界の判断基準（汎用／tools 付属／meta／マルチ AI 対応／サンプル）、Junction の規約（祖先禁止・連鎖禁止・exclude 登録）、生成物の所有権。
- `docs/repo-wide/claude-code-first-skills.md`・`tool-companion-skills.md`・`tools-directory-layout.md`・`ai-tools-config.md`（05・06）: 新しい置き場と方針に合わせて改稿。
- 各サブモジュールの `AGENTS.md`（08。`tools/AGENTS.md` など既存のものは変更）: そのサブモジュール単体で開いたときの前提（アンブレラ必須、Junction の作り方）。
- ルート `AGENTS.md`（04）: Junction を再帰削除コマンドで消さないこと。
- `maintenance/docs/` の `skill-tools-contract.md`・`skill-meta-fields.md`・`repo-ssot-pattern.md`・`repo-tools-config.md`・`uv-workspace.md`・`skill-md-commits.md`（05・07）: 外部契約、canonical ID、registry 移動、workspace、2 段階コミット。
- 移動するネストした `AGENTS.md`／`CLAUDE.md`（`tools/`、`tools/internal/`、`docs/`、`agent-tooling/`、`site/skills-site/`、`.claude/hooks/`、`plans/`）（05）: 中のパス参照を追従させる。AGENTS.md から生成するルール（`agents-rules`）は 09 で再生成する。

## 進め方

- **TODO 化**: ステップ一覧の各項目を 1 TODO にする。05 は移動のまとまり（カテゴリ）ごとに 1 コミットへさらに分ける。各ステップの実行主体・粒度は各ステップファイルの「進め方」に書く。
- **並行作業への配慮**: 他のエージェント・ユーザーが同時に作業する前提なので、05〜07 は事前にユーザーへ告知し、各バッチを短時間で `git mv` → 検査 → コミットまで終える。自分が行っていない変更は戻さない。
- **外部向け操作**（GitHub リポジトリ作成・push・リダイレクト公開）はそのたびにユーザーの確認を取る。

### コミット方針（全ステップ共通）

- **いつ**: 各ステップの「進め方」の TODO 1 つが終わり、その TODO の検査が通った時点で 1 コミットする。検査が通らない途中状態はコミットしない。複数 TODO をまとめて 1 コミットにしない。各ステップのコミット単位は、そのステップの「進め方」の「コミット」に書く。
- **プランの更新**: ステップの完了時に、`status`・実装ステータスのチェック・「実行中に判明した変更」・progress・後続ステップへの反映を、`docs(plans): ...` の 1 コミットにする。実装のコミットには混ぜない。
- **生成物の残り**: lefthook が再生成・整形したファイルがコミット後に残ったら、直後に `chore(repo): sync generated files after hooks` で追加コミットする（`committing` スキルの手順 8）。
- **手順**: `committing` スキルのラッパー（`meta-plugins/skills/committing/scripts/commit.py`、05 以降は `maintenance/plugin/...`）を使う。生の `git commit`・`--no-verify` は使わない。commitlint の制約で本文は 1 行 100 文字以内。件名・本文・`Co-Authored-By` 行は別々の `-m` で渡す。
- **他人の変更**: 自分が作っていない変更（未ステージ・ステージ済みとも）はコミットに含めない。インデックスに他人のステージ済み変更があるときは `git diff --cached --binary -- <paths> > patch` で退避し、`git restore --staged -- <paths>` で外してからコミットし、終わったら `git apply --cached patch` で戻す。`git commit -- <paths>` はリネームの削除側を拾えないので使わない。
- **push しない**: push はユーザーが明示したときだけ（07 の新リポジトリへの push もそのたびに確認する）。
