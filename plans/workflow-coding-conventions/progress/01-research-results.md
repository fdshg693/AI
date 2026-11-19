# Step 1 調査: 詳細結果

## このファイルの位置づけ

[../01-research-sdk-limits.md](../01-research-sdk-limits.md) の実行で得た SDK ごとの詳細（根拠のファイル:行・注意点）。後続ステップ（02〜08）の決定事項・注意点には反映済みなので、実装時に原則読み直す必要はない。根拠を確かめたいときの参照元。

調査は 2026-11-14、SDK ごとに 1 体のサブエージェントへ委任し（各 SDK のスキル + インストール済みソース / 型定義）、採否はメインで判断した。ソースの行番号は当日のインストール版のもの。

## SDK ごとの結果

### Claude Agent SDK（Python `claude-agent-sdk` 0.2.134 — claude-wrapper・issue-agent・sandbox）

参照: https://code.claude.com/docs/en/agent-sdk/agent-loop 、cost-tracking 、hosting 。ソースは `.venv/.../claude_agent_sdk/`。

| 観点         | 結果                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ターン数     | `ClaudeAgentOptions.max_turns`（`types.py:1837`）。到達時は例外ではなく `ResultMessage(subtype="error_max_turns")`、`terminal_reason="max_turns"`                                                                                                                                                                                                                                                        |
| タイムアウト | SDK に無し（hosting「No top-level session timeout」）。`transport.close()` は stdin close → 5s → SIGTERM → 5s → SIGKILL を anyio shield 下で行うが、`asyncio.wait_for` / `task.cancel()` では shield が効かず段階が飛ぶことがある（`_internal/transport/subprocess_cli.py:46-60, 924-1000`）。**`anyio.fail_after()`** で包むか、`ClaudeSDKClient` なら `interrupt()`（`client.py:317`）→ `disconnect()` |
| 予算         | `max_budget_usd`（`types.py:1843-1847`）。超過で `subtype="error_max_budget_usd"`。判定は応答後なので 1 応答分＋実行中サブエージェント分はみ出しうる。トークンのハード上限は無し（`task_budget` はモデルへの通知だけのベータ）                                                                                                                                                                           |
| 取得値       | 解決後モデル: `SystemMessage(subtype="init").data["model"]`、`AssistantMessage.model`、`ResultMessage.model_usage` のキー（各値の `canonicalModel`）。`session_id`・`num_turns`・`total_cost_usd`（None あり）・`usage`（メインループのみ。全体は `model_usage`）。終了理由: `subtype`・`is_error`（`success` でも True のことがある）・`stop_reason`・`terminal_reason`・`api_error_status`・`errors`   |

現行コード: `max_turns` は全箇所で指定済み（`todo_runner.py:193`、`todo_detail_runner/agent.py:74`、`minimal_agent.py:35`、`issue_agent/dispatch.py:155`、`sandbox/orchestrator/run_agent.py:345`）。`max_budget_usd`・時間制御は未使用。ログは `subtype`・`num_turns`・`total_cost_usd` まで。init の `model`・`model_usage`・`terminal_reason` は誰も出していない。`session_id` は issue-agent だけ。外側のタイムアウトは issue-agent（`check.py:85` の `subprocess` timeout）と sandbox（コンテナ単位）にある。

### Cursor Python SDK（`cursor-sdk` 1.0.27 — cursor-wrapper）

参照: https://cursor.com/docs/sdk/python 。ソースは `.venv/.../cursor_sdk/`。

| 観点         | 結果                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ターン数     | 不可（`AgentOptions`・`SendOptions` に無し、`types.py:1140-1155, 1217-1225`）。`run.messages()` の `type=="usage"` か `on_delta` の `turn-ended` を数え、超えたら `run.cancel()`                                                                                                                                                                                                                                                              |
| タイムアウト | 不可。client の `timeout`/`stream_timeout` は httpx の通信単位（`_connect.py:28-29`）。`run.cancel()`（`_run.py:120`）で status `cancelled`。**asyncio を止めてもサーバー側 run は止まらない**ので `cancel()` を必ず呼ぶ。終了済み run への `cancel()` は `UnsupportedRunOperationError`                                                                                                                                                      |
| 予算         | 不可。トークンは `run.usage` の累計を監視して `cancel()`。USD は `agent.get_usage(run_id=...)` のみで、実行後に確定・遅延あり、local では 403 `feature_unavailable` のことがある                                                                                                                                                                                                                                                              |
| 取得値       | モデル: `result.model`（`ModelSelection`）・ストリームの `system` メッセージ。エイリアスの実モデルへの解決を返すかは未記載 → 要求エイリアス・クライアント解決 ID・`result.model` を並べてログ。ID: `agent.agent_id`・`result.id`（`run_id` は非推奨）。ターン数フィールドは無し。`result.usage`（None は 0 扱いしない）、`result.duration_ms`、`result.status`（finished/error/cancelled/expired）。エラー文は例外側（`CursorSdkError.code`） |

