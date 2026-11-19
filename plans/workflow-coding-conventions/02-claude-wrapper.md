---
type: Plan Step
status: ready
---

# Step 2: claude-wrapper — カタログを `config.toml` へ（Python 版の基準実装）

## やること

gitignore されていて見本の無い `util/models.json` をやめ、`claude-wrapper/config.toml`（`[models]`・`[providers]`・`[limits]`）から読む `util/config.py` を作る。3 スクリプト（`minimal_agent`・`todo_runner`・`todo_detail_runner`）を新ローダーへ切り替え、ターン数等の既定値も `[limits]` へ移す。この `config.py` を 03〜06 の写し元にする。

## 読むべきファイル・実行推奨Grep

**移行元の仕様を確認するため（優先度: 高）**

- 読む: `workflow/claude-wrapper/util/models.py` — 現行の検証項目（id 重複・default ちょうど 1 件・evaluation 必須）と `prompt_block()` / `normalize_model()` / `invalid_tasks_model_error()` の API
- 読む: `workflow/claude-wrapper/util/test_models.py` — 既存テストが期待する振る舞い
- 読む: `workflow/claude-wrapper/util/AGENTS.md` — `models.json` のスキーマ説明（`resolved` / `verified` / `role` の意味）
- Grep: `load_catalog|default_id|is_allowed|prompt_block` in `workflow/claude-wrapper` — 呼び出し箇所の洗い出し

**上限・ログの差し込み先を確認するため（優先度: 中）**

- 読む: `workflow/claude-wrapper/todo_runner/todo_runner.py`（`run_agent` と argparse）、`todo_detail_runner/agent.py`、`todo_detail_runner/todo_detail_runner.py`
- Step 1 の調査結果は下の決定事項に反映済み（根拠: [progress/01-research-results.md](progress/01-research-results.md)）

**規約（優先度: 中）**

- 読む: `workflow/docs/coding-conventions.md` §1・§2・§7・§8
- 読む: `workflow/_umbrella/maintenance-docs/tool-conventions.md` — `.env` と設定の読み込み順の共通ルール

## 触るファイル

### 新規

- `workflow/claude-wrapper/config.example.toml` — 規約の見本の形。エイリアスは `haiku` / `sonnet` / `opus` / `fable` と、引用キーの `"sonnet[1m]"` / `"opus[1m]"`（`[models."sonnet[1m]"]`）。各モデルに `id`・`provider`・`note`（旧 `evaluation`）・任意の `role`。`default = "haiku"`（現行どおり）。上限はスクリプトごとに `[limits.minimal_agent]`・`[limits.todo_runner]`・`[limits.todo_detail_runner]` に分け、各々 `max_turns`・`timeout_seconds`・`max_budget_usd`、todo 系は加えて `max_iterations`・`max_stagnant`（現行の既定値: minimal は `max_turns=1`、todo 系は 15）
- `workflow/claude-wrapper/util/config.py` — TOML 読み込み・検証・型付き `Config`（`models` カタログ + `limits`）。旧 `models.py` の API（`prompt_block` 等）を引き継ぐ
- `workflow/claude-wrapper/util/test_config.py` — 一時ディレクトリの TOML で検証エラーを網羅、`config.example.toml` が通ること、`config.toml` 不在時のエラー文

### 変更

