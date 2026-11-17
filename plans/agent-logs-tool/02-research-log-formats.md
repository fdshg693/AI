---
type: Plan Step
status: planning-breakdown
---

# Step 2: 各ツールのローカルログ形式の調査

> [00-overview.md](00-overview.md) の続き。このステップではコードを書かない。結果は Step3（知識スキル）と Step4（アダプタ）の本文へ直接反映する。

## やること

v1 対象 6 ツールについて、ローカルに残るログ・履歴の所在、ファイル形式、レコード構造、セッション・プロジェクトとの対応付け、検索・集計に使えるフィールド（時刻・ロール・ツール呼び出し・モデル・トークン）を確定する。この PC の実データ（`~/` 配下）と公式ドキュメントを突き合わせ、公式に書かれていない部分は「実データからの推定・未保証」と区別する。

## 調査観点

計画時点で見えている候補（要確認）:

| ツール      | 実データ候補                                                                                                                                                          | 確認したいこと                                                                                                                               |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Code | `~/.claude/projects/<encoded-cwd>/<session>.jsonl`・`history.jsonl`・`sessions/`・`debug/`・`file-history/`・`stats-cache.json`                                       | jsonl のレコード種別（user/assistant/tool_use/tool_result/summary 等）、`usage` の位置、サブエージェント・compact の表現、cwd エンコード規則 |
| Cursor      | `~/.cursor/chats/`・`projects/`・`ai-tracking/`・`agents/`、VS Code 系の `%APPDATA%/Cursor/User/{globalStorage,workspaceStorage}/state.vscdb`                         | CLI（cursor-agent）と IDE で保存先が違うか、SQLite のキー（`cursorDiskKV` 等）と JSON 構造                                                   |
| Cline       | `~/.cline/data/`、`%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/<id>/`（`api_conversation_history.json`・`ui_messages.json`・`task_metadata.json`） | CLI と拡張で形式が同じか、トークン・コストの所在                                                                                             |
| Kilo Code   | `~/.local/share/kilo/`（`kilo.db`・`storage/`・`log/`）、`%APPDATA%/Code/User/globalStorage/kilocode.kilo-code/`                                                      | 新 CLI（opencode 系）と旧拡張（Cline 系）の 2 系統の有無、SQLite スキーマ                                                                    |
| Antigravity | `~/.gemini/antigravity/`（conversations・brain 等）・`antigravity-cli/`・`logs/`                                                                                      | 会話本文が平文で読めるか（protobuf 等なら v1 は所在・メタデータだけに絞る）                                                                  |
| Codex       | 実データ無し。公式・既知の `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`・`history.jsonl`                                                                            | レコード種別と `session_meta`・`turn_context`・`event_msg` の構造。フィクスチャを作れる粒度まで                                              |

共通観点:

- 書き込み中のファイル・WAL モード SQLite を読み取り専用で安全に開けるか（ロック・`mode=ro`・`immutable` の可否）
- 削除・ローテーション・保持期間（Claude Code の `cleanupPeriodDays` 等）
- 秘密情報が入りうるフィールド（環境変数・トークン・ファイル内容）
- Windows と POSIX でのパスの違い（`%APPDATA%` と `~/.config` 等）
- 既存資産: `skills/plugins/cc-knowledge/skills/claude-logs-investigate/`、`tools/coding-agent/ai-usage/`（各ツールの使用量取得の知見）、`infra/ai-logs/`（OTel 側。ローカルファイルとは別物）、`ai-tools-knowledge` の各 `*-docs` スキルの references

## 調査結果

（未実施。ツールごとに「所在・形式・主要レコード・根拠（公式URL／実データ推定）」の要約を書き、詳細は `progress/02-research-results.md` へ）

## 進め方

- **実行主体**: ツールごとに独立なので、6 ツールを Explore／general-purpose サブエージェントへ並列委任してよい（実データは構造だけを報告させ、会話本文・秘密情報を持ち帰らせない）。公式ドキュメントは各ツールの `*-docs` 知識スキルと `web-lookup` で引く。採否と要約はメインが行う。
- **TODO化**: ツール 1 つ = 1 項目。最後に Step3・Step4 の本文（知識スキルの章立て、アダプタの「決定事項」）を更新する項目を 1 つ。