現行コード（`main.py`）: `send().wait()` のみでタイムアウト・cancel・上限なし（`:315-324, :362-371`）。`getattr(result, 'error')` は `RunResult` に存在せず常に None（`:326-329, :373-376`）。ID・モデル・usage は未使用。

### Codex Python SDK（`openai-codex` — codex-wrapper）

バージョン未固定（codex-wrapper に pyproject 無し、uv.lock・.venv にも無し）。GitHub `openai/codex` main（2026-11-14）の `sdk/python/src/openai_codex/` で確認。PyPI 最新 0.169.0、手元の codex-cli 0.166.0。

| 観点         | 結果                                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ターン数     | 不可。SDK の turn はプロンプト 1 回分で、内部のツール反復の上限は無い（`api.py:135-173, 581-664`）。`turn().stream()` で `item/completed` を数えて `handle.interrupt()`（`api.py:818`）                                                                                                                                                                                                                  |
| タイムアウト | 不可（`run()` は無期限待ち、`_run.py:67-85`。公式 FAQ も stream 側で組むよう案内）。`asyncio.wait_for(handle.run(), t)` → `handle.interrupt()` で `status=interrupted`。`AsyncTurnHandle.stream` は `asyncio.to_thread` で待つ（`api.py:884`）のでワーカースレッドはすぐ止まらない → 最後に `Codex.close()` / `with` 脱出で app-server を terminate→kill（`client.py:283-297`）                          |
| 予算         | USD 不可。トークンはプロトコルの `thread/goal/set` の `tokenBudget` があるが SDK 非公開（`client.py:549-567`）→ 使わない。`ThreadTokenUsageUpdatedNotification` の `total_tokens` を監視して `interrupt()`                                                                                                                                                                                               |
| 取得値       | `thread.id`、`result.id`（turn）。解決後モデル: `thread_start` 応答の `.model` は SDK が捨てる → `thread.read().thread.model`、切り替えは `ModelReroutedNotification`。`result.usage`（`last`/`total`、input/cached_input/output/reasoning_output/total）。コストは `account/usage/read` の推定値だけ（非公開 API）→ 記録しない。`result.status` は completed/interrupted、failed は `RuntimeError` 送出 |

現行コード（`main.py`）: `thread_start(model=MODEL, cwd, sandbox=read_only)` + `thread.run()` + `final_response` の print のみ。

### Cline SDK（`@cline/sdk` 0.0.65 — cline-wrapper）

参照: https://docs.cline.bot/sdk/reference/agent 、https://docs.cline.bot/sdk/guides/going-to-production （Cost Control）。型は `@cline/shared/dist/agent.d.ts`（以下 S）、`@cline/agents/dist/agent-runtime.d.ts`（R）。

| 観点         | 結果                                                                                                                                                                                                                                                                                   |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ターン数     | `new Agent({ maxIterations })`（S:293）。到達時は例外にならず `status:"failed"`・`error.message` が `Agent runtime exceeded maxIterations (N)` → 文言で判別                                                                                                                            |
| タイムアウト | 不可（`run()` は signal を受けない、R:52）。`setTimeout(() => agent.abort("timeout"), ms)`（R:54）→ `status:"aborted"`、`error` は undefined（理由は自前変数か `snapshot().lastError`）。`abort()` は実行中以外は無効。ツール内部はツールが `context.signal` を見ないと止まらない      |
| 予算         | 不可。`usage-updated` イベント（S:361-363）で `usage.totalCost`・トークン累計を見て `abort("budget")`。1 ターン分超えうる。`totalCost` は省略可（S:63）。ガイドの `maxTokensPerTurn` は 0.0.65 の `Agent` 型に無い                                                                     |
| 取得値       | `result.iterations`・`status`（completed/aborted/failed）・`usage`（各トークン + `totalCost?`、run ごとに 0 から）・`agentId`・`runId`。sessionId は自動採番されない（自前で渡す）。**解決後モデル ID は取れない**（`messages[].modelInfo` は設定値の写し）→ 指定した `modelId` を記録 |

