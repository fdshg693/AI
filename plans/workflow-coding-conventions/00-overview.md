---
type: Plan
status: implementing-in-progress
---

## 実装ステータス

- [x] [01-research-sdk-limits.md](01-research-sdk-limits.md) — 各 SDK の上限・予算・解決後モデル ID・使用量の取り方を調査
- [ ] [02-claude-wrapper.md](02-claude-wrapper.md) — `util/models.json` を `config.toml` へ移し、Python 版ローダーの基準実装にする
- [ ] [03-issue-agent.md](03-issue-agent.md) — `dispatch.py` の直書きエイリアス・上限を `config.toml` へ
- [ ] [04-sandbox.md](04-sandbox.md) — `poller.py` / `run_agent.py` の既定モデル・上限を `config.toml` へ
- [ ] [05-cursor-wrapper.md](05-cursor-wrapper.md) — `REQUESTED_MODEL` / `MODEL_ALIASES` をカタログへ、プロンプト分離
- [ ] [06-codex-wrapper.md](06-codex-wrapper.md) — `MODEL` 直書きを `config.toml` へ
- [ ] [07-cline-wrapper.md](07-cline-wrapper.md) — `lib/config.mjs` の既定値を `config.toml` へ、Node 版ローダーの基準実装にする
- [ ] [08-copilot-wrapper.md](08-copilot-wrapper.md) — `.env` のモデル・プロバイダ・ベース URL を `config.toml` へ
- [ ] [09-conventions-doc.md](09-conventions-doc.md) — 規約の移行表と README を実態に合わせる

# workflow/ をコーディング規約に揃える - 概要

対象規約: [workflow/docs/coding-conventions.md](../../workflow/docs/coding-conventions.md)（以下「規約」）。2026-11-14 時点の移行表に載っている食い違いを、ワークフローごとに解消する。

## 要件

- 各ワークフロー（`schedule/ai-schedule` を除く）が `config.toml` を 1 つ持ち、Git には `config.example.toml` だけを置く（規約 §1）。
- コードからモデル ID・プロバイダ・ベース URL・既定モデルの直書きを無くし、カタログのエイリアスで指す（規約 §1）。
- 設定は起動時に検証して早く落とす。`config.example.toml` がそのまま検証を通ることをテストする（規約 §2・§8）。
- エージェント呼び出しにターン数・タイムアウト（SDK が対応していれば予算）の上限を `[limits]` から付け、実行ごとに解決後のモデル ID・セッション ID・ターン数・コストをログに残す（規約 §3・§7）。

## 実装ステップ

1. [01-research-sdk-limits.md](01-research-sdk-limits.md) — 5 つの SDK について、上限・予算の指定方法と、解決後モデル ID・使用量の取得方法を調査（後続すべての前提）
2. [02-claude-wrapper.md](02-claude-wrapper.md) — Python 版 `config.py` の基準実装（03〜06 はこれを写す）
3. [03-issue-agent.md](03-issue-agent.md)
4. [04-sandbox.md](04-sandbox.md)
5. [05-cursor-wrapper.md](05-cursor-wrapper.md)
6. [06-codex-wrapper.md](06-codex-wrapper.md)
7. [07-cline-wrapper.md](07-cline-wrapper.md) — Node 版 `lib/config.mjs` の基準実装（08 はこれを写す）
8. [08-copilot-wrapper.md](08-copilot-wrapper.md)
9. [09-conventions-doc.md](09-conventions-doc.md)

02 の後は 03〜06 を任意の順で進めてよい。07 → 08 は順序固定。09 は最後。

## 主要な決定事項

