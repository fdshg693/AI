# Step2 棚卸し: 移動先対応表とパス参照一覧

> [../02-research-inventory.md](../02-research-inventory.md) の成果物。05・06 の入力になる。実施日: 2026-11-10。
> 分類の下書きはプラグイン単位でサブエージェント 4 体に任せ（読み取り専用）、カテゴリの最終判断と「要確認」の推奨はメインが付けた。
> 「要確認」行はユーザー確認済み（末尾の「ユーザー確認」節）。

## 凡例

- カテゴリ: `generic` / `tool-companion` / `repo-meta` / `ai-tool-knowledge` / `format-sample` / `generated`（再生成するので移動しない）/ `config`（ルートに残す）/ `delete`
- 移動先の略記: `S/` = `skills/plugins/`、`T/` = `tools/_plugin/my-tools/skills/`、`M/` = `maintenance/`、`K/` = `skills/plugins/ai-tools-knowledge/skills/`、`F/` = `agent-compat/formats/`
- 全スキルは生成物 `.claude-plugin/skill-catalog.json` と各 `CATALOG.md` から参照されている。被参照の欄にはそれ以外を書く。

## 全体の判定基準（05 の `maintenance/docs/repo-layout.md` の正本候補）

- **`meta.requires_repo_tools` だけでは tool-companion と判定できない。** 値に `gh`・`git`・`uv`・`python`・`flow.dot`・`WebFetch`・`graphviz` など tools/ 以外が入っているスキルが 20 件近くあり、meta-plugins は独自の意味で使っている。判定は「本文が `tools/<name>` の CLI を必須にしているか」で行う。
- **`aim` を任意で使う（無くても動く）docs スキル**（ai-sdk-docs、apify-docs、ccusage-docs、ona-docs、ona-cli-docs、vercel-docs）は generic のままにする。メタ欄への記載漏れは 03 で直す。
- **リポジトリ固有の 1〜2 段落が混じる汎用スキル**（writing-hooks、writing-plugins、codex-memory、codex-skill-authoring、cursor-plugin-use、cursor-memory、cursor-skill-use、cline-skill-writer）は、スキルは generic／ai-tool-knowledge として移し、該当段落だけを削るか maintenance 側へ移す（05 の該当バッチ）。

## 1. スキル対応表

### claude-plugins/meta（20）→ `S/claude-code/`（プラグイン名 `meta` → `claude-code` に改名）

| 現パス（`claude-plugins/meta/skills/`） | カテゴリ  | 移動先                | 被参照・備考                                                                                                                                            |
| --------------------------------------- | --------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| claude-agent-sdk                        | generic   | S/claude-code/skills/ | output/ 32 ファイル追跡済み                                                                                                                             |
| claude-cli-docs                         | generic   | 同上                  | `.claude/workflows/audit-skills.js:5,48`（既定引数）、skill-maintenance の refresh_and_diff.py                                                          |
| claude-cli-use                          | generic   | 同上                  | —                                                                                                                                                       |
| claude-code-debugging                   | generic   | 同上                  | `otel-reference.md:192` に自パス直書き。coding/task-tracker/PLAN.md                                                                                     |
| claude-code-docs                        | generic   | 同上                  | 多数の requires_skills の基盤。refresh_and_diff.py、`agent-tooling/.../hooks/REFERENCES.md`、writing-skill-web                                          |
| claude-code-memory                      | generic   | 同上                  | `agent-tooling/.../adapters/codex/nested_agents_md.py:11`。requires_skills の `configuring-settings` は実在しない（03）                                 |
| claude-code-openai-gateway              | generic   | 同上                  | gateway/.env（ignore）。topics/litellm-docs に依存（プラグイン越え）                                                                                    |
| claude-logs-investigate                 | generic   | 同上                  | —                                                                                                                                                       |
| claude-mechanisms                       | generic   | 同上                  | —                                                                                                                                                       |
| claude-settings                         | generic   | 同上                  | —                                                                                                                                                       |
| skill-maintenance                       | repo-meta | M/plugin/skills/      | refresh_and_diff.py が `parents[5]` と `claude-plugins/meta/skills/...` 4 パス・state/ を直書き（移動後も深さは同じ。パス文字列は書き換え）             |
| writing-hooks                           | generic   | S/claude-code/skills/ | 「このリポジトリでフックを足すとき」節は agent-tooling/AGENTS.md へ移す                                                                                 |
| writing-output-styles                   | generic   | 同上                  | —                                                                                                                                                       |
| writing-plugins                         | generic   | 同上                  | 手順 10 の generate_marketplace.py への言及を削る。copilot 側に同名スキルあり（後述）                                                                   |
| writing-rules                           | generic   | 同上                  | —                                                                                                                                                       |
| writing-skill                           | generic   | 同上                  | `.claude/workflows/audit-skills.js:44,45` が bestpractices.md・writing.md を定数で参照。meta-plugins/discovering-skills/patterns、docs/repo-wide 2 件。 |
| writing-skill-complex                   | generic   | 同上                  | requires_repo_tools: graphviz（誤用）                                                                                                                   |
| writing-skill-web                       | generic   | 同上                  | uv workspace member（`pyproject.toml:31`、uv.lock、docs/repo-wide/uv-workspace.md、tests/）。tav-cli・tav-lit・aim は任意。                             |
| writing-subagents                       | generic   | 同上                  | cursor-cli-use/memos                                                                                                                                    |
| writing-workflows                       | generic   | 同上                  | audit-skills.js（コメント）                                                                                                                             |

