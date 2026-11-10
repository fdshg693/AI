---
type: Plan Step
status: implementing-done
---

# Step 3: 移動前に既存の不整合を直す

> [00-overview.md](00-overview.md) の続き。05 の大規模移動の前に、壊れた参照を正しい状態に戻しておく。移動と混ぜると、移動による破損と元からの破損を区別できなくなるため。前提条件（作業する clone の確定）を満たしたら、01・02 と並行して進めてよい。

## やること

調査時点で見つかった不整合を、移動を伴わない最小の変更で直す。02 の棚卸しで見つかったものも追加する。

- `tools/scheule/` → `tools/schedule/` に改名し、`pyproject.toml` の members（`tools/schedule` → 実体の `tools/schedule/ai-schedule`、`tools/issue-agent` → `tools/schedule/issue-agent`）と `tools/README.md`・ルート README の参照を直す。
- `pyproject.toml` の members `tools/aim-use/aim-summarize` が実在しない。削除済みなら外し、README・docs の `aim-use` 言及も直す（`repo-tools.yaml` のコメントにも言及あり）。
- README の `templates/`、`.clinerules/` の記述を実態に合わせる。`.clinerules` は `ai-tools.yaml` の `rules_from_agents_md.output_dir` が生成先なので、未生成なのか廃止なのかを確認して記述を合わせる。
- `.claude/rules/` は実在しないが、`agent-tooling` の `sources/claude_rules.py`・`hooks/scenarios/scoped_rules/`・生成された各ツール向け `scoped_rules.py`・`.codex/hooks/scoped_rules.py` とテストが読む入力契約。参照は外さない。「現在は空でよい（任意の入力）」ことがドキュメントから読み取れるかだけを確認し、必要なら追記する。
- `.agents/README.md` と `_agents/README.md` の Antigravity 配置の説明の矛盾を解消する（05・06 で消えるフォルダなので、最小限の修正でよい）。
- 空・残骸のフォルダを削除する: `.kilo/skills/kilo-test-guide`、`.kilo/skills/using-kilo-cli`、`antigravity-plugins/`（ai-tools.yaml の readme ブロックから除いて README を再生成）。
- `cline-plugins/` は空ではない（`personal-info` プラグイン）。ここでは触らず、02 の分類に従う。
- CATALOG.md の位置の揺れ（`<plugin>/skills/CATALOG.md` と `<plugin>/CATALOG.md`）は 05 で統一するため、ここでは記録だけにする。

02 の棚卸しで見つかったもの（詳細は [progress/02-mapping.md](progress/02-mapping.md) の「4. 03 へ回す既存の不整合」）:

- 存在しないパス参照を直す:
  - writing-skill-web の本文・README・web-patterns-reference.md（`claude-plugins/ai-code-tool`、`claude-plugins/web`）
  - codex-cli-docs・cursor-cli-docs・cursor-docs の allowed-tools と本文（`claude-plugins/other-clis`）
  - cline-cli-docs（`claude-plugins/ai-code-tool`）
  - others/vscode-docs（`plugins/vscode/...`）
  - `claude-plugins/my-tools/skills/tav-lit/extract_page.py:19`
  - `writing-skill-web/tests/conftest.py:24`
- ドキュメントのリンク・記述を直す:
  - `docs/index.md` の `claude_sandbox/` → `topics/claude_sandbox/`
  - `docs/integrations/{index,cline}.md` と `docs/integrations/justfile:57` の `cline-plugins/meta` → `cline-plugins/personal-info`
  - `.cline/skills/cline-skill-writer/skills-reference.md:100` の事実誤り
- メタ欄を直す（いずれも `meta.version` を上げる）:
  - claude-code-memory の requires_skills `configuring-settings` → `claude-settings`
  - aim-lib の name とフォルダ名の不一致（どちらに揃えるか決める）
  - requires_repo_tools の記載漏れを補う: ms-digest・tav-digest（mslearn/tav、aim）、parallel-agent-worktree（tools/linear-cli）、vscode-copilot-docs（aim）
  - `aim` を任意で使う docs スキルに注記する
  - tav-lit の requires_skills と本文の矛盾
  - kilo-cli-guide・kilo-memory-guide・kilo-skill-guide に requires_skills が無い
