---
type: Plan Step
status: planning-breakdown
---

# Step 3: ログ仕様の知識スキル

> [02-research-log-formats.md](02-research-log-formats.md) の続き。Step2 の調査結果を、ツールに依存しない知識として残す。

## やること

各 AI コーディングツールのローカルログ仕様（所在・形式・レコード構造・注意点）を知識スキルとして書く。Claude Code は既存の `claude-logs-investigate` に参照ファイルを足し、他ツールは `ai-tools-knowledge` にツールごとの新スキルを作る。Step4 の CLI はここを仕様の正本として参照する。

## 読むべきファイル・実行推奨Grep

**書き方の基準（優先度: 高）**

- 読む: `skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md` と `bestpractices.md` — SKILL.md の書き方
- 読む: `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md`・`otel-reference.md` — 追記先の既存構成と参照ファイルの粒度
- 読む: `skills/plugins/ai-tools-knowledge/skills/cursor-memory/`・`kilo-memory-guide/` — 他ツール知識スキルの命名・frontmatter・`requires_skills` の付け方
- 読む: `registry/meta_field.yaml`・`maintenance/docs/skill-meta-fields.md` — meta フィールド

**配布への影響（優先度: 中）**

- 読む: `registry/ai-tools.yaml` の `workspace_copies`（`include: ["cline-*"]` 等）— 新スキル名が Cline・Kilo・Antigravity 向けコピーに入るか
- 読む: `skills/plugins/ai-tools-knowledge/skills/CATALOG.md`・`skills/plugins/cc-knowledge/skills/CATALOG.md` — 生成カタログ（手編集しない）

## 触るファイル

### 新規

- `skills/plugins/ai-tools-knowledge/skills/cursor-logs/SKILL.md`＋`format.md`（B・C 系統の詳細）
- `skills/plugins/ai-tools-knowledge/skills/cline-logs/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/kilo-logs/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/antigravity-logs/SKILL.md`＋`format.md`（protobuf の enum・フィールド番号）
- `skills/plugins/ai-tools-knowledge/skills/codex-logs/SKILL.md`
- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/log-format.md` — ローカルログのファイル別仕様

### 変更

- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md` — `log-format.md` への導線、`meta.version` を上げる
- 生成物（各 `CATALOG.md`・`.claude-plugin/skill-catalog.json` 等）は pre-commit・生成スクリプトに任せる

## 決定事項・注意点／落とし穴