### claude-plugins/my-tools（20）→ `T/`

| 現パス（`claude-plugins/my-tools/skills/`） | カテゴリ       | 移動先               | 被参照・備考                                                                                                                                         |
| ------------------------------------------- | -------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| aim-cli                                     | tool-companion | T/                   | `repo-workflows.yaml`×2、docs/repo-wide/aim-automation.md・tool-companion-skills.md                                                                  |
| aim-lib                                     | tool-companion | T/                   | frontmatter name `using-aim-library` がフォルダ名と不一致（03）                                                                                      |
| aim2-cli                                    | tool-companion | T/                   | tools/aim2/README.md                                                                                                                                 |
| aws-docs                                    | tool-companion | T/                   | tools/awsdocs/README.md・AGENTS.md                                                                                                                   |
| gdev-docs                                   | tool-companion | T/                   | tools/gdevdocs/README.md・AGENTS.md                                                                                                                  |
| grep-app                                    | tool-companion | T/                   | tools/grepapp/README.md                                                                                                                              |
| inspecting-python-libraries                 | tool-companion | T/                   | —                                                                                                                                                    |
| interactive-cli-wrapper                     | tool-companion | T/                   | 同梱 cursor-agent.md は Cursor の知見だが同居のままにする                                                                                            |
| linear-cli                                  | tool-companion | T/                   | coding/parallel-agent-worktree が多数参照                                                                                                            |
| ms-digest                                   | tool-companion | T/                   | repo-workflows.yaml。requires_repo_tools が none（03）                                                                                               |
| ms-learn                                    | tool-companion | T/                   | repo-workflows.yaml、tools/mslearn/README.md                                                                                                         |
| my-agents                                   | tool-companion | T/                   | 前提に「リポジトリルートで uv sync」。tools 付属として扱う                                                                                           |
| ona-run                                     | tool-companion | T/                   | check/ の検証メモ（追跡済み）も一緒に移す。`check/local-secrets-template.local.md`（ignore）は手で移す                                               |
| skill-tools-cli                             | tool-companion | T/                   | `tools/skill-tools/skill_tools/config/__init__.py:23` `DEFAULT_SELF_SKILL`、`skill-tools.yaml.example:22`、tests/test_cli.py:500。外部契約（後述）。 |
| tav-cli                                     | tool-companion | T/                   | repo-workflows.yaml、tools/tav-cli/README.md                                                                                                         |
| tav-digest                                  | tool-companion | T/                   | requires_repo_tools が none（03）                                                                                                                    |
| tav-lib                                     | tool-companion | T/                   | —                                                                                                                                                    |
| tav-lit                                     | generic        | S/web-lookup/skills/ | extract_page.py 同梱で tools 不要。requires_skills: tav-cli と本文「依存なし」が矛盾（03）。.env（ignore）あり                                       |
| textgraph                                   | tool-companion | T/                   | exploring-this-repo、docs/log.md                                                                                                                     |
| use-context                                 | tool-companion | T/                   | ctx7 前提。改名（ctx7-cli 等）は今回しない                                                                                                           |

### claude-plugins/my-tools-no-install（2）→ `web-lookup` と `doc-tools` に分割

| 現パス                     | カテゴリ | 移動先                               | 被参照・備考                                                                                     |
| -------------------------- | -------- | ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| …/skills/web-lookup        | generic  | S/web-lookup/skills/web-lookup       | CLI 同梱。tools/skill-tools/.skill-tools、tools/awsdocs/AGENTS.md、README。.env・.venv（ignore） |
| …/skills/doc-transcription | generic  | S/doc-tools/skills/doc-transcription | 同梱 uv プロジェクト。.venv（ignore）                                                            |

### claude-plugins の他プラグイン（7 プラグイン、43）

