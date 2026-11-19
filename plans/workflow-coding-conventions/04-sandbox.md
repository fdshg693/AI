---
type: Plan Step
status: ready
---

# Step 4: sandbox — 既定モデル・上限を `config.toml` へ

## やること

`poller.py` の `Config.from_env()` が持つ既定値（`SANDBOX_MODEL="sonnet"`・ターン数・リソース上限・パス等）と、`run_agent.py` のコンテナ側既定 `"sonnet"` をやめ、ホストの `sandbox/orchestrator/config.toml` から読む。コンテナへはホストで解決したモデル ID と上限を環境変数で渡し、コンテナ側は既定値を持たず必須として扱う。

## 読むべきファイル・実行推奨Grep

**ホスト / コンテナの境界を確認するため（優先度: 高）**

- 読む: `workflow/sandbox/orchestrator/poller.py` — `Config` と `from_env()`、`.env` ローダー
- 読む: `workflow/sandbox/orchestrator/run_agent.py` — `run_container()` の `docker run -e` 列挙と `container_main()`、`_run_agent_query()`
- 読む: `workflow/sandbox/docker/Dockerfile` — コンテナ内の Python バージョン。orchestrator はイメージに COPY されず、`run_agent.py` が `-v {ORCHESTRATOR_DIR}:/opt/orchestrator:ro` で bind mount している
- Grep: `SANDBOX_` in `workflow/sandbox` — 環境変数の全利用箇所

**写し元（優先度: 高）**

- 読む: Step 2 の `workflow/claude-wrapper/util/config.py`

**規約・設計の経緯（優先度: 低）**

- 読む: `workflow/sandbox/CONSIDERATIONS.md` — トークンをコンテナに触れさせない設計など、壊してはいけない前提

## 触るファイル

### 新規

- `workflow/sandbox/orchestrator/config.example.toml` — `[models]`（default `sonnet`）、`[limits]`（`max_turns`・`max_issues_per_cycle`・`agent_timeout_seconds`・`container_timeout_seconds`・`poll_interval_seconds`・`max_budget_usd`）、`[container]`（image・memory・cpus・pids_limit）、`[github]`（owner/repo/base_branch・allowed_author_associations）、`[paths]`・`[logging]`
- `workflow/sandbox/orchestrator/sandbox_config.py` — TOML 読み込み・検証、`SANDBOX_*`・`GITHUB_OWNER`/`GITHUB_REPO` 環境変数での上書き（モジュール名は概要の決定事項どおりワークフロー固有）
- `workflow/sandbox/orchestrator/tests/test_sandbox_config.py` — 見本が通ること・検証エラー・上書き順・空文字は未設定扱い

### 変更

- `workflow/sandbox/orchestrator/poller.py` — `Config.from_env()` を `sandbox_config.py` へ置き換え
- `workflow/sandbox/orchestrator/state.py` — CLI が `SANDBOX_STATE_DB_PATH` を直接読む箇所を設定経由に
- `workflow/sandbox/orchestrator/logging_setup.py` — `DEFAULT_LOG_DIR` を `[paths]`/`[logging]` から
- `workflow/sandbox/orchestrator/run_agent.py` — コンテナへ渡す `SANDBOX_MODEL` をカタログ解決後の `id` に。`run_container()` の `-e` に上限用の環境変数（`SANDBOX_MAX_BUDGET_USD` 等）を足す。`container_main()` の `"sonnet"` 既定を削除し未設定ならエラー。`ResultMessage` のセッション ID・解決後モデル ID もログへ
- `workflow/sandbox/orchestrator/.env.example` — 秘密情報（GitHub App の ID・鍵パス・installation ID、`ANTHROPIC_API_KEY`）だけに
- `workflow/sandbox/orchestrator/pyproject.toml` — `requires-python = ">=3.11"`、`py-modules` に `sandbox_config` を追加、pytest を dev 依存に（未設定なら）
- `workflow/sandbox/AGENTS.md`、`README.md`、`docs/github-app-setup.md` — セットアップ手順・`.env` の説明

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                | 理由                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| コンテナ内の `_run_agent_query()` に `max_budget_usd` と `anyio.fail_after(agent_timeout_seconds)` を付ける。値はホストから `-e SANDBOX_MAX_BUDGET_USD`・`SANDBOX_AGENT_TIMEOUT_SECONDS` で渡し、コンテナ側では必須 | Step 1: SDK にタイムアウトは無く、`asyncio.wait_for` は不可。コンテナ単位の timeout（`container_timeout_seconds`）は最後の安全網として残し、内側をそれより短くする |
| ログ 1 行（JSON）に、要求エイリアス・カタログの `id`・init の `data["model"]`・`model_usage` のキー（`canonicalModel`）・`session_id`・`num_turns`・`total_cost_usd`・`subtype`/`terminal_reason`/`is_error` を出す | Step 1: 解決後モデルは init と `model_usage` でしか取れない。`subtype="success"` でも `is_error=True` がある                                                       |
| `session_id` は init メッセージの時点で控え、タイムアウトや例外で `ResultMessage` が来なかったときは終了理由を `timeout` / `failed` として自前で記録する                                                            | Step 1: 中断時は `ResultMessage` が届かない                                                                                                                        |
| `config.toml` はホストだけが読み、コンテナには環境変数で値を渡す                                                                                                                                                    | イメージに設定ファイルを焼き込むとモデル変更のたびに再ビルドが要る                                                                                                 |
| モデルの解決（エイリアス → `id`）はホスト側で行う                                                                                                                                                                   | コンテナ側にカタログを持たせない。ログにはホストで要求した `id` とコンテナが報告した解決後 ID の両方が残る                                                         |
| `SANDBOX_MODEL` はエイリアスだけを受け、空文字は未設定とみなす。`GITHUB_OWNER`/`GITHUB_REPO` も上書き用として残す                                                                                                   | 概要の決定事項。既存 `.env` を壊さない                                                                                                                             |
| `GITHUB_APP_ID` 等の非秘密だが認証に属する値は `.env` に残す                                                                                                                                                        | 鍵パスと組で扱う値で、`get_installation_token.py` も単体で環境変数から読む                                                                                         |

- 落とし穴: orchestrator は bind mount されるので、ホストの `config.toml`（と `.env`・`data/`）はコンテナからも見える。`.dockerignore` は効かない。「コンテナ内で `config.toml` を読まない」はコードでしか守れないため、`run_agent.py` の `sandbox_config` の import はホスト側の関数内に閉じ、`container_main()` は環境変数だけを読む。

## 実行中に判明した変更

- 2026-11-14（Step 1 完了時）: SDK の上限・使用量の調査結果を「決定事項・注意点」に反映（上限の渡し方・ログ項目）。根拠は [progress/01-research-results.md](progress/01-research-results.md)。

## ルール更新ポイント

- `workflow/sandbox/AGENTS.md`: 「設定の正はホストの `config.toml`。コンテナには環境変数で渡す」の 1 行と、上書き用環境変数の一覧。

## 進め方

- **実行主体**: メインエージェント。Docker を実際に動かす確認はユーザーに依頼する（単体テストは実 API・Docker を使わない）。
- **TODO化**: 「`sandbox_config.py` + 見本 + テスト」「poller / run_agent の切替」「.env.example・ドキュメント」の 3 項目。
