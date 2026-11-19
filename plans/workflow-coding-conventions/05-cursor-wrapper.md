---
type: Plan Step
status: ready
---

# Step 5: cursor-wrapper — モデル直書きをカタログへ、プロンプト分離

## やること

`main.py` の `REQUESTED_MODEL` / `MODEL_ALIASES` / `CURSOR_MODEL` フォールバックを `cursor-wrapper/config.toml` のカタログへ移す。`resolve_model()` の Grok 専用分岐（variant 選択）をカタログの記述で表せる形にし、解決後の ID をログに出す。`PLANNER_INSTRUCTIONS` 等のプロンプトを `cursor_prompts.py` へ分ける。

## 読むべきファイル・実行推奨Grep

**モデル解決の現行ロジックを確認するため（優先度: 高）**

- 読む: `workflow/cursor-wrapper/main.py` — `resolve_model()`（`Cursor.models.list` と variant の `params`）、`PlannerRegistry`（サブエージェントの `model` 検証）、`main()` の argparse
- Step 1 の調査結果は下の決定事項に反映済み（根拠: [progress/01-research-results.md](progress/01-research-results.md)）
- 参照: `cursor-sdk-use` スキル — `ModelSelection` の `params` の形

**写し元（優先度: 高）**

- 読む: Step 2 の `workflow/claude-wrapper/util/config.py`

## 触るファイル

### 新規

- `workflow/cursor-wrapper/config.example.toml` — `[models.<alias>]` に `id`（要求 ID）と任意の `variant`（variant を選ぶパラメータ）、`note`。`[limits]` に `max_turns`・`timeout_seconds`・`max_total_tokens`
- `workflow/cursor-wrapper/cursor_config.py` — 読み込み・検証（モジュール名は概要の決定事項どおりワークフロー固有）
- `workflow/cursor-wrapper/cursor_prompts.py` — `PLANNER_INSTRUCTIONS`・`DEFAULT_PROMPT` 等
- `workflow/cursor-wrapper/test_cursor_config.py` — 見本が通ること・検証エラー。`resolve_model()` はモデル一覧をスタブで渡してテスト

### 変更

- `workflow/cursor-wrapper/main.py` — 直書き定数・`CURSOR_MODEL` 既定を削除。`--model` はエイリアス、解決順は CLI → `CURSOR_MODEL` → `default`。解決後の ID と variant を出力
- `workflow/cursor-wrapper/pyproject.toml` — `requires-python = ">=3.11"`、`py-modules` に `cursor_config`・`cursor_prompts` を追加
- `workflow/cursor-wrapper/AGENTS.md` — セットアップ・`--model` の説明

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                                                                | 理由                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[limits]` は `max_turns`・`timeout_seconds`・`max_total_tokens`。どれも SDK に指定口が無いので、`run.messages()` を読むループで経過時間・ターン数（`type=="usage"` の回数）・`run.usage` の累計を監視し、超えたら `run.cancel()` する                              | Step 1: Cursor SDK にターン数・タイムアウト・予算のオプションは無い。asyncio を止めてもサーバー側の run は止まらないので `cancel()` を明示する（終了済み run への `cancel()` は例外になるので try で包む） |
| ログは run ごとに 1 件: 要求エイリアス・解決後 ID と variant・`result.model`・`agent_id`・`result.id`・ターン数・`result.usage`（None は 0 にしない）・`duration_ms`・`status`・自前の終了理由。USD は `agent.get_usage()` をベストエフォートで（403・None を許容） | Step 1: エイリアスの実モデル解決を SDK が返すか不明。コストは実行後にしか確定しない                                                                                                                        |
| `getattr(result, 'error')` は `RunResult` に無く常に None なので削除し、エラーは `CursorSdkError` 側から取る                                                                                                                                                        | Step 1 で判明した現行コードの誤り                                                                                                                                                                          |
| `--model` と `CURSOR_MODEL` はエイリアスだけを受ける（空文字は未設定）。既存 `.env` の `CURSOR_MODEL=grok-4.5-medium` 等は起動時エラーになるので AGENTS.md に移行手順を書く                                                                                         | 概要の決定事項                                                                                                                                                                                             |
| 旧 `MODEL_ALIASES`（Cursor 側の slug 改名の吸収）は、カタログの `id` を新 slug に直すことで不要にする                                                                                                                                                               | 改名はカタログ 1 か所の修正で済ませる（規約 §1-4）                                                                                                                                                         |
| プランナーが選ぶサブエージェントの `model` は、従来どおり SDK の利用可能モデル一覧で検証する（カタログ外も可）                                                                                                                                                      | プランナーへの提示は実行時の一覧で、カタログはメインの実行モデル用。ここを変えるとプランナーの選択肢が狭まる。§1-4 の例外として AGENTS.md に明記                                                           |

- 落とし穴: `resolve_model()` は Grok の variant を名前の部分一致で探している。汎用化するときは、variant 指定が無いモデルで従来どおり `str` を返すこと。

## 実行中に判明した変更

- 2026-11-14（Step 1 完了時）: SDK の上限・使用量の調査結果を「決定事項・注意点」に反映（上限の自前監視・ログ項目・現行コードの誤り）。根拠は [progress/01-research-results.md](progress/01-research-results.md)。

## ルール更新ポイント

- `workflow/cursor-wrapper/AGENTS.md`: プランナーのサブエージェント用モデルはカタログ外（SDK の一覧）から選ぶ、という例外を 1 行。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 「config + 見本 + テスト」「main.py の切替・prompts 分離」の 2 項目。`uv run --project workflow/cursor-wrapper python -m pytest workflow/cursor-wrapper/test_cursor_config.py` が通ることを完了条件にする。