| 現パス（`claude-plugins/`）                              | カテゴリ       | 移動先                                            | 被参照・備考                                                                                                    |
| -------------------------------------------------------- | -------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| coding/skills/brainstorming                              | generic        | S/coding/skills/                                  | —                                                                                                               |
| coding/skills/merge-proposal                             | generic        | 同上                                              | coding/skills/testing                                                                                           |
| coding/skills/okf-spec                                   | generic        | 同上                                              | `docs/AGENTS.md:3`、`README.md:54` がパス直書き。WRITING_REPO.md は repo-meta だが同居のまま                    |
| coding/skills/parallel-agent-worktree                    | tool-companion | T/                                                | 本文が tools/linear-cli 前提（frontmatter は none、03）。プラグイン名前空間が `coding:` → `my-tools:` に変わる  |
| coding/skills/pr-check                                   | generic        | S/coding/skills/                                  | —                                                                                                               |
| coding/skills/proposing-flow                             | generic        | 同上                                              | coding/agents/flow-proposer.md と対で移す。plans/guides/claude-code-execution.md                                |
| coding/skills/review                                     | generic        | 同上                                              | .diffignore（ignore）                                                                                           |
| coding/skills/systematic-debugging                       | generic        | 同上                                              | —                                                                                                               |
| coding/skills/task-tracker                               | tool-companion | T/                                                | `skill-tools hooks install` 前提。フック正本は agent-tooling。memo/（ignore）。名前空間 `coding:` → `my-tools:` |
| coding/skills/testing（SKILL.md なし、git フィクスチャ） | repo-meta      | S/coding/skills/testing（移動のみ）               | review／merge-proposal の手動検証用。docs/repo-wide/skill-tools-contract.md、tools/skill-tools/README.md が参照 |
| coding/agents/flow-proposer.md                           | generic        | S/coding/agents/                                  | proposing-flow と対                                                                                             |
| cicd/skills/diagnosing-actions                           | generic        | S/cicd/skills/                                    | —                                                                                                               |
| cicd/skills/github-agentic-workflows                     | generic        | 同上                                              | gh-aw は GitHub の機能。ai-tool-knowledge にしない                                                              |
| cicd/skills/issue-triage                                 | generic        | 同上                                              | `.github/workflows/*-issue-triage.yml` が `/github-action:issue-triage` の名前で呼ぶ（名前は変えない）          |
| cicd/skills/pr-agent-docs                                | generic        | 同上                                              | —                                                                                                               |
| topics/skills/ai-sdk-docs                                | generic        | S/topics/skills/                                  | `aim` 任意                                                                                                      |
| topics/skills/apify-docs                                 | generic        | 同上                                              | `aim` 任意                                                                                                      |
| topics/skills/ccusage-docs                               | generic        | 同上                                              | CLI ヘルプ生成はルート package.json の ccusage 前提（再生成時のみ）                                             |
| topics/skills/codegraph-docs                             | generic        | 同上                                              | ルート `AGENTS.md:18`、exploring-this-repo:31、README                                                           |
| topics/skills/deepseek-harness-docs                      | generic        | 同上                                              | —                                                                                                               |
| topics/skills/langchain-docs                             | generic        | 同上                                              | tools/my-agents/AGENTS.md:3                                                                                     |
| topics/skills/litellm-docs                               | generic        | 同上                                              | —                                                                                                               |
| topics/skills/ona-cli-docs                               | generic        | 同上                                              | config.yml:10 が `claude-plugins/topics/skills/ona-docs/output/...` を参照（ona-docs と同じ場所に置く）         |
| topics/skills/ona-docs                                   | generic        | 同上                                              | —                                                                                                               |
| topics/skills/openrouter-docs                            | generic        | 同上                                              | tools/aim/README.md、tools/openrouter/README.md                                                                 |
| topics/skills/vercel-docs                                | generic        | 同上                                              | `aim` 任意                                                                                                      |
| topics/skills/writing-mermaid-diagrams                   | generic        | 同上                                              | tav 任意                                                                                                        |
| others/skills/github-fetch                               | generic        | S/others/skills/                                  | .env（ignore）                                                                                                  |
| others/skills/vscode-docs                                | generic        | 同上                                              | copilot vscode-copilot-docs/config.yml:10 が output を参照。本文の `plugins/vscode/...` は古い（03）            |
| special/skills/command-group（＋sub_commands 3）         | format-sample  | S/special/skills/ のまま                          | Claude Code のスキル構造の実験。ダミーのサブスキル                                                              |
| special/skills/skill-group（＋sub_skills 3）             | format-sample  | 同上                                              | tests/test_list_skills.py が自パス直書き                                                                        |
| subagents/skills/dispatching-parallel-agents             | generic        | S/subagents/skills/                               | —                                                                                                               |
| subagents/skills/subagent-driven-development             | generic        | 同上                                              | —                                                                                                               |
| subagents/skills/test-driven-development                 | generic        | 同上                                              | —                                                                                                               |
| subagents/agents/code-reviewer.md                        | generic        | S/subagents/agents/                               | —                                                                                                               |
| no-code/skills/french                                    | generic        | S/no-code/skills/                                 | —                                                                                                               |
| no-code/output-styles/language-learning.md               | generic        | S/no-code/output-styles/                          | —                                                                                                               |
| claude-plugins/README.md                                 | repo-meta      | 削除（説明は maintenance/docs/repo-layout.md へ） | —                                                                                                               |

### meta-plugins（6 ＋ agents）→ `M/plugin/`

| 現パス                                  | カテゴリ  | 移動先           | 被参照・備考                                                                                         |
| --------------------------------------- | --------- | ---------------- | ---------------------------------------------------------------------------------------------------- |
| meta-plugins/（.claude-plugin、README） | repo-meta | M/plugin/        | ルート AGENTS.md 5 か所、`check_skill_repo_tools.py:27` `EXCLUDED_PREFIXES`、docs/repo-wide 4 件以上 |
| agents/skill-search.md                  | repo-meta | M/plugin/agents/ | discovering-skills 配下 12 件                                                                        |
| skills/changing-skills-and-tools        | repo-meta | M/plugin/skills/ | `list_skill_tool_impact.py:34`                                                                       |
| skills/committing                       | repo-meta | 同上             | commit.py が docs/repo-wide・tools/internal を文字列で案内                                           |
| skills/configuring-github               | repo-meta | 同上             | —                                                                                                    |
| skills/discovering-skills               | repo-meta | 同上             | requires_repo_tools に `meta-plugins/agents/...` パス。logs/（ignore）                               |
| skills/exploring-this-repo              | repo-meta | 同上             | snapshot_indexed_layout.py `parents[4]`（深さ同じ）                                                  |
| skills/meta                             | repo-meta | 同上             | list_repo_meta_docs.py が `docs/repo-wide` と 5 段 parent（深さ同じ、docs パスは書き換え）           |

### 他ツールの知識スキル（42）→ `K/`（06 と同じコミット）

改名は名前の衝突を避けるものだけにする（`copilot-` 接頭辞を 2 件）。

