---
type: Plan Step
status: implementing-done
---

# Step 5: 使い方スキルのプラグインと SSOT 登録

> [04-agent-logs-cli.md](04-agent-logs-cli.md) の続き。

## やること

`tools/_plugin/my-tools` と同型のプラグイン `agent-compat/_plugin/agent-compat-tools/` を作り、`agent-logs` の使い方スキル `agent-logs-cli` を置く。プラグインを `registry/ai-tools.yaml`、CLI を `registry/repo-tools.yaml` に登録し、マーケットプレイス・カタログ・README を生成し直す。agent-compat とリポジトリ全体の規約文書を新構成に合わせる。

## 読むべきファイル・実行推奨Grep

**同型の手本（優先度: 高）**

- 読む: `tools/_plugin/my-tools/`（`.claude-plugin/plugin.json`・`README.md`・`skills/CATALOG.md`）と `skills/aim-cli/`・`skills/skill-tools-cli/` — プラグインの最小構成と使い方スキルの書き方（`--ai-help` を正本にして転記しない、前提条件の書き方）
- 読む: `maintenance/docs/tool-companion-skills.md` — 使い方スキルの責務境界
- 読む: `maintenance/plugin/skills/changing-skills-and-tools/SKILL.md` — スキル・ツール追加時の手順

**登録と生成器の前提（優先度: 高）**

- 読む: `registry/ai-tools.yaml`（`claude-code.plugins`・`readme.plugin_roots`）と `maintenance/docs/ai-tools-config.md`
- 読む: `registry/repo-tools.yaml` の冒頭コメント（登録条件・`description` ロケータ・`release`）
- Grep: `rg -n "tools/_plugin|skills/plugins" maintenance/scripts site/skills-site/scripts tools/skill-tools/skill_tools` — プラグインのルートを `skills/plugins`・`tools/_plugin` に決め打ちしている箇所（計画時点で `generate_readme_tools_section.py` の説明文、`plugin_source.py` を要確認）
- 読む: `maintenance/scripts/skill/check/check_skill_repo_tools.py` — `TOOLS_PATH_PATTERN` が `tools/` 始まりのパスしか見ないため、`agent-compat/logs/agent-logs` を `requires_install` に書いても検査されない

**サブモジュール単体で開いたとき（優先度: 低）**

- 読む: `agent-compat/.links.yaml` と `maintenance/docs/repo-layout.md`「サブモジュールを単体で開く」

## 触るファイル

### 新規

- `agent-compat/_plugin/agent-compat-tools/.claude-plugin/plugin.json`
- `agent-compat/_plugin/agent-compat-tools/README.md` — my-tools README と同じ構成（前提: CLI を別途インストール）
- `agent-compat/_plugin/agent-compat-tools/skills/agent-logs-cli/SKILL.md`（＋設計意図の `README.md`）— どのサブコマンドで何が分かるか、ツール別の欠損（Antigravity の本文、トークンの有無）の読み方、仕様は知識スキルへ。`meta.requires_repo_tools: agent-logs`、`requires_install: uv tool install --editable agent-compat/logs/agent-logs`、`requires_skills` に Step3 の知識スキル
- `agent-compat/_plugin/agent-compat-tools/skills/CATALOG.md` — 生成物

### 変更

