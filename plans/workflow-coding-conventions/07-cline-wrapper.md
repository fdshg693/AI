---
type: Plan Step
status: ready
---

# Step 7: cline-wrapper — 既定プロバイダ・モデルを `config.toml` へ（Node 版の基準実装）

## やること

`lib/config.mjs` の `DEFAULT_PROVIDER_ID` / `DEFAULT_MODEL_ID` と、`main.mjs`・`repo-search.mjs` に散らばる `maxIterations`（3・14・10）を `cline-wrapper/config.toml` へ移す。`lib/config.mjs` を `smol-toml` で TOML を読み検証するローダーに作り替え、copilot-wrapper（Step 8）の写し元にする。

## 読むべきファイル・実行推奨Grep

**現行の設定経路を確認するため（優先度: 高）**

- 読む: `workflow/cline-wrapper/lib/config.mjs`、`lib/agent-runner.mjs`（既定値の受け方）、`lib/dotenv.mjs`
- 読む: `workflow/cline-wrapper/main.mjs`、`repo-search.mjs` — `--model` の解析と `resolveModel()` の使われ方、`maxIterations`
- Grep: `DEFAULT_MODEL_ID|DEFAULT_PROVIDER_ID|maxIterations` in `workflow/cline-wrapper`
- Step 1 の調査結果は下の決定事項に反映済み（根拠: [progress/01-research-results.md](progress/01-research-results.md)）

**テストの流儀を確認するため（優先度: 中）**

- 読む: `workflow/cline-wrapper/test-repo-tools.mjs` — 既存テストの書き方（`node` 直実行）
- 読む: `workflow/cline-wrapper/NEXT.md` — 進行中の作業と衝突しないか

## 触るファイル

### 新規

- `workflow/cline-wrapper/config.example.toml` — `[models.<alias>]`（`provider = "cline-pass"`、`id = "cline-pass/minimax-m3"`）、`[providers.cline-pass]`（`api_key_env = "CLINE_API_KEY"`）、`[limits]`（`main_max_iterations`・`explorer_max_iterations`・`answerer_max_iterations` 等、用途別）、`timeout_seconds`・`max_cost_usd`・`max_total_tokens`
- `workflow/cline-wrapper/test-config.mjs` — 見本が通ること・検証エラー

### 変更

- `workflow/cline-wrapper/lib/config.mjs` — `loadConfig(path?)` と `resolveModel(alias)` に置き換え。直書き定数を削除
- `workflow/cline-wrapper/lib/agent-runner.mjs` — 既定値の import をやめ、呼び出し側から必ず受け取る
- `workflow/cline-wrapper/main.mjs`、`repo-search.mjs` — `--model` はエイリアス。上限を config から。解決後モデル ID・使用量をログへ
- `workflow/cline-wrapper/package.json` — `smol-toml` を依存に、`test` に `test-config.mjs` を追加
- `workflow/cline-wrapper/AGENTS.md` — セットアップ・`--model` の説明
- `workflow/cline-wrapper/NEXT.md` — 「フル id または短い名前」の記述をエイリアス前提に

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                                          | 理由                                                                                                           |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| ターン数は `maxIterations`。タイムアウトと予算は `runAgent` に `timeoutMs`・`maxCostUsd`・`maxTotalTokens` を足し、`setTimeout` と `usage-updated` イベントから `agent.abort(reason)` を呼ぶ。理由は自前の変数に残し、終了後に `clearTimeout` | Step 1: SDK にタイムアウト・予算のオプションは無い。`run()` は signal を受けず、`abort()` は実行中しか効かない |
| 終了理由は `status`・`maxIterations` の文言（`status:"failed"` + `Agent runtime exceeded maxIterations`）・abort 理由から `completed / max_iterations / timeout / budget / aborted / failed` に正規化する                                     | Step 1: 上限到達は例外にならず `failed` になる                                                                 |
| ログ（JSON 1 行）: 要求エイリアス・指定した `modelId`・`agentId`/`runId`・自前で渡す `sessionId`・`iterations`・`usage`・終了理由。解決後モデル ID は SDK から取れないので指定値を記録する（規約 §7 の例外として AGENTS.md に 1 行）          | Step 1: `messages[].modelInfo` は設定値の写し                                                                  |
| `usage.totalCost` が無いプロバイダでは USD 上限を判定しない（トークン上限だけ効かせる）。単価表は持たない                                                                                                                                     | YAGNI。cline-pass は `totalCost` を返す前提で、返さないときはログに `cost: null`                               |
| 旧来の「`provider/model` のフル ID を `--model` に直接渡す」形は廃止し、エイリアスのみ受ける                                                                                                                                                  | 規約 §1-4。試しに別モデルを使うときはカタログに 1 行足す                                                       |
| `api_key_env` で読む環境変数名をプロバイダ側に書く                                                                                                                                                                                            | 規約 §1 見本の形                                                                                               |

- 落とし穴: `smol-toml` の追加はアンブレラの pnpm workspace で行う（`pnpm add smol-toml --filter cline-wrapper-example`）。`pnpm-lock.yaml` はアンブレラ側のコミットになる。

## 実行中に判明した変更

- 2026-11-14（Step 1 完了時）: SDK の上限・使用量の調査結果を「決定事項・注意点」に反映（abort による上限・終了理由の正規化・ログ項目）。根拠は [progress/01-research-results.md](progress/01-research-results.md)。

## ルール更新ポイント

- `workflow/cline-wrapper/AGENTS.md`: セットアップ手順とエイリアス指定の説明。

## 進め方

- **実行主体**: メインエージェント（基準実装）。
- **TODO化**: 「config.mjs + 見本 + テスト + 依存」「main / repo-search の切替 + ログ」の 2 項目。`pnpm --filter cline-wrapper-example test` が通ることを完了条件にする。
