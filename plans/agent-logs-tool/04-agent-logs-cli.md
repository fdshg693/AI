---
type: Plan Step
status: implementing-done
---

# Step 4: agent-logs CLI の実装

> [03-knowledge-skills-log-specs.md](03-knowledge-skills-log-specs.md) の続き。ログ形式の前提は Step2 の調査結果と Step3 の知識スキルに従う。

## やること

`agent-compat/logs/agent-logs/` に Python（uv）の CLI `agent-logs` を作る。ツールごとのアダプタがローカルログを読み、共通スキーマに正規化し、横断で一覧・検索・集計する。v1 のサブコマンド:

- `sources` — 対象ツールごとの検出結果（ログの場所・有無・件数・最終更新）
- `sessions` — セッション一覧（ツール・プロジェクト/cwd・開始/終了・メッセージ数・モデル）
- `show <session>` — 1 セッションの正規化イベント列
- `search <query>` — 本文・ツール呼び出しの横断検索（正規表現可）
- `stats` — 集計（期間・ツール・プロジェクト・モデル・ツール呼び出し名別の件数、取れる場合はトークン）

共通フィルタ: `--tool`・`--since/--until`・`--project`・`--role`。出力は人間向けの表と `--json`（一覧系は NDJSON）。

## 読むべきファイル・実行推奨Grep

**既存パッケージの型（優先度: 高）**

- 読む: `agent-compat/hooks/agent-tooling/pyproject.toml`・`README.md`・`justfile`・`agent_tooling/sessions_cli.py` — 同じサブモジュールの CLI の作り（argparse、`--json`、`--watch` の出し分け、依存ゼロ方針）
- 読む: `agent-compat/hooks/agent-tooling/agent_tooling/core/fs_links.py` — Junction を辿らない走査（`is_link_like`）。パッケージ内に同じ関数を持つ方針
- 読む: Step3 で作った各 `<tool>-logs` スキルと `claude-logs-investigate/log-format.md` — アダプタの仕様。要約は [02-research-log-formats.md](02-research-log-formats.md) の「調査結果」の表

**似た既存ツール（優先度: 中）**

- 読む: `tools/coding-agent/ai-usage/ai_usage_core/` — ツールごとのコレクタを try/except で分離する構成
- 読む: `tools/skill-tools/` の README・`pyproject.toml` — `uv tool install --editable` 前提の配布

**登録・検査（優先度: 中）**

- 読む: `pyproject.toml`（ルートの uv workspace members）・`maintenance/docs/justfile-conventions.md`

## 触るファイル

### 新規

- `agent-compat/logs/README.md` — `logs/` の案内
- `agent-compat/logs/agent-logs/pyproject.toml` — パッケージ `agent-logs`、エントリ `agent-logs = agent_logs.cli:main`、実行時依存なし（dev に pytest）
- `agent-compat/logs/agent-logs/agent_logs/cli.py` — サブコマンドと出力整形
- `agent-compat/logs/agent-logs/agent_logs/model.py` — 正規化スキーマ（Session・Event）
- `agent-compat/logs/agent-logs/agent_logs/adapters/{claude,cursor,cline,kilo,antigravity,codex}.py` — ツール別の検出と読み取り
- `agent-compat/logs/agent-logs/agent_logs/query.py`・`stats.py` — フィルタ・検索・集計
- `agent-compat/logs/agent-logs/tests/`＋`tests/fixtures/<tool>/` — 架空データのフィクスチャで各アダプタと集計を検証。Codex は [progress/02-research-results.md](progress/02-research-results.md) の最小 rollout 例を元にする
- `agent-compat/logs/agent-logs/{README.md,AGENTS.md,CLAUDE.md,justfile}`

### 変更

