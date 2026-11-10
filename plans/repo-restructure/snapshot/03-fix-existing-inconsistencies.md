---
type: Plan Step
status: planning-breakdown
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