| 現パス                                               | カテゴリ          | 移動先                                | 被参照・備考                                                                                                    |
| ---------------------------------------------------- | ----------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| codex-plugins/meta/skills/codex-cli-docs             | ai-tool-knowledge | K/codex-cli-docs                      | 本文・allowed-tools が存在しない `claude-plugins/other-clis/...`（03）                                          |
| …/codex-cli-use                                      | ai-tool-knowledge | K/codex-cli-use                       | agents/openai.yaml → F/codex/                                                                                   |
| …/codex-docs                                         | ai-tool-knowledge | K/codex-docs                          | output/（ignore）。REFERENCES.md                                                                                |
| …/codex-hooks                                        | ai-tool-knowledge | K/codex-hooks                         | REFERENCES.md                                                                                                   |
| …/codex-memory                                       | ai-tool-knowledge | K/codex-memory                        | `nested_agents_md.py:7`                                                                                         |
| …/codex-sdk-use                                      | ai-tool-knowledge | K/codex-sdk-use                       | tools/codex-wrapper/AGENTS.md                                                                                   |
| …/codex-settings                                     | ai-tool-knowledge | K/codex-settings                      | —                                                                                                               |
| …/codex-skill-authoring                              | ai-tool-knowledge | K/codex-skill-authoring               | openai.yaml → F/codex/                                                                                          |
| copilot-plugins/meta/copilot-cli-docs                | ai-tool-knowledge | K/copilot-cli-docs                    | —                                                                                                               |
| …/github-copilot-docs                                | ai-tool-knowledge | K/github-copilot-docs                 | writing-skill-web 3 件                                                                                          |
| …/github-copilot-observability-docs                  | ai-tool-knowledge | K/github-copilot-observability-docs   | 混入した agents/openai.yaml は削除                                                                              |
| …/github-copilot-sdk-docs                            | ai-tool-knowledge | K/github-copilot-sdk-docs             | tools/copilot-wrapper/AGENTS.md                                                                                 |
| …/vscode-copilot-docs                                | ai-tool-knowledge | K/vscode-copilot-docs                 | 抜粋生成が `aim` 前提（再生成時のみ）。config.yml が others/vscode-docs を参照。output/verification（ignore）   |
| …/writing-copilot-instructions                       | ai-tool-knowledge | K/writing-copilot-instructions        | 混入した agents/openai.yaml は削除                                                                              |
| …/writing-plugins                                    | ai-tool-knowledge | **K/copilot-writing-plugins**（改名） | Claude 版 writing-plugins と同名衝突                                                                            |
| …/writing-skills                                     | ai-tool-knowledge | **K/copilot-writing-skills**（改名）  | —                                                                                                               |
| cursor-plugins/meta/skills/cursor-cli-docs           | ai-tool-knowledge | K/cursor-cli-docs                     | 存在しない other-clis パス（03）                                                                                |
| …/cursor-cli-use                                     | ai-tool-knowledge | K/cursor-cli-use                      | eval-logs/model-eval.jsonl（ignore）、memos/                                                                    |
| …/cursor-docs                                        | ai-tool-knowledge | K/cursor-docs                         | download_cursor_reference.py:11 が writing-skill-web を相対参照                                                 |
| …/cursor-memory                                      | ai-tool-knowledge | K/cursor-memory                       | —                                                                                                               |
| …/cursor-plugin-use                                  | ai-tool-knowledge | K/cursor-plugin-use                   | —                                                                                                               |
| …/cursor-sdk-use                                     | ai-tool-knowledge | K/cursor-sdk-use                      | tools/cursor-wrapper/AGENTS.md                                                                                  |
| …/cursor-skill-use                                   | ai-tool-knowledge | K/cursor-skill-use                    | —                                                                                                               |
| _agents/plugins/antigravity-meta/skills/agy-cli-docs | ai-tool-knowledge | K/agy-cli-docs                        | site/skills-site/tests/publication.test.mjs                                                                     |
| …/antigravity-docs                                   | ai-tool-knowledge | K/antigravity-docs                    | output/（ignore）                                                                                               |
| …/antigravity-memory                                 | ai-tool-knowledge | K/antigravity-memory                  | `tools/agents-rules/agents_rules/targets.py:9`、.agents/README.md。rules の frontmatter 実測値 → F/antigravity/ |
| …/antigravity-skills                                 | ai-tool-knowledge | K/antigravity-skills                  | —                                                                                                               |
| …/antigravity-subagents                              | ai-tool-knowledge | K/antigravity-subagents               | —                                                                                                               |
| .cline/skills/cline-cli-docs                         | ai-tool-knowledge | K/cline-cli-docs                      | 存在しない `claude-plugins/ai-code-tool/...`（03）                                                              |
| .cline/skills/cline-cli-use                          | ai-tool-knowledge | K/cline-cli-use                       | —                                                                                                               |
| .cline/skills/cline-docs                             | ai-tool-knowledge | K/cline-docs                          | output/temp（ignore）                                                                                           |
| .cline/skills/cline-memory                           | ai-tool-knowledge | K/cline-memory                        | —                                                                                                               |
| .cline/skills/cline-plugin-writer                    | ai-tool-knowledge | K/cline-plugin-writer                 | —                                                                                                               |
| .cline/skills/cline-rule-writer                      | ai-tool-knowledge | K/cline-rule-writer                   | —                                                                                                               |
| .cline/skills/cline-sdk-docs                         | ai-tool-knowledge | K/cline-sdk-docs                      | tools/cline-wrapper/AGENTS.md                                                                                   |
| .cline/skills/cline-skill-writer                     | ai-tool-knowledge | K/cline-skill-writer                  | skills-reference.md:100 の事実誤り（03）                                                                        |
| .kilo/skills/kilo-agent-writer                       | ai-tool-knowledge | K/kilo-agent-writer                   | —                                                                                                               |
| .kilo/skills/kilo-cli-guide                          | ai-tool-knowledge | K/kilo-cli-guide                      | requires_skills キー無し（03）                                                                                  |
| .kilo/skills/kilo-code-docs                          | ai-tool-knowledge | K/kilo-code-docs                      | —                                                                                                               |
| .kilo/skills/kilo-memory-guide                       | ai-tool-knowledge | K/kilo-memory-guide                   | requires_skills キー無し（03）                                                                                  |
| .kilo/skills/kilo-plugin-writer                      | ai-tool-knowledge | K/kilo-plugin-writer                  | —                                                                                                               |
| .kilo/skills/kilo-skill-guide                        | ai-tool-knowledge | K/kilo-skill-guide                    | requires_skills キー無し（03）                                                                                  |
| .kilo/skills/kilo-test-guide                         | delete            | —                                     | 空・未追跡（03）                                                                                                |
| .kilo/skills/using-kilo-cli                          | delete            | —                                     | `__pycache__` だけの残骸・未追跡（03）                                                                          |

