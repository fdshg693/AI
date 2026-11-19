---
type: Plan Step
status: planning-breakdown
---

# Step 7: cline-wrapper — 既定プロバイダ・モデルを `config.toml` へ（Node 版の基準実装）

## やること

`lib/config.mjs` の `DEFAULT_PROVIDER_ID` / `DEFAULT_MODEL_ID` と、`main.mjs`・`repo-search.mjs` に散らばる `maxIterations`（3・14・10）を `cline-wrapper/config.toml` へ移す。`lib/config.mjs` を `smol-toml` で TOML を読み検証するローダーに作り替え、copilot-wrapper（Step 8）の写し元にする。

## 読むべきファイル・実行推奨Grep

**現行の設定経路を確認するため（優先度: 高）**

- 読む: `workflow/cline-wrapper/lib/config.mjs`、`lib/agent-runner.mjs`（既定値の受け方）、`lib/dotenv.mjs`
- 読む: `workflow/cline-wrapper/main.mjs`、`repo-search.mjs` — `--model` の解析と `resolveModel()` の使われ方、`maxIterations`
- Grep: `DEFAULT_MODEL_ID|DEFAULT_PROVIDER_ID|maxIterations` in `workflow/cline-wrapper`
- 読む: Step 1 の調査結果（Cline SDK のタイムアウト・使用量）

**テストの流儀を確認するため（優先度: 中）**

- 読む: `workflow/cline-wrapper/test-repo-tools.mjs` — 既存テストの書き方（`node` 直実行）
- 読む: `workflow/cline-wrapper/NEXT.md` — 進行中の作業と衝突しないか

## 触るファイル

### 新規

- `workflow/cline-wrapper/config.example.toml` — `[models.<alias>]`（`provider = "cline-pass"`、`id = "cline-pass/minimax-m3"`）、`[providers.cline-pass]`（`api_key_env = "CLINE_API_KEY"`）、`[limits]`（`main_max_iterations`・`explorer_max_iterations`・`answerer_max_iterations` 等、用途別）
- `workflow/cline-wrapper/test-config.mjs` — 見本が通ること・検証エラー

### 変更

- `workflow/cline-wrapper/lib/config.mjs` — `loadConfig(path?)` と `resolveModel(alias)` に置き換え。直書き定数を削除
- `workflow/cline-wrapper/lib/agent-runner.mjs` — 既定値の import をやめ、呼び出し側から必ず受け取る
- `workflow/cline-wrapper/main.mjs`、`repo-search.mjs` — `--model` はエイリアス。上限を config から。解決後モデル ID・使用量をログへ
- `workflow/cline-wrapper/package.json` — `smol-toml` を依存に、`test` に `test-config.mjs` を追加
- `workflow/cline-wrapper/AGENTS.md` — セットアップ・`--model` の説明
- `workflow/cline-wrapper/NEXT.md` — 「フル id または短い名前」の記述をエイリアス前提に

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| --- | --- |
| 旧来の「`provider/model` のフル ID を `--model` に直接渡す」形は廃止し、エイリアスのみ受ける | 規約 §1-4。試しに別モデルを使うときはカタログに 1 行足す |
| `api_key_env` で読む環境変数名をプロバイダ側に書く | 規約 §1 見本の形 |

- 落とし穴: `smol-toml` の追加はアンブレラの pnpm workspace で行う（`pnpm add smol-toml --filter cline-wrapper-example`）。`pnpm-lock.yaml` はアンブレラ側のコミットになる。

## ルール更新ポイント

- `workflow/cline-wrapper/AGENTS.md`: セットアップ手順とエイリアス指定の説明。

## 進め方

- **実行主体**: メインエージェント（基準実装）。
- **TODO化**: 「config.mjs + 見本 + テスト + 依存」「main / repo-search の切替 + ログ」の 2 項目。`pnpm --filter cline-wrapper-example test` が通ることを完了条件にする。