- `pyproject.toml`（ルート）・`uv.lock` — workspace member に追加
- `agent-compat/README.md` — 中身に `logs/` を追加
- `agent-compat/.gitignore` — 先頭 `/` の無い `logs/`・`*.sqlite3`・`*.log` が `logs/agent-logs/` 一式とフィクスチャを無視する。`/logs/*.log` 等に絞るか否定パターンを足す（`git check-ignore` で確認）

## 決定事項・注意点／落とし穴

| 決定・注意                                                                                                                                                                                                                                                                                                                                                                                                                                           | 理由                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| アダプタは共通インターフェース（`detect()`・`iter_sessions(filters)`・`iter_events(session)`）を実装し、1 アダプタの失敗は警告にして他を続ける                                                                                                                                                                                                                                                                                                       | ログ形式は非公開で壊れやすい。ai-usage と同じ分離方針                                                                                                             |
| ルートはツールごとの環境変数（`AGENT_LOGS_<TOOL>_DIR`）で上書きでき、既定は Windows/POSIX の両方を持つ                                                                                                                                                                                                                                                                                                                                               | テスト・別マシン・Codex（実データ無し）のフィクスチャ検証に必要                                                                                                   |
| SQLite は `file:///<path>?mode=ro` の URI で開く（パスは `/` 区切りにして `urllib.parse.quote`）。失敗したら一時ディレクトリへ `.db`＋`-wal` をコピーして読み、`immutable=1` は使うなら「最新分が欠ける」と警告する。Antigravity の DB は既定でコピー方式（または immutable）にする                                                                                                                                                                  | Cursor・Cline・Kilo は起動中でも `mode=ro` で開けた。Antigravity は `mode=ro` で開いた後に `-wal`/`-shm` が生じた疑いがある（Step2）。immutable は WAL を読まない |
| v1 はインデックスを持たず、`--since` をファイル mtime の前段フィルタにも使って走査量を減らす                                                                                                                                                                                                                                                                                                                                                         | 正しさ優先。遅ければ後でキャッシュ（`~/.cache/agent-logs`）を足す                                                                                                 |
| 正規化できないレコードは `kind: "raw"` で残し、`show --raw` で元 JSON を見せる                                                                                                                                                                                                                                                                                                                                                                       | 未知のレコード種別を捨てずに調査できる                                                                                                                            |
| `search` の出力は既定で前後を切り詰め、全文は `show` で見る                                                                                                                                                                                                                                                                                                                                                                                          | ログに秘密情報・巨大なツール出力が入る                                                                                                                            |
| フィクスチャに実ログを使わない（架空値で作る）。AGENTS.md に明記                                                                                                                                                                                                                                                                                                                                                                                     | サブモジュールは公開リポジトリ                                                                                                                                    |
| SQLite フィクスチャはバイナリをコミットせず、テスト時に SQL から作る                                                                                                                                                                                                                                                                                                                                                                                 | `.gitignore` の `*.sqlite3` に掛からず、差分もレビューできる                                                                                                      |
| Antigravity は 3 段のフォールバック: (1) `brain/<id>/.system_generated/logs/transcript_full.jsonl`（無ければ `transcript.jsonl`）→ (2) `conversation_summaries.db` のメタデータだけ（本文なし）→ (3) `conversations/<id>.db` の protobuf の最小デコーダは v1 では作らない。3 ルート（`antigravity`・`antigravity-cli`・`antigravity-ide`）を走査し会話 ID で重複除去する                                                                             | Step2 で本文は平文と判明。ただし transcript は 2026-10-29 以降の会話にしか無く、protobuf はスキーマ非公開で番号が変わりうる                                       |
| 正規化スキーマ: Session に `id, tool, source`（cli/ide/vscode-legacy 等の下位区分）`, project, cwd, started_at, ended_at, model, title, parent_id, tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, cost`。Event に `session_id, ts, role, kind, tool_name, call_id, text, tokens_*, cost, raw`。`kind` は `message`/`reasoning`/`tool_call`/`tool_result`/`system`/`summary`/`usage`/`turn_end`/`raw`。取れない値は `None`（0 と区別） | Step2 の写像で全ツールに共通して取れる範囲。Kilo の `cost=0` のように 0 と未計測が混ざる                                                                          |
| トークンの重複計上を防ぐ: Claude Code は `message.id` ごとに最後の usage だけ、Codex は `token_count` の最後の `total_token_usage`（あれば `token_usage_record` を優先）、Kilo・Cline は assistant メッセージ単位、Antigravity は `PLANNER_RESPONSE` 単位。セッション合計はツールの累計値（Claude `cost-state`、Kilo `session` 列、Cline `metadata.usage`）を優先                                                                                    | Step2: Claude は 1 応答が複数行に分かれ usage が繰り返される。Codex は累積値                                                                                      |
| 系統が複数あるツールは 1 アダプタ内でソースを分ける: Cursor は transcript JSONL を正本にし、CLI `store.db`・IDE `state.vscdb` は cwd・title・model・時刻の補完だけ（v1 は IDE の bubble 本文を読まない）。Cline は SDK セッション（`~/.cline/data`）とレガシーのタスク（VS Code 系 globalStorage）の両方を読み、移行で重なる ID を除く。Codex は `sessions/`・`archived_sessions/` を読み、一覧は `state_5.sqlite` があれば使う                      | Step2: Cursor の IDE DB は 1.6GB で形式が版ごとに変わる。Cline は 2 系統が併存                                                                                    |
| プロジェクト照合はパス正規化（ドライブレターを大文字化、区切りを `/`、`file://` URI はデコード）してから比べる。Claude Code・Cursor のディレクトリ名（cwd の非可逆エンコード）は前段の絞り込みにだけ使い、正はレコード／メタの cwd                                                                                                                                                                                                                   | Step2: 全ツールでドライブレターの大小が混在。Claude Code は同じフォルダが 2 ディレクトリに分かれる                                                                |
| 秘密情報の除外を一覧で持つ: 読まないファイル（`~/.claude/.credentials.json`、Cline `data/secrets.json`・`settings/providers.json`、Kilo `auth.json`、Codex `auth.json`）、読まない表（Kilo は `session`/`message`/`part`/`project` 以外、Cursor `ItemTable` の `secret:*`）、出さないフィールド（`*EncryptionKey`、Antigravity `csrfToken`、Claude `session-owner`）                                                                                 | Step2 で各ツールに認証情報が同居していると判明                                                                                                                    |
| Codex の `.jsonl.zst`（7 日超の rollout）は、Python 3.14 以上なら `compression.zstd` で読み、それ未満ではスキップして `sources` に件数を警告する（実行時依存は足さない）                                                                                                                                                                                                                                                                             | 依存ゼロ方針。ルート環境は 3.13                                                                                                                                   |
| 巨大な入力を前提にする: JSONL は行ストリームで読み、壊れた最終行は捨てる。Claude Code の `api-request*` 行は文字列判定でパース前に飛ばす。Kilo（2.2GB）は既存インデックスに乗る SQL で絞る                                                                                                                                                                                                                                                           | Step2 の実測（1 行 ~1MB、DB 1.6〜2.2GB）                                                                                                                          |
| 時刻は全て UTC の aware datetime に正規化する: ISO8601（`Z`/`+00:00`/7 桁小数）、epoch 秒・ミリ秒、protobuf `{seconds,nanos}`、Cursor transcript の `<timestamp>Weekday, Mon D, YYYY, H:MM AM (UTC+9)</timestamp>`（ロケール非依存の自前パーサ）。Antigravity の `0001-01-01` は未設定扱い                                                                                                                                                           | Step2: ツールごとに形式が違う                                                                                                                                     |
| パッケージ内で Junction・symlink を辿らない                                                                                                                                                                                                                                                                                                                                                                                                          | [repo-layout](../../maintenance/docs/repo-layout.md) の走査規約                                                                                                   |