### プラグイン外の要素・ツール固有書式

| 現パス                                                                                                                                      | カテゴリ                         | 移動先                                          | 備考                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| claude-plugins/*/.claude-plugin/plugin.json                                                                                                 | —                                | プラグインと一緒に移す                          | meta の `"name": "meta"` → `claude-code`（名前空間が変わる）                                                                             |
| codex-plugins/meta/.codex-plugin/plugin.json                                                                                                | format-sample                    | F/codex/ にサンプル、実体は 06 の配布方式に従う | —                                                                                                                                        |
| codex-plugins/meta/skills/*/agents/openai.yaml（5）                                                                                         | format-sample                    | F/codex/                                        | Codex 固有 UI メタデータ                                                                                                                 |
| copilot-plugins/meta（direct レイアウト）、plugin.json                                                                                      | format-sample／generated         | F/copilot/ にサンプル、plugin.json は再生成     | `ai-tools.yaml:134` `plugin_json_output_path`                                                                                            |
| cursor-plugins/meta/.cursor-plugin/plugin.json                                                                                              | format-sample                    | F/cursor/                                       | `ai-tools.yaml:169` の `skills_layout: direct` が実体（skills/）と不一致 → CATALOG が更新されていない疑い（03）                          |
| _agents/plugins/antigravity-meta/plugin.json                                                                                                | format-sample                    | F/antigravity/                                  | —                                                                                                                                        |
| cline-plugins/personal-info（index.ts ほか）                                                                                                | format-sample                    | F/cline/personal-info                           | `docs/integrations/justfile:57-60`（`../../cline-plugins/personal-info`）、docs/integrations/cline.md（`cline-plugins/meta` と誤記、03） |
| antigravity-plugins/（README のみ）                                                                                                         | delete                           | —                                               | ai-tools.yaml:176、README、README_EN、discovering-skills（03）                                                                           |
| .cline/rules/README.md                                                                                                                      | delete                           | —                                               | 案内だけ（03）                                                                                                                           |
| .github/agents/README.md、.github/skills/README.md                                                                                          | config                           | ルートに残す                                    | 案内だけ。削除は 09 で判断                                                                                                               |
| 各 `*/CATALOG.md`、`.claude-plugin/{marketplace,skill-catalog}.json`、`.agents/plugins/marketplace.json`、`.github/plugin/marketplace.json` | generated                        | 再生成                                          | —                                                                                                                                        |
| `.clinerules/`、`.agents/rules/`、`.github/instructions/`                                                                                   | config（生成先、未生成）         | ルート                                          | ai-tools.yaml の説明が実態と合わない（03）                                                                                               |
| .kilo/plugin/、.kilo/package*.json                                                                                                          | config（agent-tooling の生成物） | ルート                                          | —                                                                                                                                        |

## 2. tools・docs・その他の対応表

