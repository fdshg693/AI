---
type: Plan Step
status: planning-breakdown
---

# Step 8: copilot-wrapper — `.env` の非秘密設定を `config.toml` へ

## やること

`.env` で指定しているモデル・プロバイダ種別・ベース URL・`wire_api`・Azure API バージョンを `copilot-wrapper/config.toml` のカタログ（`[models.<alias>]` + `[providers.<name>]`）へ移す。`.env` は API キーと GitHub トークンだけにする。Step 1 で分かったタイムアウトを付け、使用量をログに出す。

## 読むべきファイル・実行推奨Grep

**現行の設定経路を確認するため（優先度: 高）**

- 読む: `workflow/copilot-wrapper/lib/config.mjs` — `resolveConfig(flags)` の検証（provider type・wire API・reasoning effort）
- 読む: `workflow/copilot-wrapper/main.mjs` — CLI フラグ、`createSession` への渡し方、`session.send` 後の待ち方
- 読む: `workflow/copilot-wrapper/.env.example`、`AGENTS.md`（Ollama 等ローカル利用の例）
- 読む: Step 1 の調査結果（Copilot SDK のタイムアウト・使用量）

**写し元（優先度: 高）**

- 読む: Step 7 の `workflow/cline-wrapper/lib/config.mjs`

## 触るファイル

### 新規

- `workflow/copilot-wrapper/config.example.toml` — `[providers.openai]`（`type`・`base_url`・`wire_api`・`api_key_env = "COPILOT_BYOK_API_KEY"`）、`[providers.ollama]`（キー不要の例）、`[models.<alias>]`、`[limits]`（`timeout_seconds`）、`[copilot]`（`use_logged_in_user`）
- `workflow/copilot-wrapper/test-config.mjs` — 見本が通ること・検証エラー

### 変更

- `workflow/copilot-wrapper/lib/config.mjs` — TOML 読み込みへ。`--model` と `COPILOT_BYOK_MODEL` はエイリアスだけを受ける。`--base-url` 等のフラグと残りの `COPILOT_BYOK_*` 環境変数は一時上書きとして残す（空文字は未設定）
- `workflow/copilot-wrapper/main.mjs` — ヘルプ文の更新（`--model llama3 --base-url ...` の例は、カタログの `ollama` プロバイダ + エイリアス指定の例に置き換える）、タイムアウト、ログ
- `workflow/copilot-wrapper/.env.example` — `COPILOT_BYOK_API_KEY` と `COPILOT_GITHUB_TOKEN` だけに
- `workflow/copilot-wrapper/package.json` — `smol-toml`、`test` スクリプト
- `workflow/copilot-wrapper/AGENTS.md` — 実行例をエイリアス指定に

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| --- | --- |
| API キーは `[providers.<name>].api_key_env` が指す環境変数から読む。キー不要のプロバイダは `api_key_env` を省略可 | 規約 §1-6。Ollama 等のローカル利用を壊さない |
| `--api-key` フラグは残す（変更しない） | 一時上書きの経路で、既存の使い方を壊さない。秘密を引数で渡す危険は AGENTS.md に 1 行注記 |
| `--approve-all` は CLI 明示時だけ有効のまま変えない | 既定は read とカスタムツールだけ許可で、規約 §4 に沿っている |

- 落とし穴: 既存ユーザーの `.env` に実 ID の `COPILOT_BYOK_MODEL`（`llama3` 等）が残っていると、エイリアス検証で起動時エラーになる。エラー文に移行案内を入れ、AGENTS.md に `.env` → `config.toml` のキー対応を書く。ベース URL 等の残りは上書きとして効き続ける。
- 落とし穴: 現行は `session.idle` を待つだけでタイムアウトが無い。上限を付けるときは `session.disconnect()` / `client.stop()` が確実に走ること。

## ルール更新ポイント

- `workflow/copilot-wrapper/AGENTS.md`: 移行手順（`.env` から `config.toml` へ移すキーの対応）を 1 段落。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 「config.mjs + 見本 + テスト + 依存」「main.mjs・.env.example・ドキュメント」の 2 項目。依存追加は `pnpm add smol-toml --filter copilot-wrapper-byok`。`pnpm --filter copilot-wrapper-byok test` が通ることを完了条件にする。