現行コード: `lib/agent-runner.mjs:34-41` は `maxIterations` まで、abort・`usage-updated` 未使用。`repo-search.mjs` は `status`・`iterations`・`usage` を stderr に出す（`:164, 185-186, 218-222`）。`main.mjs:74-77` は `status` のみ。

### GitHub Copilot SDK（`@github/copilot-sdk` 1.0.11 / `@github/copilot` 1.0.81 — copilot-wrapper）

参照: https://docs.github.com/en/copilot/how-tos/copilot-sdk/features/agent-loop 、session-limits 、usage-and-billing 。型は `@github/copilot-sdk/dist`（以下 D）。

| 観点         | 結果                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ターン数     | 不可。`assistant.turn_start` を数えて `session.abort()`（1 ターン分超えうる）                                                                                                                                                                                                                                                                                                                                                                                                    |
| タイムアウト | `sendAndWait(opts, timeout)`（既定 60000ms、D/session.d.ts:149-163）は**待つのをやめるだけ**（"does not abort in-flight agent work"）。catch で `session.abort()`（:271-290）→ `disconnect()`。`session.idle.data.aborted` で停止を確認                                                                                                                                                                                                                                          |
| 予算         | `createSession({ sessionLimits: { maxAiCredits } })`（experimental、ソフト上限、D/types.d.ts:2005-2009）。BYOK で効くかは未記載。USD・トークン・premium request は不可 → `assistant.usage` のトークン累計で `abort()`                                                                                                                                                                                                                                                            |
| 取得値       | `session.sessionId`。モデル: `assistant.usage.data.model`・`assistant.turn_start.data.model`・`session.model_change`・`session.rpc.usage.getMetrics().currentModel`。トークン: `assistant.usage`（input/output/cacheRead/cacheWrite/reasoning、`finishReason`）、累計は `getMetrics()`（`totalPremiumRequestCost`・`totalNanoAiu`・`modelMetrics`）。USD は出ない。終了理由は `finishReason`・`idle.aborted`・`abort.reason`・`session.error`・`session.shutdown` を組み合わせる |

現行コード: `main.mjs:183-195` は `sessionLimits` なし。`:198-214` は `session.idle`/`session.error` を待つ自作 Promise で時間上限なし。`sessionId`・`assistant.usage`・`getMetrics()` は未使用。

## 検討したが見送った選択肢

- **Codex の `thread/goal/set` の `tokenBudget`、`account/usage/read` のコスト推定** — SDK 非公開の `_client.request` 経由になり、SDK 更新で壊れうる。トークン監視 + `interrupt()` で代替し、コストは記録しない。
- **Copilot の `sessionLimits.maxAiCredits`** — experimental で BYOK での効き方が未記載。copilot-wrapper は BYOK が主なので採らない。
- **Cursor の `get_usage()` を予算の監視に使う** — 実行後にしか確定せず遅延・403 がある。ログ用のベストエフォートに留める。
- **Claude Agent SDK を `asyncio.wait_for` で包む** — 子プロセスの段階的停止が飛ぶ。`anyio.fail_after` を使う。
- **予算（USD）を上限として全ワークフローで必須にする** — USD を返すのは Claude と Cline（プロバイダ依存）だけ。他はトークン上限で代替する。

## プラン本文への反映

- [../02-claude-wrapper.md](../02-claude-wrapper.md)・[../03-issue-agent.md](../03-issue-agent.md)・[../04-sandbox.md](../04-sandbox.md): `max_budget_usd` を付ける、`anyio.fail_after`、ログ項目（init の model・`model_usage`・`terminal_reason`）、タイムアウト時は `ResultMessage` が来ない前提
- [../05-cursor-wrapper.md](../05-cursor-wrapper.md): 上限 3 種は自前監視 + `run.cancel()`、`[limits]` のキー、`getattr(result,'error')` の誤り
- [../06-codex-wrapper.md](../06-codex-wrapper.md): `turn().stream()` 監視 + `interrupt()` + `close()`、コストは記録しない
- [../07-cline-wrapper.md](../07-cline-wrapper.md): `abort()` によるタイムアウト・予算、`maxIterations` 到達の判別、モデル ID は指定値を記録
- [../08-copilot-wrapper.md](../08-copilot-wrapper.md): `abort()` → `disconnect()`、ターン数は `turn_start` で数える、`sessionLimits` は使わない
- [../09-conventions-doc.md](../09-conventions-doc.md): §3 に「SDK が持たない上限は呼び出し側で監視して中断する」と USD 上限の可否を注記