| 現パス                                                                     | 区分                     | 移動先                                                      | 備考                                                                                                                                                                                                              |
| -------------------------------------------------------------------------- | ------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| tools/internal/（ai-usage 以外）                                           | repo-meta                | M/scripts/                                                  | 深さが同じなので `parents[N]` は変わらない。パス文字列は 58 ファイル                                                                                                                                              |
| tools/internal/ai-usage                                                    | 個人用 CLI               | tools/ai-usage                                              | `uv tool install --editable`、statusLine。uv member（`pyproject.toml:26`）。repo-tools.yaml への登録要否は 05 で判断                                                                                              |
| tools/infra/                                                               | 配布しないインフラツール | tools/infra のまま                                          | terraform state 等（ignore）あり                                                                                                                                                                                  |
| tools/<配布 CLI>（repo-tools.yaml の 16）                                  | 配布 CLI                 | tools/ のまま                                               | path 契約                                                                                                                                                                                                         |
| tools/{claude,cline,codex,copilot,cursor}-wrapper、interactive-cli-wrapper | ラッパー                 | tools/ のまま                                               | —                                                                                                                                                                                                                 |
| tools/{my-agents,sandbox,scheule/_}、openrouter/_                          | 実験・グループ           | tools/ のまま                                               | sandbox の pem・.env、data/ は ignore                                                                                                                                                                             |
| agent-tooling/                                                             | マルチ AI 対応           | agent-compat/agent-tooling/                                 | 深さ +1: `hooks/build/build.py:810`（`package_root.parent.parent / "repo-tools.yaml"`）、tests の `parents[2]`（conftest、test_codex_parity、test_builder）。uv member（`pyproject.toml:36`）、lefthook.yml:27-33 |
| docs/repo-wide/                                                            | repo-meta                | M/docs/                                                     | 36 ファイルが参照                                                                                                                                                                                                 |
| docs/integrations/                                                         | 利用者向け導入手順       | docs/integrations のまま（アンブレラ）                      | 中の `cline-plugins/`、`codex-plugins/meta`（`--sparse`）等の記述は 05・06 で更新                                                                                                                                 |
| docs/topics/claude_sandbox                                                 | tools/sandbox の運用知識 | docs/topics のまま（tools に入れると OKF バンドルが割れる） | docs/index.md のリンクが `claude_sandbox/` で壊れている（03）                                                                                                                                                     |
| docs/index.md、docs/log.md、docs/AGENTS.md                                 | —                        | docs/ のまま                                                | AGENTS.md が okf-spec パスを参照                                                                                                                                                                                  |
| plans/                                                                     | テンプレート兼作業場所   | plans/ のまま                                               | 配布は README の「コピーする」手順のみで、外部からのパス参照なし                                                                                                                                                  |
| templates/                                                                 | —                        | —                                                           | **実在しない**。README.md「リポジトリ運用」節が言及（03）                                                                                                                                                         |
| SSOT yaml 6 本                                                             | —                        | registry/（05 バッチ 2）                                    | 下の参照一覧                                                                                                                                                                                                      |

## 3. パス参照の棚卸し

`git ls-files` から node_modules・dist・output・generated・temp・plans/repo-restructure を除き、旧パス・SSOT 名を検索した。**252 ファイル・1173 か所**（md 154、py 62、mjs 9、yaml 7、yml 6、json 4 ほか）。

| 旧パス                | 参照ファイル数（うち md／SKILL.md） |
| --------------------- | ----------------------------------- |
| `claude-plugins/`     | 105（79／15）                       |
| `tools/internal`      | 58（39／3）                         |
| `ai-tools.yaml`       | 65（41／7）                         |
| `repo-tools.yaml`     | 62（27／4）                         |
| `meta-plugins/`       | 42（36／6）                         |
| `docs/repo-wide`      | 36（27／7）                         |
| `agent-tooling/`      | 20（13／4）                         |
| `meta_field.yaml`     | 19（11／1）                         |
| `repo-hooks.yaml`     | 18（11／1）                         |
| `copilot-plugins/`    | 18（12／1）                         |
| `codex-plugins/`      | 16（12／3）                         |
| `cursor-plugins/`     | 13（11／3）                         |
| `_agents/`            | 13（10／3）                         |
| `.cline/skills`       | 11（10／4）                         |
| `repo-workflows.yaml` | 11（7／1）                          |
| `.kilo/skills`        | 6（5／2）                           |
| `skill-tags.yaml`     | 4（1／0）                           |

### 種類別（壊れると動作に影響するもの）

- **コードのハードコード**
  - `tools/skill-tools/skill_tools/config/__init__.py:23` `DEFAULT_SELF_SKILL`、`skill-tools.yaml.example:22,26`
  - SSOT のファイル名を定数で持つ: `tools/skill-tools/skill_tools/{catalog/__init__.py:78, repo_tools/load.py:24, workflows/__init__.py:17, hooks/catalog.py:28}`（**source ルート直下を読む前提＝外部契約**）、`tools/agents-rules/agents_rules/generate.py:16`（ルート判定にも使う）
  - `REPO_ROOT / "<ssot>.yaml"`: `tools/internal/plugin_meta/util/ai_tools_config.py:16`、`tools/internal/skill/util/{meta_field_registry.py:16, repo_tools_registry.py:18}`、`tools/internal/release/bump_tool_versions.py:36`、`agent-tooling/.../hooks/build/build.py:810`
  - site: `site/skills-site/scripts/{source-registry.mjs:16, meta-field-registry.mjs:17, repo-tools-registry.mjs:16}`、`site/tools-site/scripts/repo-tools-data.mjs:16`
  - `tools/internal/skill/check/check_skill_repo_tools.py:27,58`（`EXCLUDED_PREFIXES = ("meta-plugins/", "tools/internal/")`）
  - `tools/internal/precommit/__main__.py:54-101`（ステージ判定 glob。`copilot-plugins/meta/**/SKILL.md` ほか）
  - `tools/internal/plugin_meta/generate/generate_copilot_marketplace.py`（copilot-plugins/meta を走査）
  - `claude-plugins/meta/skills/skill-maintenance/scripts/refresh_and_diff.py:34,136-149`、`meta-plugins/skills/meta/scripts/list_repo_meta_docs.py:51-56`
  - `.claude/workflows/audit-skills.js:44,45,48`
  - `claude-plugins/topics/skills/ona-cli-docs/config.yml:10`、`copilot-plugins/meta/vscode-copilot-docs/config.yml:10`（他スキルの output をパスで読む）
  - `.github/workflows/tool-release.yml:45`（`open('repo-tools.yaml')`）
