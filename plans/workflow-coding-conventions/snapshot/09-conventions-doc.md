---
type: Plan Step
status: planning-breakdown
---

# Step 9: 規約ドキュメントを実態に合わせる

## やること

02〜08 の結果を受けて `workflow/docs/coding-conventions.md` の「既存コードの移行」表を更新し、実行中に決めた解釈（置き場所・例外）を本文へ反映する。`workflow/README.md` の該当箇所も確認する。

## 読むべきファイル・実行推奨Grep

**反映内容を集めるため（優先度: 高）**

- 読む: 02〜08 の各ステップの「実行中に判明した変更」節と「ルール更新ポイント」
- 読む: Step 1 の調査結果 — SDK が対応しておらず付けられなかった上限

**残っている食い違いを確認するため（優先度: 中）**

- Grep: `MODEL\s*=|DEFAULT_MODEL|os\.environ\.get\(".*MODEL|process\.env\..*MODEL` in `workflow/` — 直書きの取り残し
- Grep: `config.toml` in `workflow/**/AGENTS.md` — セットアップ手順の記載漏れ

## 触るファイル

### 変更

- `workflow/docs/coding-conventions.md` — 移行表の完了行を削除し、残った食い違い（例: codex-wrapper の `cwd` がアンブレラ全体）を記載。§1-1 の置き場所を「uv / pnpm プロジェクトのディレクトリ（無ければエントリスクリプトのあるディレクトリ。例: codex-wrapper）直下」に。§1 の解決順に「上書き用の環境変数の空文字は未設定とみなす（tool-conventions 規則 1 の例外）」を追記。§3 に SDK ごとの上限の可否を短く注記（必要な場合のみ）。frontmatter の `generated.at` を更新
- `workflow/README.md` — 規約への導線の文言確認（変更不要なら触らない）

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| --- | --- |
| SDK ごとの詳細な調査結果は規約に転記せず、付けられない上限の事実だけを 1 行で書く | 規約は書き方のルールで、SDK 仕様のまとめではない |

## ルール更新ポイント

- このステップ自体がルール更新。`workflow/docs/coding-conventions.md` の `status: draft` を `stable` にするかはユーザーに確認する。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 1 項目。完了後、概要の完了記録（`progress/99-completion.md`）を書く。
