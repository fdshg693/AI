# AWS ドキュメント調査 概要

AWS ドキュメントを効率よく検索・取得するスキルを作る前段の調査メモ。`tav-cli` スキル（Web検索）と `curl` による直接検証の両方で確認した。

## 調査結果サマリ

| 観点                 | 結論                                                                                                                                                           |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MCP / API            | **AWS Knowledge MCP Server**（リモート・フルマネージド・認証不要）が最も手軽。生の検索APIも直接叩けるが非公式                                                  | 詳細: [01-mcp-and-api.md](01-mcp-and-api.md)                           |
| llms.txt             | `docs.aws.amazon.com` は **ルート `llms.txt`/`llms-full.txt` あり**、さらに**ガイド単位の `llms.txt`** もあり。ただし "full" でも本文全文ではなく目次+リンク集 | 詳細: [02-llms-txt.md](02-llms-txt.md)                                 |
| 自作スクリプトの旨味 | 全ページに **`.html` → `.md` で生Markdownが直接取れる**（JS不要・課金不要）。sitemap と組み合わせれば大量ページの一括ローカルミラーが非常に安く作れる          | 詳細: [03-custom-script-efficiency.md](03-custom-script-efficiency.md) |

## 最重要発見（3行で）

1. `docs.aws.amazon.com` の任意のページは、URL 末尾を `.html` → `.md` に変えるだけで生の Markdown 本文が直接ダウンロードできる（`Content-Type: text/markdown`、JS実行・HTMLパース不要）。
2. 各ガイド配下には `llms.txt`（例: `https://docs.aws.amazon.com/AmazonS3/latest/userguide/llms.txt`）があり、そのガイド内の全ページ一覧＋説明文＋`.md` リンクが一括で手に入る。ルート `https://docs.aws.amazon.com/llms.txt` は全ガイドの索引。
3. AWS 公式の「AWS Documentation MCP Server」がそのまま使っている検索APIは `https://proxy.search.docs.aws.com/search`（POST, 認証不要）。ただし非公式・非公開なので、恒久的な依存は推奨しない。まずは **AWS Knowledge MCP Server**（`https://knowledge-mcp.global.api.aws`）を使うのが無難。

## このディレクトリの構成

- [01-mcp-and-api.md](01-mcp-and-api.md) — MCP サーバー各種と検索APIの比較・使い方
- [02-llms-txt.md](02-llms-txt.md) — llms.txt / llms-full.txt / ページ単位 .md の実測結果
- [03-custom-script-efficiency.md](03-custom-script-efficiency.md) — 自作スクリプトで効率化できるユースケース