| 決定                                                                                                                                                                                                                                                      | 理由                                                                                                                                                                                                                                                                           |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ローダーはワークフロー間で共有せず、各ワークフローに `config.py` / `lib/config.mjs` を 1 つずつ置く（基準実装を写す）                                                                                                                                     | ワークフローは `uv run --project <name>` で単体でも動く前提（[AGENTS.md](../../workflow/AGENTS.md)）。共有パッケージを作ると単体 clone が壊れる                                                                                                                                |
| Python は `tomllib` を使うため、`requires-python` を `>=3.11` に上げる（claude-wrapper・cursor-wrapper・sandbox/orchestrator）                                                                                                                            | 規約 §1「実装の目安」。手元は 3.14 で、3.10 を守る理由が無い                                                                                                                                                                                                                   |
| Node は `smol-toml` を依存に足す（pnpm、アンブレラの workspace）                                                                                                                                                                                          | 規約 §1「実装の目安」                                                                                                                                                                                                                                                          |
| `config.toml` の置き場所は「そのワークフローの uv / pnpm プロジェクトのディレクトリ直下」（sandbox は `sandbox/orchestrator/config.toml`）                                                                                                                | sandbox は `.env` も `pyproject.toml` も `orchestrator/` にあり、読むのも `poller.py` だけ。規約の「ワークフローのディレクトリ直下」をこの意味に明確化する（Step 9）                                                                                                           |
| 既存の外部入力で使われているエイリアス名（`haiku` / `sonnet` / `opus` / `fable`）は見本のカタログでもそのまま使う                                                                                                                                         | GitHub ISSUE の `model:` ラベルや既存 `todo.json` の `model` を壊さない                                                                                                                                                                                                        |
| 既存の環境変数名（`ISSUE_AGENT_*`・`SANDBOX_*`・`CURSOR_MODEL`・`COPILOT_BYOK_*` の非秘密分）は「一時的な上書き」として残し、既定値だけを `config.toml` に移す                                                                                            | 規約の解決順（CLI → 環境変数 → `config.toml`）に合う。ai-schedule のジョブ定義など既存の呼び出し側を壊さない                                                                                                                                                                   |
| モデル・プロバイダ・上限以外の非秘密設定（owner/repo・ラベル・パス・ログ等）も `config.toml` に寄せる                                                                                                                                                     | 規約 frontmatter の「non-secret run settings live in one config file」。設定の置き場所を 1 か所にする                                                                                                                                                                          |
| 新設する Python のトップレベルモジュールは、ワークフロー固有の名前にする（`cursor_config.py`・`cursor_prompts.py`・`sandbox_config.py`・`codex_config.py`）。パッケージ内に置くもの（`claude-wrapper/util/config.py`・`issue_agent/config.py`）はそのまま | アンブレラの共有 venv では setuptools の editable finder がモジュール名で引くため、素の `config` / `prompts` が複数あると衝突する（`claude-wrapper/todo_detail_runner/prompts.py` とも）。ルートからの `pytest --import-mode=importlib` でも `sys.modules` が 1 つしか持てない |
| 上書き用の環境変数は、空文字を「未設定」とみなす                                                                                                                                                                                                          | 既存ユーザーの `.env` は旧 `.env.example` を写したもので `SANDBOX_MODEL=` のような空行を含む。現行コード（`_env_or_default`・`default_env`・`orUndefined`）の意味を引き継ぐ。tool-conventions 規則 1（空文字も既存値が勝つ）との差は Step 9 で規約に明記する                   |
| モデルを指す環境変数（`SANDBOX_MODEL`・`CURSOR_MODEL`・`COPILOT_BYOK_MODEL` 等）と `--model` はエイリアスだけを受ける。カタログに無い値は、エイリアス一覧と「実 ID はカタログの `id` に書く」移行案内を出して起動時に止める                               | 規約 §1-4・§2。実 ID の直指定を残すと直書きの抜け道になる。既存 `.env` の実 ID（`grok-4.5-medium`・`llama3` 等）は壊れるので、各 AGENTS.md に移行手順を書く                                                                                                                    |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `workflow/claude-wrapper/config.example.toml`、`util/config.py`、`util/test_config.py`
- `workflow/schedule/issue-agent/config.example.toml`、`tests/test_config_example.py`（または既存 `tests/test_config.py` に追記）
- `workflow/sandbox/orchestrator/config.example.toml`、`sandbox_config.py`、`tests/test_sandbox_config.py`
- `workflow/cursor-wrapper/config.example.toml`、`cursor_config.py`、`cursor_prompts.py`、`test_cursor_config.py`
- `workflow/codex-wrapper/config.example.toml`、`codex_config.py`、`test_codex_config.py`
- `workflow/cline-wrapper/config.example.toml`、`test-config.mjs`
- `workflow/copilot-wrapper/config.example.toml`、`test-config.mjs`