- `workflow/claude-wrapper/util/models.py` / `util/test_models.py` — 削除（`config.py` / `test_config.py` に統合）
- `workflow/claude-wrapper/todo_detail_runner/todo_state.py`・`result.py` — `from util.models import` を `util.config` へ
- `workflow/claude-wrapper/todo_detail_runner/test_todo_detail_runner.py` — 読み込み時の `load_catalog()`（開発者の実カタログに依存）をやめ、一時 TOML か見本を明示パスで読む（規約 §8）
- `workflow/claude-wrapper/minimal_agent/minimal_agent.py`、`todo_runner/todo_runner.py`、`todo_detail_runner/todo_detail_runner.py`、`todo_detail_runner/agent.py`、`todo_detail_runner/prompts.py` — 新ローダーへ切替。argparse の既定値を `[limits]` から取る。`--model` はエイリアスを受け、SDK にはカタログの `id` を渡す。上限（`max_turns`・`max_budget_usd`・`anyio.fail_after`）を付け、結果ログに決定事項の項目を出す。3 スクリプトの `run_agent` は claude-wrapper 内の共通関数（例: `util/agent_run.py`）にまとめてよい
- `workflow/claude-wrapper/pyproject.toml` — `requires-python = ">=3.11"`
- `workflow/claude-wrapper/AGENTS.md`、`util/AGENTS.md`、`minimal_agent/AGENTS.md`（`models.json` へのリンク）、`todo_runner/AGENTS.md`、`todo_detail_runner/AGENTS.md` — `models.json` の記述を `config.toml` に置き換え、セットアップ手順を追加
- `workflow/claude-wrapper/todo_*/todo.json.example` — `model` の例がカタログのエイリアスになっているか確認（必要なら修正）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                | 理由                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 上限は `max_turns` と `max_budget_usd` を SDK に渡し、壁時計タイムアウトは `anyio.fail_after(timeout_seconds)` で包む。`asyncio.wait_for` は使わない                                                                | Step 1: SDK にタイムアウトは無い。`asyncio` のキャンセルでは子プロセスの段階的停止（SIGTERM→SIGKILL）が飛ぶことがある |
| ログ 1 行（JSON）に、要求エイリアス・カタログの `id`・init の `data["model"]`・`model_usage` のキー（`canonicalModel`）・`session_id`・`num_turns`・`total_cost_usd`・`subtype`/`terminal_reason`/`is_error` を出す | Step 1: 解決後モデルは init と `model_usage` でしか取れない。`subtype="success"` でも `is_error=True` がある          |
| `session_id` は init メッセージの時点で控え、タイムアウトや例外で `ResultMessage` が来なかったときは終了理由を `timeout` / `failed` として自前で記録する                                                            | Step 1: 中断時は `ResultMessage` が届かない                                                                           |
| 検証は旧 `models.py` と同等以上（未知キー・型違い・`default` の指し先無し・`*_key`/`*_token`/`*_secret` キー）をエラーにし、メッセージに絶対パスとキー名を入れる                                                    | 規約 §1-6・§2                                                                                                         |
| `todo.json` の `task.model` とプロンプトに渡すカタログはエイリアス（キー名）。SDK に渡すのは `id`                                                                                                                   | 規約 §1-4・§5。エージェントに実 ID を書かせない                                                                       |
| 旧 `resolved` は `id` に統合し、`verified` は持ち越さない。`id` には現行で SDK に渡している値をそのまま書く（CLI のエイリアスか固定 ID かは手元の `models.json` を見て移す）                                        | 振る舞いを変えない。実際の解決結果はログに出す（§7）                                                                  |
| `[1m]` 付きのエイリアスもカタログに残す                                                                                                                                                                             | 既存テストが許可しており、既存 `todo.json` で使われている可能性がある                                                 |
| `config.toml` 不在時は `cp config.example.toml config.toml` を案内して終了（見本へフォールバックしない）                                                                                                            | 規約 §1-7                                                                                                             |
| `.gitignore` の `*.json` は `todo.json` 用として残す                                                                                                                                                                | `config.toml` はルート `.gitignore` で無視済み。`*.example` は `.json` で終わらない                                   |

- 落とし穴: `util/` は `sys.path` 操作で import されている（`from util.models import ...`）。import パスの変更漏れに注意。
- 落とし穴: 手元に旧 `util/models.json` があっても読まれなくなる。AGENTS.md に移行手順（値の移し替え）を 1 行書く。

## 実行中に判明した変更

- 2026-11-14（Step 1 完了時）: SDK の上限・使用量の調査結果を「決定事項・注意点」に反映（上限の付け方・タイムアウトの包み方・ログ項目）。根拠は [progress/01-research-results.md](progress/01-research-results.md)。

## ルール更新ポイント

- `workflow/claude-wrapper/util/AGENTS.md`: カタログのスキーマ説明を削除し、「キーの説明は `config.example.toml` のコメントが正」と書く（規約 §9 の二重記述禁止）。

## 進め方

- **実行主体**: メインエージェント（基準実装なので委任しない）。
- **TODO化**: 「`config.py` + テスト + 見本」「3 スクリプトの切替 + ログ」「AGENTS.md 更新」の 3 項目。完了条件は、既存の流儀（各 AGENTS.md の `python -m unittest`）どおり `util/` と `todo_detail_runner/` で `uv run --project workflow/claude-wrapper python -m unittest` が通ること。アンブレラの pytest（`--import-mode=importlib`）はテストディレクトリを `sys.path` に入れず平置き import が収集で落ちるため、完了条件に使わない（テストの import 方式の変更は本プランの対象外）。