| 決定・注意                                                                                                                                                                                                                                                                                                                      | 理由                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 他ツールはツールごとに `<tool>-logs` スキルを新設し、既存の `*-docs`（公式ドキュメント全般）には混ぜない                                                                                                                                                                                                                        | 既存の `*-memory`・`*-cli-use` と同じ「関心ごとに 1 スキル」の粒度。ログ調査で発火させやすい description にできる |
| Claude Code は新スキルを作らず `claude-logs-investigate` に参照ファイルを足す                                                                                                                                                                                                                                                   | 既にローカルログの所在を扱っており、スキルが重複する                                                              |
| 各スキルは「公式に記載あり」と「実データからの推定（バージョン依存・未保証）」を節で分け、確認したバージョンと日付を書く                                                                                                                                                                                                        | 非公開形式は予告なく変わる。CLI が壊れたときの切り分けに使う                                                      |
| 会話本文・秘密情報を含む実ログをサンプルとして貼らない。構造は架空値で示す                                                                                                                                                                                                                                                      | スキルは公開サイト・マーケットプレイスで配布される                                                                |
| スキル本文に agent-logs CLI の使い方は書かない（`requires_skills` にも入れない）。CLI 側スキルから知識スキルを参照する一方向                                                                                                                                                                                                    | 知識スキルはツール非依存に保つ（[tool-companion-skills](../../maintenance/docs/tool-companion-skills.md)）        |
| 各スキルの章立ては共通にする: 所在（Windows/POSIX・環境変数での上書き）→ 保存系統と正本 → レコード構造（フィールド表、架空値の最小例）→ セッション⇔プロジェクト対応 → 読み取り安全性（SQLite の開き方）・保持期間 → 秘密情報（読まないファイル・出さないフィールド）→ 公式記載／実データ推定の区別と確認バージョン → 未確認事項 | Step2 の調査観点と同じ並び。CLI のアダプタがそのまま対応付けられる                                                |
| `cursor-logs` は 3 系統（A: `projects/*/agent-transcripts` の JSONL、B: CLI `chats/` の `store.db`、C: IDE `state.vscdb`）を分けて書き、A を正本、B・C を補完と明記する。B の protobuf root blob と C の `cursorDiskKV` キー接頭辞は `format.md` に分ける                                                                       | 1 ファイルに収まらない量。A に時刻・モデル・ツール結果が無いことが最大の注意点                                    |
| `cline-logs` は SDK セッション形式（`~/.cline/data/sessions/`）とレガシーのタスク形式（VS Code の globalStorage、旧 CLI の `~/.cline/data/tasks/`）の 2 系統を書く。`kilo-logs` から「旧 Kilo Code 拡張（v4 系、Cline フォーク）の tasks 形式は `cline-logs` のレガシー形式を参照」とリンクする                                 | Kilo の旧形式は Cline レガシーと同型。仕様を重複させない                                                          |
| `kilo-logs` は `kilo.db` の `session`/`message`/`part`/`project` 表に絞り、他の表（`account`・`credential`・`session_share` 等）は秘密情報として「読まない」と書く。`event` 表は正本ではないと明記                                                                                                                              | 公式 session-history ページの SQL 例と一致。秘密情報の表が同じ DB にある                                          |
| `antigravity-logs` は 3 ルート（`~/.gemini/antigravity/`・`antigravity-cli/`・`antigravity-ide/`）、索引 `conversation_summaries.db`、本文の `transcript_full.jsonl`、protobuf の `conversations/<id>.db`（`step_type` の enum 表とフィールド番号は推定として `format.md` へ）を書く                                            | 本文は平文で読めると分かったため、所在だけでなく構造まで書く                                                      |
| `codex-logs` は実データが無いので、全項目の根拠を公式ドキュメントと openai/codex のソース（コミット SHA とファイルパス）にする。legacy／paginated モードの違い、`.jsonl.zst` 圧縮、`token_count` の累積を必ず書く                                                                                                               | 推定と区別できるよう出典を明示する                                                                                |
| `claude-logs-investigate/log-format.md` には既存 SKILL.md に無い事項を書く: `subagents/`（`.meta.json`・workflows）、1 ブロック 1 行の分割と usage の重複、`cost-state`・`ai-title` 等の新しい種別、ドライブレターの大小によるディレクトリ分裂、`history.jsonl`・`stats-cache.json` がスイープされないこと                      | Step2 で既存スキルとの差分として洗い出した                                                                        |
| `cline-logs` は `workspace_copies` の `cline-*` に入って `.cline/skills/` へコピーされる。Kilo・Antigravity の include パターンも確認し、必要なら `ai-tools.yaml` に足す                                                                                                                                                        | 各ツールで自分のログを調べる場面がある                                                                            |

## ルール更新ポイント

- 新規ルールは不要。`ai-tools-knowledge` の README・カタログに一覧があれば生成に任せる。
- `agent-compat/.links.yaml` に `_umbrella/cc-knowledge`（→ `skills/plugins/cc-knowledge`）を足すかは Step5 で判断（agent-compat を単体で開いて CLI を直すとき Claude Code の仕様を参照できるように）。

## 進め方

- **実行主体**: メインエージェント。スキル 1 本ずつの下書きはサブエージェントに委任してよいが、Step2 の要約と [progress/02-research-results.md](progress/02-research-results.md) の該当ツールの節だけを渡し、実データを読み直させない。progress の内容は実データ推定を含むので、スキルでは「推定」の節に置く。
- **TODO化**: スキル 1 本 = 1 項目（計 6）。skills サブモジュールでまとめて 1 コミット、アンブレラでポインタ更新。

## 実行中に判明した変更

- 2026-11-17（Step2 完了時）: 調査結果を受けて、共通の章立て、Cursor 3 系統・Cline 2 系統の書き分け、Kilo の旧形式を Cline レガシーへリンクすること、Antigravity を構造まで書くこと、`cursor-logs`・`antigravity-logs` に `format.md` を足すことを決定事項と触るファイルに反映した。