## ルール更新ポイント

- `agent-compat/logs/agent-logs/AGENTS.md`（新規）: アダプタ追加手順（知識スキル→アダプタ→フィクスチャ→テストの順）、読み取り専用・外部送信禁止、フィクスチャに実ログを入れない、仕様の正本は知識スキル
- `agent-compat/AGENTS.md`「このフォルダの責務」に `logs/` を追記（Step1 で枠を作っていれば中身だけ）

## 進め方

- **実行主体**: メインエージェント。共通スキーマと CLI 骨格を先に作り、アダプタはツールごとにサブエージェントへ並列委任してよい（各アダプタは対応する知識スキルとフィクスチャだけを入力にする）。
- **TODO化**: (1) スキーマ・CLI 骨格・`sources`、(2) Claude アダプタ＋`sessions`/`show`、(3) 残り 5 アダプタ（1 つ 1 項目）、(4) `search`・`stats`、(5) README・AGENTS.md・workspace 登録。各項目で `just --justfile agent-compat/logs/agent-logs/justfile test` を通し、実機で `agent-logs sources` の結果を目視確認する。

## 実行中に判明した変更

- 2026-11-17（Step2 完了時）: SQLite の開き方、Antigravity のフォールバック、正規化スキーマ、トークンの重複除去、複数系統の扱い、パス・時刻の正規化、秘密情報の除外一覧、Codex の zstd を決定事項に反映した。重複していた「SQLite フィクスチャ」の行を 1 つにした。
- 2026-11-17（Step4 完了時）: 共通部分・Claude アダプタはメイン、残り 5 アダプタはサブエージェント 5 体へ並列委任。テスト 40 件、ruff クリーン。実機（Codex 以外）で全ツール `stats` が約 10 秒（2,931 セッション）、警告なし。Antigravity の DB は前後で `-wal`/`-shm` の変化なしを確認。
  - 実装で足した決定: ルート解決に `AGENT_LOGS_HOME`・`AGENT_LOGS_APPDATA` を追加（テストを密閉するため。ツール別 `AGENT_LOGS_<TOOL>_DIR` より手前の全体置き換え）。SQLite フィクスチャは `<name>.db.sql` を `conftest.py` が組み立てる。`show` にも `--tool` を付けた。`stats --by` に `month`・`source` を追加。
  - トークンの意味を揃えた: `tokens_in` はキャッシュ読み出しを含まない。Codex（`input_tokens − cached_input_tokens`）と Cline SDK（`inputTokens` が `cacheReadTokens` を含むと実データで判明）は差し引く。Kilo の `tokens_out` は reasoning を含む。
  - Cline のセッション合計は「`metadata.usage` を優先」を改め、`metadata.usage` と metrics 合計の大きい方にした（再開したセッションで `metadata.usage` が最後の実行分だけになる例が 2 件）。
  - `.gitignore`: `logs/` 規則を削除（`/logs/` でもこのフォルダ自体に掛かり、Antigravity のフィクスチャは途中に `logs/` を含む）。`*.log`・`*.sqlite3` は影響なし。
  - **知識スキルへの差し戻し候補（未反映。Step5 か別作業で `skills` 側を直す）**: Cursor — `meta.json` の無い CLI チャット（`store.db` だけ）が 152 中 15、`composerHeaders` に `name` が無い行、タグの無い transcript。Cline — 上記 `metadata.usage` と `inputTokens` の包含関係。Kilo — 仕様に無いインデックス・列（`workspace_id` 等）、`tokens.output` は reasoning を含まない。Antigravity — `antigravity-ide` に `conversation_summaries.db` が無い、transcript は 2026-10-29 より前にも旧ルートに 553 件ある、tool result のステップ種別が `GENERIC` 以外にも多数、`title` は大半が空で `preview` が実質の題、token/model は一部の `PLANNER_RESPONSE` にしか無い。Codex — `input_tokens` がキャッシュを含むか、`token_usage_record` と `token_count` の関係が仕様で不明（実データ無し）。
