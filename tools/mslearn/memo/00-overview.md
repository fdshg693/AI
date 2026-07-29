# Microsoft Learn 構造調査 — 概要

調査日: 2026-07-08
調査方法: `claude-plugins/web/skills/tav-cli` スキル(`tav search` / `tav extract`)+ `curl` による直接検証(content negotiation の確認など、tavily では見えない挙動があったため)

このディレクトリは「Microsoft Learn を効率よく検索する Claude Code スキル」を作るための事前調査メモ。詳細は各ファイルを参照。

## 結論(先に要点)

1. **Microsoft Learn には公式 MCP サーバーが存在する。** → まずはこれを使うのが最も手軽。認証不要・無料・公開エンドポイント。詳細は [01-mcp-server.md](01-mcp-server.md)。
2. **サイト全体の `llms.txt` / `llms-full.txt` は存在しない。** 一部の製品(Teams SDK など)だけが独自に配布している。ただし **`Accept: text/markdown` ヘッダーを付けて任意の Learn ページに GET するだけで、そのページの生 Markdown ソース(frontmatter 付き)がそのまま返る** という content negotiation の裏技があり、これが `llms.txt` 不在を補って余りある効率化ポイント。詳細は [02-catalog-api-and-llms-txt.md](02-catalog-api-and-llms-txt.md)。
3. **Catalog API(研修コンテンツのメタデータ専用 REST API)も別途あるが、ドキュメント本文の検索には使えない。** 学習パス/モジュール/認定資格のカタログを扱うときだけ使う。新しい後継 API(Microsoft Learn Platform API)への移行が案内されている(2026年6月で旧エンドポイント終了予定)。
4. **自作スキルを作るなら、MCP をラップするより「公式が既に配っている `microsoft-docs` / `microsoft-code-reference` Agent Skill をインストールする」方が早い。** それでも自作する価値があるユースケース(バッチ処理、Catalog API 連携、`--json` 出力のパイプライン化など)は [03-efficiency-ideas.md](03-efficiency-ideas.md) にまとめた。

## 選択の指針(「手軽な方を選択する想定」への回答)

| やりたいこと                                                             | 推奨手段                                                                                                              |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Claude Code から対話的に Learn ドキュメントを検索・参照したい            | **MCP サーバーをそのまま使う**(`/plugin install microsoft-docs@claude-plugins-official`)。自作不要。                  |
| 特定ページの本文だけ確実に、高速・低コストで取りたい(スクレイピング代替) | `curl -H "Accept: text/markdown" <URL>` を使う自作スクリプト。tavily extract や HTML パースより軽い。                 |
| 学習パス/モジュール/認定資格のメタデータを一括収集したい                 | Catalog API (`https://learn.microsoft.com/api/catalog/`) をそのまま叩く。                                             |
| シェルスクリプトや CI からノンインタラクティブに MCP 相当の検索をしたい  | `npx @microsoft/learn-cli`(`mslearn search/fetch/code-search --json`)。MCP クライアントを持たない環境向けの公式 CLI。 |

つまり「MCP か API か」という二択では、**MCP 一択**(公式が明言: Catalog API はドキュメント検索には非対応、Learn 本文用の伝統的な REST API は存在しない)。API 的な使い方が必要なら `Accept: text/markdown` の content negotiation と Catalog API を補助的に組み合わせる、という設計が現実的。