### 変更

- `workflow/claude-wrapper/`: `util/models.py`（削除して `util/config.py` へ統合）、`util/test_models.py`、`todo_runner/todo_runner.py`、`todo_detail_runner/*.py`（`todo_state.py`・`result.py`・`test_todo_detail_runner.py` を含む）、`minimal_agent/minimal_agent.py`、`pyproject.toml`、各 `AGENTS.md`（`minimal_agent/AGENTS.md` を含む）
- `workflow/schedule/issue-agent/`: `issue_agent/config.py`、`dispatch.py`、`worker.py`、`check.py`、`worktree.py`、`attempt_store.py`、`.env.example`、`AGENTS.md`、`README.md`、`tests/test_dispatch.py`、`tests/test_config.py`、`tests/test_worker.py`
- `workflow/sandbox/`: `orchestrator/poller.py`、`run_agent.py`、`state.py`、`logging_setup.py`、`.env.example`、`pyproject.toml`、`AGENTS.md`、`README.md`、`docs/github-app-setup.md`
- `workflow/cursor-wrapper/`: `main.py`、`pyproject.toml`、`AGENTS.md`
- `workflow/codex-wrapper/`: `main.py`、`AGENTS.md`
- `workflow/cline-wrapper/`: `lib/config.mjs`、`lib/agent-runner.mjs`、`main.mjs`、`repo-search.mjs`、`package.json`、`AGENTS.md`、`NEXT.md`
- `workflow/copilot-wrapper/`: `lib/config.mjs`、`main.mjs`、`.env.example`、`package.json`、`AGENTS.md`
- `workflow/docs/coding-conventions.md`、`workflow/README.md`
- アンブレラ: `pnpm-lock.yaml`（smol-toml 追加）、`uv.lock`（requires-python 変更があれば。issue-agent が既に `>=3.11` なので変わらない可能性が高い）、`registry/local-configs.yaml`（各ステップで `config.toml` / `config.example.toml` の組を追加）

## ルール更新ポイント

- `workflow/docs/coding-conventions.md`（Step 9）: 「既存コードの移行」表を実態に合わせて更新（完了した行を削除、残りがあれば残す）。§1 の置き場所を「uv / pnpm プロジェクトのディレクトリ直下」に明確化。調査（Step 1）で SDK ごとに付けられない上限があれば §3 に注記。
- 各ワークフローの `AGENTS.md`（各ステップ）: セットアップに `cp config.example.toml config.toml` を追加、モデル指定の説明をカタログのエイリアス前提に書き換え（規約 §9）。
- アンブレラの `registry/local-configs.yaml`（各ステップ）: そのステップで作る `config.toml` / `config.example.toml` の組を `local_configs` に追加する（[repo-layout](../../maintenance/docs/repo-layout.md) の「ローカル設定ファイル」）。見本が追跡済みであることを検査されるので、見本をコミットするのと同じアンブレラ側コミットで足す。

## 進め方

- **TODO化**: ステップ一覧の各項目を 1 TODO にする。各ステップの「TODO化」に挙げた小項目が 1 コミット（`workflow` サブモジュール内コミット → アンブレラのポインタ更新の 2 段階。`committing` スキルを使う）。
- **Step 2 の前提**: 規約本体（未追跡の `workflow/docs/`）と `workflow/.gitignore`・`workflow/README.md` の変更を先にコミットしておく（Step 9 が追跡済みの規約を編集する形にするため）。
- **着手前**: 本プランのレビューをサブエージェントに 1 回依頼し、反映後に `snapshot/` を取る（[plan-writing.md](../guides/plan-writing.md#プランレビューサブエージェントに1回依頼する必須)）。
