---
type: Plan Step
status: implementing-done
---

# Step 2: 各ツールのローカルログ形式の調査

> [00-overview.md](00-overview.md) の続き。このステップではコードを書かない。結果は Step3（知識スキル）と Step4（アダプタ）の本文へ直接反映する。詳細な調査結果 → [progress/02-research-results.md](progress/02-research-results.md)

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

2026-11-17 に実施。ツールごとの要約（所在・形式・正本・取れる指標）。フィールド表・根拠 URL・未解決事項は [progress/02-research-results.md](progress/02-research-results.md)。ローカル保存形式はどのツールもほぼ非公開で、下記の大半は実データからの推定（バージョン依存・未保証）。

| ツール（確認版）                           | 正本にする入力                                                                                                                                                                                                                                         | 形式                                                                             | トークン / コスト                                                                                    | 主な落とし穴                                                                                                                                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Code（2.1.325）                     | `~/.claude/projects/<enc-cwd>/<sid>.jsonl`（子は `<sid>/subagents/agent-<id>.jsonl`＋`.meta.json`）                                                                                                                                                    | JSONL                                                                            | `assistant.message.usage`（`message.id` で重複除去）／`cost-state`（累積、最後の行がセッション合計） | assistant は 1 ブロック 1 行に分割され usage が繰り返される。ドライブレターの大小で同じフォルダが 2 ディレクトリに分かれる → cwd はレコードの `cwd` を正にする。`api-request*` は巨大で本文と重複するので読まない |
| Cursor（IDE 3.30 / CLI 2026.10）           | A: `~/.cursor/projects/<enc-cwd>/agent-transcripts/<sid>/<sid>.jsonl`（IDE・CLI 共通）。補完に B: `~/.cursor/chats/<md5(cwd)>/<id>/{meta.json,store.db}`、C: `%APPDATA%/Cursor/User/globalStorage/state.vscdb`（`composerHeaders` 表・`cursorDiskKV`） | JSONL／SQLite（B の会話順は protobuf）                                           | 取れない（bubble の `tokenCount` は全件 0）。cost は全系統で無し                                     | A には時刻・モデル・ツール結果が無い。時刻は user 本文の `<timestamp>` タグを解析。C は 1.6GB。`*EncryptionKey`・`secret:*` を出さない                                                                            |
| Cline（CLI 3.0 / 拡張 4.0）                | A: `~/.cline/data/sessions/<sid>/{<sid>.json,<sid>.messages.json}`＋索引 `data/db/sessions.db`（CLI と新しい拡張）。B: `%APPDATA%/Code/User/globalStorage/saoudrizwan.claude-dev/{state/taskHistory.json,tasks/<id>/}`（レガシー拡張）                 | JSON（jsonl ではない）／SQLite                                                   | A: assistant の `metrics`（キャッシュ・cost 含む）、B: `ui_messages` の `api_req_started`            | 2 系統を別に読み、移行で重なる分を除く。`secrets.json`・`settings/providers.json` は読まない。`CLINE_DATA_DIR` で上書き                                                                                           |
| Kilo Code（7.8）                           | `~/.local/share/kilo/kilo.db` の `session`／`message`／`part`／`project` 表だけ（CLI と現行拡張の共通の正本）                                                                                                                                          | SQLite（WAL、2.2GB、opencode 由来の Drizzle）                                    | assistant `message.data.tokens`／`cost`、セッション累計は `session` 列                               | 拡張の globalStorage は空（旧 Cline 系形式は無し）。`tool` part は呼び出しと結果が同居。session ID は降順。他の表（`account`・`credential` 等）は SELECT しない                                                   |
| Antigravity（agy 1.5.9 / LS 2.32）         | 一覧: `~/.gemini/antigravity/conversation_summaries.db`。本文: `brain/<id>/.system_generated/logs/transcript_full.jsonl`（2026-10-29 以降の会話だけ）。旧ルート `antigravity-cli/`・`antigravity-ide/` も同じ構成                                      | SQLite／JSONL／会話ごとの SQLite（`conversations/<id>.db`、中身は素の protobuf） | transcript の `input_tokens`/`output_tokens`。cost 無し                                              | **本文は平文で読める**（暗号化は思考署名だけ）。transcript が無い旧会話は protobuf だけ。`mode=ro` で開いた後に `-wal`/`-shm` が生じた疑い → immutable かコピーで開く。3 ルートを ID で重複除去                   |
| Codex（ソース main 885a1df、実データ無し） | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`（7 日超は `.jsonl.zst`）・`archived_sessions/`。一覧は `state_5.sqlite` の `threads`                                                                                                                    | JSONL `{timestamp,type,payload}`／SQLite                                         | `event_msg.token_count`（累積。最後の `total_token_usage` を使う）。cost 無し                        | legacy モードでは発話が `response_item` と `event_msg` に二重記録。zstd は Python 3.14 未満では標準ライブラリに無い。モデルは `turn_context` から                                                                 |

横断で分かったこと:

- SQLite は `mode=ro` の URI で、各ツールの起動中でも開けた（Cursor・Cline・Kilo）。`immutable=1` は WAL の未チェックポイント分を読まないので最後の手段。Antigravity だけは `mode=ro` で開いた後に `-wal`/`-shm` が生じた疑いがある。
- 削除・保持: Claude Code は `cleanupPeriodDays`（既定 30 日、公式）。Codex は削除せず圧縮。Cursor は自動クリーンアップの痕跡があるが基準不明。Cline・Kilo・Antigravity は自動削除の記載なし。
- プロジェクトの対応付け: Claude Code・Cursor はディレクトリ名が cwd の非可逆エンコード、Cline・Kilo・Codex は生パス、Antigravity は `file:///c%3A/...` の URI。Windows ではどれもドライブレターの大小が混在する。
- コストがローカルに残るのは Claude Code・Cline・Kilo だけ。Cursor はトークンも残らない。
- 未確認（実データに無かった）: compact／要約の表現（Claude Code・Kilo・Cline・Antigravity）、サブエージェント・チームの Cline の実データ、Codex の実ログ全般。

## 進め方

- **実行主体**: ツールごとに独立なので、6 ツールを Explore／general-purpose サブエージェントへ並列委任してよい（実データは構造だけを報告させ、会話本文・秘密情報を持ち帰らせない）。公式ドキュメントは各ツールの `*-docs` 知識スキルと `web-lookup` で引く。採否と要約はメインが行う。
- **TODO化**: ツール 1 つ = 1 項目。最後に Step3・Step4 の本文（知識スキルの章立て、アダプタの「決定事項」）を更新する項目を 1 つ。

## 実行中に判明した変更

- 2026-11-17: 調査を完了。Antigravity は本文が平文で読めたため、Step4 の「メタデータだけに絞る」想定を 3 段のフォールバックに改めた。Cline は 2 系統、Cursor は 3 系統の保存先があり、Step3・Step4 の本文に反映済み。
- 調査は 6 ツールを読み取り専用のサブエージェントに並列委任した（実ログは構造だけを集計させ、本文は持ち帰らせていない）。