- `meta.requires_repo_tools` に tools/ 以外の値（gh、uv、python、WebFetch、graphviz、flow.dot 等）が約 20 件ある。値を直すのか、欄の意味を `meta_field.yaml` で広げるのかを先にユーザーに確認する。
- `ai-tools.yaml` の cursor `skills_layout: direct` が実体（`skills/` サブディレクトリ）と合わない。生成器を実行し、`cursor-plugins/meta/CATALOG.md` が更新されていないかを確かめてから直す。
- copilot 側に混入した `agents/openai.yaml`（2 件）は 06 で削除するので、ここでは触らない。
- `.cline/rules/README.md`（案内だけ）を削除する。
- 改名の影響（`tools/scheule`）: タスクスケジューラへの登録は無い（02 で確認）。editable インストールも tools/scheule 配下には無い。

## 読むべきファイル

### 参照先の実在確認

- `pyproject.toml`（workspace members）、`pnpm-workspace.yaml`
- `README.md`、`README_EN.md`、`tools/README.md`、`AGENTS.md`
- `ai-tools.yaml` の `readme` ブロックと `tools/internal/plugin_meta/generate/generate_readme_tools_section.py`（README の該当節は生成物。手で直さない）

### 改名の影響

- `rg -n "scheule|tools/schedule|issue-agent|aim-use"` の結果全件
- `repo-tools.yaml`（`tools/schedule` 言及のコメント）、`docs/repo-wide/tools-directory-layout.md`

## 触るファイル

- 変更: `pyproject.toml`、`uv.lock`（`uv lock` で再生成）、`README.md`、`README_EN.md`、`tools/README.md`、`ai-tools.yaml`、`AGENTS.md`、`.agents/README.md`、`_agents/README.md`
- 変更（改名・aim-use の追従）: `tools/scheule/issue-agent/{AGENTS.md,README.md,issue_agent/environment.py,check.py,scripts/check.ps1}`、`tools/scheule/ai-schedule/AGENTS.md`、`.devcontainer/Dockerfile`、`tools/aim/README.md`、`site/tools-site/docs/tools/aim.md`、`claude-plugins/my-tools/skills/aim-lib/SKILL.md`（`meta.version` を上げる）、`docs/repo-wide/tools-directory-layout.md`・`uv-workspace.md`・`aim-automation.md`
- 移動: `tools/scheule/` → `tools/schedule/`
- 削除: `.kilo/skills/kilo-test-guide/`（空）、`.kilo/skills/using-kilo-cli/`（`output` と `__pycache__` だけ）、`antigravity-plugins/`

## 決定事項・注意点／落とし穴

- README の ai-tools 節は生成物。`ai-tools.yaml` を直して再生成する。手で編集しない。
- `tools/schedule/issue-agent` 等が別エージェントの作業中でないか、着手前に `git status` と最近のコミットで確認する。
- `uv.lock` は members の変更で大きく変わる。差分が lock だけに閉じているか確認する。
- `.claude/hooks/` はインストール先。ここを直接直さない（AGENTS.md の規約）。
- `tools/scheule` の改名で、Windows タスクスケジューラに登録済みの実行パスや editable インストール（`uv tool install --editable`）が壊れることがある。02 で洗い出した登録を、改名と同時に直す（ユーザー環境側の変更なので確認を取る）。
- `.claude/test.json` は `.claude/.gitignore`（`test*.json`）で無視されるローカルファイルなので、対象外にする。

## ルール更新ポイント

- `docs/repo-wide/tools-directory-layout.md`（本ステップ）: `tools/schedule` の例を実在パスへ直す。
- ルール新設はしない。

## 進め方

- **実行主体**: メインがそのまま進める。削除対象の確認だけはユーザーに聞く。
- **TODO 化**: 上の箇条書きの項目ごとに 1 TODO・1 コミット（`fix:`／`chore:`）。最後に `uv sync`、`just --justfile tools/internal/justfile precommit-check` 相当、`pnpm` の skills-site ビルドが通ることを確認する。

## 実行中に判明した変更

- 2026-11-10（02 完了時）: 02 の棚卸しで見つかった不整合（存在しないパス参照、壊れたリンク、メタ欄の誤り、cursor の `skills_layout`、空の README）を「やること」に追加した。
- 2026-11-10（完了）: 全項目を実施。`requires_repo_tools` は自作ツールだけにし、外部コマンドは `dependencies` へ（`meta_field.yaml` も更新）。aim-lib の name を `aim-lib` に変更。vscode-docs・github-copilot-docs の downloader が存在しない共有モジュールを import していたので自己完結版に置き換えた。renormalize は不要だった。詳細・コミット一覧・検証は [progress/03-fix-results.md](progress/03-fix-results.md)。
