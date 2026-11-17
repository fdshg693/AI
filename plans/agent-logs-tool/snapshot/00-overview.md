---
type: Plan
status: planning-breakdown
---

## 実装ステータス

- [ ] [01-move-agent-tooling-to-hooks.md](01-move-agent-tooling-to-hooks.md) — `agent-compat/agent-tooling/` を `agent-compat/hooks/agent-tooling/` へ移し、全参照を更新
- [ ] [02-research-log-formats.md](02-research-log-formats.md) — 各 AI コーディングツールのローカルログの所在・形式を調査（実データ＋公式ドキュメント）
- [ ] [03-knowledge-skills-log-specs.md](03-knowledge-skills-log-specs.md) — ログ仕様を知識スキル（`ai-tools-knowledge`・`cc-knowledge`）に書く
- [ ] [04-agent-logs-cli.md](04-agent-logs-cli.md) — 検索・集計・集約 CLI `agent-logs` を `agent-compat/logs/agent-logs/` に実装
- [ ] [05-plugin-and-registration.md](05-plugin-and-registration.md) — `agent-compat/_plugin/` に使い方スキルのプラグインを作り、各 SSOT に登録

# AI コーディングツールのログ検索・集計ツール 実装プラン - 概要

## 要件

- 各 AI コーディングツールがこの PC の `~/` 配下に残すログ（セッション・会話・ツール呼び出し等）を、横断して検索・集計・集約できる CLI を `agent-compat/` に作る。
- v1 の対象は Claude Code・Cursor・Cline・Kilo Code・Antigravity・Codex。Codex はこの PC に実データが無いため、仕様とテスト用フィクスチャだけで対応する。GitHub Copilot（CLI・VS Code）は v1 対象外。
- 既存の `agent-compat/agent-tooling/`（フック中心）は `agent-compat/hooks/` 配下へ移し、新ツールは `agent-compat/logs/` 配下に置く。
- 各ツールのログ仕様は知識スキル（他ツールは `skills/plugins/ai-tools-knowledge/skills/`、Claude Code は `skills/plugins/cc-knowledge/skills/`）に書き、新 CLI の使い方スキルは `tools/_plugin/my-tools` と同型のプラグインとして `agent-compat/_plugin/` に置く。

## 実装ステップ

1. [01-move-agent-tooling-to-hooks.md](01-move-agent-tooling-to-hooks.md) — 既存フォルダの移動と参照更新（他ステップと独立。最初に済ませて以降の参照パスを確定させる）
2. [02-research-log-formats.md](02-research-log-formats.md) — ログ形式の調査（Step3・4 の前提）
3. [03-knowledge-skills-log-specs.md](03-knowledge-skills-log-specs.md) — 知識スキルの作成・追記
4. [04-agent-logs-cli.md](04-agent-logs-cli.md) — CLI 本体の実装
5. [05-plugin-and-registration.md](05-plugin-and-registration.md) — 使い方スキル・プラグイン・SSOT 登録・ドキュメント更新

## 主要な決定事項

| 決定 | 理由 |
| ---- | ---- |
| 既存は `agent-compat/hooks/agent-tooling/` へ丸ごと移す。パッケージ名 `agent-tooling`・コマンド名は変えない。`formats/`・`docs/` は移さない | ユーザー選択。パッケージ名を保てば `uv tool install` 済みの利用者・`catalog.json` の契約への影響がパス変更だけで済む |
| 新 CLI は `agent-compat/logs/agent-logs/`（Python・uv、パッケージ `agent_logs`、コマンド `agent-logs`） | ユーザー選択（Python）。agent-tooling と同じ技術スタックで、SQLite（Kilo 等）を標準ライブラリで読める。`hooks/` と `logs/` を並べて将来の追加にも同じ形で対応する |
| agent-logs は agent-tooling に依存させない独立パッケージにする | 配布物どうしで依存させない既存方針（[repo-layout](../../maintenance/docs/repo-layout.md) の `is_link_like` の扱いと同じ） |
| 読み取り専用。ログは書き換えず、外部へ送らない。v1 は永続インデックスを持たず都度走査する | ログに秘密情報が含まれうる。まず正しさを優先し、遅ければ後でキャッシュを足す |
| ツールごとの差はアダプタ層で吸収し、共通の正規化スキーマ（Session / Event）で検索・集計する | ログ形式はツールごと・バージョンごとに変わる。差分を 1 か所に閉じ込める |
| ログ仕様の正本は知識スキル、CLI のスキルは使い方と判断だけ | [tool-companion-skills](../../maintenance/docs/tool-companion-skills.md) の役割分担。仕様を CLI スキルに重複させない |
| 使い方スキルのプラグインは `agent-compat/_plugin/agent-compat-tools/`（`tools/_plugin/my-tools` と同型） | ユーザー要望。agent-compat のツールに付属するスキルを同じサブモジュールに置く。`agent-compat/AGENTS.md` の「スキルの実体は置かない」を例外付きに改める必要がある（Step5） |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `agent-compat/hooks/README.md`・`agent-compat/logs/README.md`
- `agent-compat/logs/agent-logs/`（pyproject・`agent_logs/`・`tests/`・README・AGENTS.md・CLAUDE.md・justfile）
- `agent-compat/_plugin/agent-compat-tools/`（`.claude-plugin/plugin.json`・README・`skills/agent-logs-cli/`）
- `skills/plugins/ai-tools-knowledge/skills/{cursor,cline,kilo,antigravity,codex}-logs/`
- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/log-format.md`

### 変更

- `agent-compat/agent-tooling/` → `agent-compat/hooks/agent-tooling/`（移動）と、その参照元一式（Step1 に列挙）
- `agent-compat/AGENTS.md`・`agent-compat/README.md`・`agent-compat/.links.yaml`
- `registry/ai-tools.yaml`・`registry/repo-tools.yaml`・`registry/repo-hooks.yaml`・`pyproject.toml`・`uv.lock`
- `maintenance/docs/repo-layout.md`・`maintenance/docs/hook-distribution.md`・`maintenance/docs/tool-companion-skills.md`
- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md`

## ルール更新ポイント

- `agent-compat/AGENTS.md`（Step1・Step5）: 「このフォルダの責務」に `hooks/`・`logs/`・`_plugin/` を足し、「スキルの実体は置かない」に「agent-compat のツールに付属する使い方スキル（`_plugin/`）は例外」と書く
- `maintenance/docs/repo-layout.md`（Step1・Step5）: 置き場所の判定基準表とサブモジュール表の agent-compat 行を新構成に合わせる
- `maintenance/docs/tool-companion-skills.md`（Step5）: 使い方スキルの置き場所に `agent-compat/_plugin/` を追加
- `agent-compat/logs/agent-logs/AGENTS.md`（Step4、新規）: アダプタ追加手順、読み取り専用・外部送信禁止、フィクスチャに実ログを入れない規約

## 進め方

- **TODO化**: ステップ一覧の各項目を 1 つの TODO にする。各ステップの実行主体・粒度は各ステップファイルの「進め方」に書く。
- サブモジュールをまたぐので、コミットは各サブモジュール内 → アンブレラのポインタ更新の 2 段階（`maintenance/plugin/skills/committing/SKILL.md`）。
- プランレビュー（サブエージェント 1 回）→ `uv run plans/snapshot_plan.py plans/agent-logs-tool` で凍結してから着手する。