- **SSOT yaml**: `ai-tools.yaml`（plugin path 22 か所・`plugin_json_output_path`）、`repo-workflows.yaml`（skill パス 6）、`repo-hooks.yaml:13`（catalog パス）、`repo-tools.yaml`（コメント）
- **CI の `paths:`**: `.github/workflows/skill-site.yml:10-31`（旧プラグインルート 6 種 ×2）、`tools-site.yml:9,24`（`repo-tools.yaml`）
- **lefthook / justfile / workspace**: `lefthook.yml:14-70`（`tools/internal/justfile`、`agent-tooling/**` glob、`ai-tools.yaml`・`repo-tools.yaml` glob）、`docs/integrations/justfile:60`、`pyproject.toml:26,31,36`（uv members）、`uv.lock`。ルート `justfile` は直接の旧パスなし
- **深さ依存（`parents[N]`）**: 深さが変わるのは agent-tooling（+1）と claude-plugins → skills/plugins（+1）。後者で repo root を求めるコードは無い（check_urls.py の `parents[2]` はスキル相対）。tools/internal → maintenance/scripts、meta-plugins → maintenance/plugin は深さ同じ
- **Markdown・SKILL.md 本文**: 154 ファイル。代表はルート `AGENTS.md`（meta-plugins 5 か所、codegraph-docs）、`docs/AGENTS.md:3`、`README.md`・`README_EN.md`、`agent-tooling/agent_tooling/hooks/REFERENCES.md`（他ツールスキル 30 か所）、`meta-plugins/skills/discovering-skills/patterns/*.md`

### 外部契約

| 契約                                                                                                                                  | 現状                                                                                                             | 影響                                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude marketplace `fdshg693/AI` の `.claude-plugin/marketplace.json`                                                                 | `source: ./claude-plugins/<p>`（10）                                                                             | source は再生成で追従。プラグイン名変更（`meta`→`claude-code`、`my-tools-no-install`→改名）はインストール済み利用者が再インストール。スキル移籍（task-tracker、parallel-agent-worktree が `coding`→`my-tools`、tav-lit が `my-tools`→`web-lookup`）も名前空間が変わる |
| Codex marketplace `.agents/plugins/marketplace.json`                                                                                  | local source `codex-plugins/meta`                                                                                | 06 で再設計。`docs/integrations/codex.md:89` の `--sparse codex-plugins/meta`                                                                                                                                                                                         |
| Copilot `.github/plugin/marketplace.json`                                                                                             | `./copilot-plugins/meta`                                                                                         | 06                                                                                                                                                                                                                                                                    |
| skill-tools の GitHub ソース                                                                                                          | ルート直下の `ai-tools.yaml`・`repo-tools.yaml`・`repo-workflows.yaml`・`repo-hooks.yaml` をファイル名固定で読む | **registry/ 移動で旧版 skill-tools が全滅する**。05 バッチ 2 で「ルートにも読める何か（ポインタ or 両対応）」が必要                                                                                                                                                   |
| 他プロジェクトの `.skill-tools` マニフェスト・ジャーナル                                                                              | source のスキルパスを記録                                                                                        | パスが変わると update が旧パスを見失う。canonical ID 変更の移行措置を 05 で決める                                                                                                                                                                                     |
| `uv tool install "git+https://github.com/fdshg693/AI.git#subdirectory=tools/<name>"`（README、docs/integrations/cli-tools.md:98-100） | tools/ 直下                                                                                                      | 07 でサブモジュール化すると subdirectory 方式が動くか未確認（01 から継続）                                                                                                                                                                                            |
| skills-site の URL                                                                                                                    | canonical ID = パス                                                                                              | 変わってよい（ユーザー回答済み）                                                                                                                                                                                                                                      |
| `skill-tools --fb` 保存先                                                                                                             | スキル名単位                                                                                                     | 改名するスキル（copilot-writing-plugins、copilot-writing-skills）だけ確認                                                                                                                                                                                             |
| `.github/workflows/claude-issue-triage.yml:38`                                                                                        | `seiwan-marketplace@github-action` と `/github-action:issue-triage`                                              | プラグイン名を変えない限り影響なし                                                                                                                                                                                                                                    |

### リポジトリ外の参照

| 参照                                               | 現状                                                                                                                                                                                                                                        | 対応                                                                                                              |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `~/.claude/settings.json` `statusLine`             | `python C:/CodeRoot/AI/tools/internal/ai-usage/statusline_hook.py`                                                                                                                                                                          | **既に存在しないパスを指している**（`C:/CodeRoot/AI`）。05 で ai-usage の移動先が決まったらユーザー確認の上で直す |
| `~/.claude/settings.json` `extraKnownMarketplaces` | `directory`: `C:\C\ai`                                                                                                                                                                                                                      | ルートは変わらないので影響なし                                                                                    |
| `uv tool` editable                                 | `tools/{aim,awsdocs,ctx7,grepapp,mslearn,ona-run,pyinspect,skill-tools,tav-cli,openrouter/*}` は影響なし。`ai-usage-cli` → `tools/internal/ai-usage`（要再インストール）。`skill-deploy` → `tools/skill-deploy`（**既に存在しない**、残骸） | ai-usage を移したら `uv tool install --editable <新パス> --force`。skill-deploy はアンインストールを提案          |
| Windows タスクスケジューラ                         | `schtasks` に本リポジトリのパスを含むタスクは検出されなかった                                                                                                                                                                               | 影響なし（tools/scheule は自分で登録する仕組みなので、登録時のパスは README 確認のみ）                            |