- `registry/ai-tools.yaml` — `claude-code.plugins` と `readme.plugin_roots` に `agent-compat/_plugin` を追加
- `registry/repo-tools.yaml` — `agent-logs`（`path: agent-compat/logs/agent-logs`、`description` ロケータ）
- 生成物: `.claude-plugin/marketplace.json`・`skill-catalog.json`・README の ai-tools セクション・ルート直下の生成コピー（生成スクリプト・pre-commit で更新）
- 決め打ちがあれば `maintenance/scripts/plugin_meta/` の該当箇所、`check_skill_repo_tools.py` の `TOOLS_PATH_PATTERN`（`agent-compat/` も対象にする）
- `agent-compat/AGENTS.md`・`agent-compat/README.md`・`agent-compat/.links.yaml`
- `maintenance/docs/repo-layout.md`・`maintenance/docs/tool-companion-skills.md`
- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md` —「ローカルログを横断で検索・集計したい」行に agent-logs-cli への導線を足すか判断（足すなら `meta.version` を上げる）

## 決定事項・注意点／落とし穴

| 決定・注意                                                                                                                                                                                                            | 理由                                                                                                                                            |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| プラグイン名は `agent-compat-tools`、置き場所は `agent-compat/_plugin/`（`tools/_plugin/` と同じ `_plugin` 命名）                                                                                                     | ユーザー要望「my-tools と同型」。将来 agent-compat に CLI が増えても同じプラグインに足す                                                        |
| `agent-compat/AGENTS.md` の「スキルの実体は置かない」を「agent-compat のツールに付属する使い方スキル（`_plugin/`）だけは置く」に改め、README の「スキルは `skills/plugins/` と `tools/_plugin/` に 1 か所だけ」も更新 | 現行ルールと矛盾する。ルート README の文言は生成元（`generate_readme_tools_section.py`）側を直す                                                |
| `release`（tools-site 掲載）は v1 では付けない                                                                                                                                                                        | 非公開形式に依存し、まず手元で使い込む                                                                                                          |
| `agent-compat/.links.yaml` に `_umbrella/cc-knowledge` を追加する                                                                                                                                                     | agent-compat 単体で開いたとき Claude Code のログ仕様（`claude-logs-investigate`）を読めるようにする。既存の `_umbrella/ai-tools-knowledge` と対 |
| スキル走査（skill-tools・skills-site・カタログ生成）が `agent-compat/_plugin/` を拾うことを生成結果で確認する。`formats/` は `.format-samples` で除外されているので影響しない                                         | 新しいプラグインルートを足すのは初めてではない（`tools/_plugin`）が、サブモジュールをまたぐ                                                     |

## ルール更新ポイント

- `agent-compat/AGENTS.md`「このフォルダの責務」: `_plugin/` の例外を追記
- `maintenance/docs/repo-layout.md`「置き場所の判定基準」: 「agent-compat のツールの使い方スキル → `agent-compat/_plugin/agent-compat-tools/skills/`」の行を追加
- `maintenance/docs/tool-companion-skills.md`「置き場所」: `agent-compat/_plugin/` を併記
- `maintenance/plugin/skills/exploring-this-repo/SKILL.md`: 地図に `agent-compat/hooks/`・`logs/`・`_plugin/` を追加（`meta.version` を上げる）

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: (1) プラグインとスキル本体、(2) SSOT 登録と生成器・検査の対応（生成結果の diff を確認）、(3) 規約文書・`.links.yaml` 更新と `just links-sync`。最後に `uv run plans/lint_plans.py plans`、各 pre-commit を通し、別ディレクトリから `agent-logs sources` が動くこと（`uv tool install --editable`）を確認する。

## 実行記録

- 2026-11-17（Step5 完了時）: 計画どおり。完了記録は [progress/99-completion.md](progress/99-completion.md)。
  - 決め打ちの対応: `generate_readme_tools_section.py` の導入文、`check_skill_repo_tools.py` の `TOOLS_PATH_PATTERN`（`agent-compat/<dir>/<name>` を対象に足し、`my-tools/` のような長い語の途中で `tools/` に当たらないよう後読みを付けた）、`precommit` の検査 glob に `agent-compat/**/pyproject.toml`。`plugin_source.py`・skill-tools・skills-site は `ai-tools.yaml`／サブモジュール表から汎用に解決しており変更不要。
  - `claude-logs-investigate` の「何をしたいか」表に横断検索の行（`agent-logs-cli` への導線）を足し、1.0.4 へ。
