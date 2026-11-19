---
type: Plan Step
status: planning-breakdown
---

# Step 3: schedule/issue-agent — 直書きエイリアス・上限を `config.toml` へ

## やること

`dispatch.py` の `DEFAULT_MODEL_ALIAS` / `KNOWN_MODEL_ALIASES` / `DEFAULT_MAX_TURNS` と、`config.py` の既定値（owner/repo・ラベル・上限・パス）を `schedule/issue-agent/config.toml` へ移す。`model:` ラベルはカタログのエイリアスで検証し、SDK にはカタログの `id` を渡す。

## 読むべきファイル・実行推奨Grep

**現行の設定経路を確認するため（優先度: 高）**

- 読む: `workflow/schedule/issue-agent/issue_agent/config.py` — pydantic の `Config.from_env()`。新ローダーもこの `Config` 型を返す形に寄せる
- 読む: `workflow/schedule/issue-agent/issue_agent/dispatch.py` — `resolve_model_label()`・`_max_turns()`・`_run_claude_code_query()`
- 読む: `workflow/schedule/issue-agent/issue_agent/worker.py` / `check.py` — `Config` と `dispatch` の使われ方、ワーカーのタイムアウト
- Grep: `os.environ` in `workflow/schedule/issue-agent` — 設定を直接読んでいる箇所（`worktree.py` の `ISSUE_AGENT_WORKTREE_ROOT`、`attempt_store.py` の DB パス）

**写し元（優先度: 高）**

- 読む: Step 2 で作った `workflow/claude-wrapper/util/config.py`

**呼び出し側を壊さないため（優先度: 中）**

- 読む: `workflow/schedule/ai-schedule/config/jobs.example.yaml` — issue-agent を起動するジョブが環境変数を渡しているか
- 読む: `workflow/schedule/issue-agent/tests/test_dispatch.py`、`tests/test_config.py`、`tests/test_worker.py`

## 触るファイル

### 新規

- `workflow/schedule/issue-agent/config.example.toml` — `[models]`（`haiku`/`sonnet`/`opus`/`fable`、default `sonnet`）、`[limits]`（`max_turns`・`worker_timeout_seconds`・`max_issues_per_cycle`・`max_budget_usd`）、`[github]`（owner/repo・ラベル・allowed_logins）、`[paths]`（state_db・log_dir・worktree_root）

### 変更

- `workflow/schedule/issue-agent/issue_agent/config.py` — TOML を読み、環境変数 `ISSUE_AGENT_*` を上書きとして重ねる。モデルカタログを持つ。`extra="forbid"` で未知キーを拒否
- `workflow/schedule/issue-agent/issue_agent/dispatch.py` — 直書き定数を削除し、`Config` からカタログ・上限を受け取る。`ResultMessage` のコスト・解決後モデル ID をログへ
- `workflow/schedule/issue-agent/issue_agent/worker.py`、`check.py`、`worktree.py`、`attempt_store.py` — `Config` 経由に統一
- `workflow/schedule/issue-agent/.env.example` — 秘密情報（`ANTHROPIC_API_KEY`）だけにし、上書き用の環境変数は AGENTS.md へ説明を移す
- `workflow/schedule/issue-agent/tests/test_config.py`、`test_dispatch.py`、`test_worker.py` — 一時 TOML を使う形へ。`config.example.toml` の読み込みテストを追加
- `workflow/schedule/issue-agent/AGENTS.md`、`README.md` — セットアップ手順・`model:` ラベルの説明

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| --- | --- |
| エイリアス名は現行の `haiku`/`sonnet`/`opus`/`fable` を維持 | 既存 ISSUE の `model:` ラベルを壊さない（概要の決定事項） |
| `ISSUE_AGENT_*` 環境変数は上書きとして残す。空文字は未設定とみなす | ai-schedule ジョブや手元の `.env` を壊さない。解決順は規約どおり 環境変数 → `config.toml`。空文字の扱いは概要の決定事項 |
| `bypassPermissions` + `deny_permissions.json` は変えない | 専用 worktree 内で動かしており規約 §4 の例外に該当 |

- 落とし穴: `worker.py` は `check.py` からサブプロセスで起動される。両方が同じ `config.toml` を同じ絶対パス（パッケージ基準）で解決すること。cwd 基準にしない。
- 落とし穴: テストが `monkeypatch.setenv` で設定を差し替えている箇所は、一時 TOML への置き換えが要る。開発者の `config.toml` に依存させない（規約 §8）。

## ルール更新ポイント

- `workflow/schedule/issue-agent/AGENTS.md`: 「設定は `config.toml`、秘密は `.env`、環境変数は一時上書き」の 3 行と、上書きできる環境変数名の一覧（キーの意味は見本のコメントを正とする）。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 「`config.py` + 見本 + テスト」「dispatch/worker/check の切替 + ログ」「.env.example・ドキュメント」の 3 項目。`uv run --project workflow/schedule/issue-agent pytest` が通ることを完了条件にする。