### 追跡外ファイル（`git status --ignored`、node_modules・`__pycache__`・`*.egg-info`・キャッシュを除く）

移動対象フォルダ内にあり、05 で手で移すもの:

- `claude-plugins/`: `coding/skills/review/.diffignore`、`coding/skills/task-tracker/memo/`、`coding/skills/testing/merge-fixture-repo/`、`meta/skills/claude-code-docs/output/temp/`、`meta/skills/claude-code-openai-gateway/gateway/.env`、`meta/skills/writing-skill-web/scripts/.cache/`、`my-tools-no-install/skills/{doc-transcription,web-lookup}/.venv/`（作り直す）、`my-tools-no-install/skills/web-lookup/.env`、`my-tools/skills/ona-run/check/local-secrets-template.local.md`、`my-tools/skills/tav-lit/.env`、`others/skills/github-fetch/.env`、`topics/skills/*/output/temp/`・`.cache/`・`output/llms-full.txt`・litellm の `output/selection*.json`
- `meta-plugins/skills/discovering-skills/logs/`
- `codex-plugins/meta/skills/codex-docs/output/`、`copilot-plugins/meta/vscode-copilot-docs/output/verification/`、`cursor-plugins/meta/skills/cursor-cli-use/eval-logs/model-eval.jsonl`、`_agents/plugins/antigravity-meta/skills/antigravity-docs/output/`、`.cline/skills/cline-docs/output/temp/`
- `agent-tooling/agent_tooling/hooks-staging/`
- tools/ 配下（tools はパスが変わらないので 07 の退避対象）: `.env` 多数、`logs/`、`memo/`、`tools/sandbox/*.pem`・`orchestrator/data/`、`tools/infra/ai-logs/terraform/{.terraform,terraform.tfstate,terraform.tfvars}`、`tools/skill-tools/.venv/`、`tools/textgraph/.venv/`
- site/ 配下（07 の退避対象）: `site/skills-site/{.env,.azure/,api/data/*.json,public/*}`、`site/tools-site/docs/tools/`

### `temp/rewrite_moved_paths.py` の再利用

- 使える部分: 走査（スキップ規則、`.claude/hooks/` と egg-info 除外）、改行コードの保持、SKILL.md の frontmatter が変わったときだけ `version` を上げる処理。
- 使えない部分: `transform()` が前回の移動（repo-meta → repo-wide 等）の置換をハードコードしている。`rglob` は Junction を辿る（04 以降は `git ls-files` に替える）。
- 05 での方針: 本対応表から「旧プレフィクス → 新プレフィクス」の表を作り、**長いプレフィクスから順に**置換する（例: `claude-plugins/meta/skills/skill-maintenance` を `claude-plugins/meta` より先に）。`/` と `\` の両表記を扱う。`maintenance/scripts/` に汎用化して置く（バッチごとに表を差し替える）。

## 4. 03 へ回す既存の不整合（今回見つかったもの）

- 存在しないパス参照: writing-skill-web（`claude-plugins/ai-code-tool`、`claude-plugins/web`）、codex-cli-docs・cursor-cli-docs・cursor-docs（`claude-plugins/other-clis`）、cline-cli-docs（`claude-plugins/ai-code-tool`）、vscode-docs（`plugins/vscode/...`）、tav-lit/extract_page.py:19（`claude-plugins/web`）、writing-skill-web/tests/conftest.py:24（tav-cli/tests）
- `docs/index.md` の `claude_sandbox/` リンク（実体は `topics/claude_sandbox/`）、README の `templates/`（実在しない）、`docs/integrations/{index,cline}.md`・justfile コメントの `cline-plugins/meta`（実体は personal-info）
- メタ欄: `configuring-settings`（実在しない requires_skills）、aim-lib の name 不一致、ms-digest・tav-digest・parallel-agent-worktree・vscode-copilot-docs の requires_repo_tools 漏れ、tav-lit の矛盾、kilo 3 件の requires_skills キー欠落、requires_repo_tools への tools/ 以外の値の記入（約 20 件。意味の統一は meta_field.yaml 側の判断が要る）
- `ai-tools.yaml` の cursor `skills_layout: direct` と実体の不一致、`.clinerules` 等の説明文
- copilot 側に混入した `agents/openai.yaml`（2 件）、cline-skill-writer の事実誤り
- 空・残骸: `.kilo/skills/{kilo-test-guide,using-kilo-cli}`、`antigravity-plugins/`、`.cline/rules/README.md`
- リポジトリ外: statusLine のパス（`C:/CodeRoot/AI`）、`skill-deploy` の editable 残骸

## ユーザー確認

2026-11-10 にユーザーへ質問した 4 点は、すべて推奨どおりに決定。それ以外の「要確認」行（writing-skill、writing-skill-web、tav-lit、skill-tools-cli）は推奨どおりとし、質問していない。

- task-tracker と parallel-agent-worktree は `tools/_plugin/my-tools/skills/` へ移す（名前空間が `coding:` から `my-tools:` に変わる）。
- my-tools-no-install は `skills/plugins/web-lookup`（web-lookup、tav-lit）と `skills/plugins/doc-tools`（doc-transcription）に分ける。
- claude-plugins/special（command-group、skill-group）は `skills/plugins/special` に残す。
- tools/internal/ai-usage は `tools/ai-usage` へ移す（maintenance には入れない）。
