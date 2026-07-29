# Catalog API / Learn Platform API と llms.txt 調査

## Catalog API(研修コンテンツのメタデータ専用)

出典: https://learn.microsoft.com/en-us/training/support/catalog-api

- **ドキュメント本文の検索には使えない。** 対象はモジュール・ユニット・ラーニングパス・Applied Skills・認定資格・試験・集合研修(Instructor-Led Courses)のメタデータのみ。
- 認証不要、無料、REST、JSON レスポンス
- フルカタログ取得: `GET https://learn.microsoft.com/api/catalog/`(2022年時点で約13MB)
- クエリパラメータで絞り込み可能(例: `?type=modules&uid=<uid>`)。実際に叩いた例:

```
GET https://learn.microsoft.com/api/catalog/?locale=en-us&type=modules&uid=learn.wwl.introduction-to-azure-app-service
```

```json
{
  "modules": [
    {
      "summary": "...",
      "levels": ["intermediate"],
      "roles": ["developer"],
      "products": ["azure", "azure-app-service"],
      "uid": "learn.wwl.introduction-to-azure-app-service",
      "title": "Explore Azure App Service",
      "duration_in_minutes": 44,
      "rating": { "count": 8708, "average": 4.65 },
      "url": "https://learn.microsoft.com/en-us/training/modules/introduction-to-azure-app-service/...",
      "units": [
        "learn.wwl.introduction-to-azure-app-service.introduction",
        "..."
      ]
    }
  ]
}
```

- 1日1回以上リフレッシュ
- **重要**: 旧 Catalog API は非推奨予定(2026年6月まで動作継続)。後継は **Microsoft Learn Platform API**(追加のクエリパラメータなど機能強化版)。新規に作るなら後継 API のドキュメントを別途確認したほうがよい(`integrations-learn-platform-api-catalog` というページIDが案内されていた)。

## llms.txt / llms-full.txt

### サイト全体としては存在しない

- `https://learn.microsoft.com/llms.txt` → **404**(`en-us/llms.txt` にリダイレクトされた上で 404)
- `robots.txt` にも `llms.txt` への言及なし。sitemap インデックスのみ案内(`https://learn.microsoft.com/_sitemaps/sitemapindex.xml`)
- ページ単位の `.md` サフィックス直アクセス(`/overview.md` のような Mintlify/Fern 系サイトでよくあるパターン)も **404**、Learn では使えない

### 製品単位では llms.txt を配布している例がある

- 例: Teams SDK(`https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/developer-tools/llms-txt` で解説ページが読める)
  - ルート概要用の `llms.txt` と、言語別(TypeScript/Python/C#)のナビゲーション索引 + full 版(`llms-full.txt` 相当、コンテキストウィンドウが大きいツール向け)を提供
  - Teams 開発では `teams-dev` という agent skill をインストールすると、この llms.txt を自動的に参照してくれる、という案内もある
- **教訓**: 「Microsoft Learn 全体で使える単一の llms.txt」は無いので、そこに依存する設計は成立しない。製品ごとに存在有無を都度確認する必要がある。

### 代替の勝ち筋: content negotiation による生 Markdown 取得

llms.txt が無くても、**Learn の全ページは `Accept: text/markdown` ヘッダーを付けて GET するだけで、レンダリング前の生 Markdown ソース(YAML frontmatter 付き)をそのまま返す。** これは llms.txt/llms-full.txt が担うはずだった役割(LLM 向けのクリーンなテキスト取得)を、サイト全体・任意ページに対して代替できる。

検証コマンドと結果:

```bash
curl -s -H "Accept: text/markdown" \
  "https://learn.microsoft.com/en-us/azure/app-service/overview" \
  -w "status=%{http_code} type=%{content_type}\n"
# → status=200 type=text/markdown; charset=utf-8
```

取得できる内容の例(先頭部分):

```
---
layout: Conceptual
title: Overview of Azure App Service - Azure App Service | Microsoft Learn
canonicalUrl: https://learn.microsoft.com/en-us/azure/app-service/overview
description: Learn how Azure App Service helps you develop and host web applications.
ms.date: ...
...
---
# Azure App Service overview
...(本文 Markdown)
```

- ナビゲーションメニューや広告バナー等のノイズが一切入らない(HTML から `tav extract` した場合と比較して圧倒的にクリーン → トークン消費が少ない)
- frontmatter に `ms.date`(更新日)や `original_content_git_url`(GitHub 上のソースファイル)まで含まれており、更新監視や一次ソース特定にも使える
- MCP の `microsoft_docs_fetch` ツールも内部的にはこれと同じ仕組みで Markdown 変換していると考えられる(README に "Fetch and convert a Microsoft documentation page into markdown format" と明記)
- Learn の画面上の「Copy Markdown」ボタンも、恐らく同じ content negotiation を使っている

**注意点**: これは非公式に観測された挙動であり、Microsoft が正式にサポートを明言しているわけではない(MCP の `microsoft_docs_fetch` ツールが公式の入口)。将来的に仕様変更・アクセス制限される可能性はゼロではないため、大量・高頻度アクセスをするバッチ処理では MCP や CLI (`mslearn fetch`) を優先し、この裏技は補助的な検証・単発取得に留めるのが安全。
