# 自作スクリプトによる効率化ユースケース

MCPやAI検索を使わず、**素の `curl`/`requests` レベルの自作スクリプトだけで大幅に効率化できる**ポイントをまとめる。鍵になるのは次の2つの実測済み事実。

1. `docs.aws.amazon.com` の任意のページは `.html` → `.md` に拡張子を変えるだけで、**レンダリング不要の生Markdownが直接ダウンロードできる**（`Content-Type: text/markdown`、JS実行・HTMLパース・LLM呼び出し一切不要）。
2. `https://docs.aws.amazon.com/sitemap_index.xml` を起点に、**全ガイドのURL一覧を機械的に列挙できる**（実測: サブsitemapが10,879個）。各ガイドの `sitemap.xml` にはそのガイド内の全ページURL（例: S3 User Guideで798ページ）が入っている。

この2つを組み合わせると、「MCPツール呼び出し→LLMがHTML/Markdown変換」という重い経路を経由せず、**純粋なHTTPダウンロードだけでAWSドキュメントの全文ローカルコーパスが作れる**。

## ユースケース1: 特定サービスのドキュメント全文をローカルミラー化

**目的**: 特定サービス（例: S3、Lambda、Bedrock）のUser Guide全ページをローカルにMarkdownで保存し、`grep`/全文検索やベクトル埋め込みのソースにする。

**手順（概念）**:

1. `https://docs.aws.amazon.com/<Service>/latest/<guide>/llms.txt` を1回取得する（→ 全ページの `.md` URLリストがそのまま手に入る。sitemap.xmlより軽量で、説明文付きなのでページ選別もしやすい）。
2. リストされた `.md` URLを並列ダウンロード（`robots.txt` の `Crawl-delay: 5` に配慮し、同時接続数と間隔を抑える）。
3. ローカルに `<slug>.md` として保存 → ripgrepでの横断検索、または埋め込みモデルでベクトルDB化。

**効果**: MCPの `read_documentation` をページ数分呼ぶ場合と比べ、LLM呼び出し・ツールコール往復が一切発生しないため、数百ページ規模でも**秒〜分オーダー**で完結する。「S3 User Guideを丸ごと読んで質問に答えて」のような網羅系タスクの前処理に有効。

## ユースケース2: 新サービス・新機能のドキュメント差分監視

**目的**: 特定ガイドの更新（Document History / What's New ページ）を定期的に見張り、変更があればSlack通知などにつなげる。

**手順**: 各ガイドの `WhatsNew.md`（または `Reference.md` 等、`llms.txt` に載っているドキュメント履歴ページ）を定期取得し、前回保存分とdiffするだけ。`Last-Modified` / `ETag` ヘッダーも返ってくる（実測確認済み）ため、**HEADリクエストで更新有無だけ先にチェックしてから本文を取りに行く**、という軽量な差分検知が組める。

## ユースケース3: 複数サービス横断のAPIリファレンス一括収集

**目的**: 「このIAMアクションを使うサービス一覧」「特定のCloudFormationリソースタイプの全パラメータ」のような横断調査。

**手順**: ルート `https://docs.aws.amazon.com/llms.txt` から `APIReference` を含むガイドだけを抽出し、それぞれのガイド `llms.txt` から `.md` を収集。API Referenceは構造化されたパラメータ表が多く、Markdownテーブルとして機械的にパースしやすい。

## ユースケース4: 検索APIの直接利用（プロトタイピング限定）

`01-mcp-and-api.md` に記載の非公式エンドポイント `https://proxy.search.docs.aws.com/search` を直接叩けば、**MCPサーバーのプロセス起動すら不要**でキーワード検索ができる。大量クエリを投げるバッチ処理の試作には便利だが、非公式APIなので**本番運用の基盤にはしない**。恒久的に使うなら AWS Knowledge MCP Server 経由の `search_documentation` に寄せる。

## 実装時の注意点（共通）

- **`robots.txt` を尊重する**: `Crawl-delay: 5` が明示されているので、大量ページ取得時は最低5秒間隔、または並列数を絞る。`Disallow: /search/` の対象パス（検索結果ページのクロール）は避ける。
- **対象ドメインは `docs.aws.amazon.com` に閉じる**: `.md` 直取得のテクニックはこのドメイン配下でのみ確認済み。`aws.amazon.com/blogs/...` や `repost.aws` など別ドメインのAWSコンテンツには通用しない（HTML取得＋パースが必要、または `tav-cli` スキルの `tav extract` を使う）。
- **バージョン固定に注意**: URLの `latest` セグメントは常に最新ガイドを指す。過去バージョンとの差分を追いたい場合は取得日でスナップショットを残す設計にする。
- **キャッシュ設計**: `.md` レスポンスに `ETag`/`Last-Modified`/`Cache-Control: max-age=300` が付与されている（実測）。ローカルキャッシュ更新の判定に使える。

## この知見をスキル化する際の設計方針（次のステップ用メモ）

- 「軽い探索」は `llms.txt`（ルート→ガイド単位）で十分。**Tavily検索やMCP検索を呼ぶ前に、まず対象ガイドの `llms.txt` を1回引く**方が速くて安い。
- 「特定ページの本文が欲しい」なら `tav extract` や MCPの `read_documentation` を使うより、**URLの拡張子を `.md` に変えて直接フェッチ**する専用ツール/スクリプトを1つ用意した方が圧倒的に安価。
- 「サービス名や機能名だけ分かっていてURLが不明」な場合のみ、検索（AWS Knowledge MCPの`search_documentation`、または非公式APIの直叩き）に頼る。
