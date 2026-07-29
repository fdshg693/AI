# 自作スクリプトによる効率化ユースケース案

前提: MCP サーバー(https://learn.microsoft.com/api/mcp )と公式 Agent Skills があるため、**通常の対話的な調査は自作せず公式プラグインに任せるのが最も効率的**。以下は、それでも自作スクリプトを書く価値がある場面の案。

## 1. ページ本文の軽量一括取得(`Accept: text/markdown` 活用)

- ユースケース: 特定の Learn セクション配下(例: `azure/app-service/*`)を横断的に読み込んで要約・差分監視したい
- 方法:
  1. `sitemap`(`https://learn.microsoft.com/_sitemaps/sitemapindex.xml` 配下)や Learn の TOC(`toc.json`)から対象 URL 一覧を作る
  2. 各 URL に `curl -H "Accept: text/markdown"` で本文取得(HTML パース不要、ノイズなし)
  3. frontmatter の `ms.date` / `updated_at` を見て差分だけ再取得する差分更新スクリプトにできる
- 利点: `tav extract` や一般的な HTML スクレイピングよりトークン効率・速度ともに有利。MCP の `microsoft_docs_fetch` を1URLずつ呼ぶより、並列 curl の方が大量ページ処理には向く場面もある(ただしレート制限は考慮)

## 2. Catalog API を使った学習パス/認定資格のカタログ化

- ユースケース: 「Azure の初級〜上級の学習パスを一覧化して自社の研修計画に転記したい」「認定資格の出題範囲モジュールを一括収集したい」
- 方法: `https://learn.microsoft.com/api/catalog/?type=learningPaths&locale=ja-jp` のようにクエリして JSON を取得、`products` / `roles` / `levels` でフィルタするスクリプトを書く
- 利点: MCP の `microsoft_docs_search` はドキュメント検索用でカタログ全体を俯瞰する用途には向かない。Catalog API ならメタデータをまとめて機械的に処理できる
- 注意: 旧 Catalog API は2026年6月に非推奨予定 → 新規実装するなら Microsoft Learn Platform API 側の仕様を先に確認すべき

## 3. `mslearn --json` を使ったパイプライン処理

- ユースケース: CI やシェルスクリプトなど、MCP クライアントを持たない非対話環境から Learn 検索結果を取得し、後続処理(Slack通知、レポート生成など)に流し込みたい
- 方法:

```bash
npx @microsoft/learn-cli search "azure functions timeout" --json | jq '.results[].title'
```

- 利点: MCP プロトコルのハンドシェイクを自前実装せずに済む。`fetch --section <heading>` で見出し単位の部分取得もでき、トークン予算を抑えられる

## 4. `maxTokenBudget` を使ったコスト制御ラッパー

- ユースケース: 自作エージェントが1ターンで何度も Learn 検索するワークフロー(例: 複数の Azure サービスを横断比較する)で、検索結果のトークン量を予測可能にしたい
- 方法: MCP エンドポイントを直接叩く自作クライアントで `https://learn.microsoft.com/api/mcp?maxTokenBudget=<N>` を使う(ただし README は「エージェントフレームワーク経由推奨、直接エンドポイントに依存する実装は tools/list を都度呼んで動的に対応せよ」と注意している点に留意)

## 5. 自作スキルを作る場合の設計指針(公式2スキルからの学び)

自作する場合、`tav-cli` スキルのような「判断フロー付き一枚スキル」形式に寄せつつ、公式の `microsoft-docs` / `microsoft-code-reference` の以下の要素を踏襲すると質が上がりそうだった。

- **クエリの具体性を上げるコツを明示する**(❌ "Azure Functions" → ✅ "Azure Functions Python v2 programming model" のような Before/After 例を SKILL.md に埋め込む)
- **search → fetch の使い分け基準を明文化する**(チュートリアル全体が必要/検索結果が途中で切れている、など fetch すべき条件をリスト化)
- **CLI フォールバックを明記する**(MCP が使えない環境向けに `mslearn` コマンド対応表を用意する)
- **`context: fork` 相当の分離**(探索的な検索でメイン会話のコンテキストを汚さない設計)

## 未検証・今後の宿題

- Microsoft Learn Platform API(Catalog API 後継)の詳細な仕様・エンドポイント一覧は未調査。カタログ活用を本格的にやるなら別途調査が必要
- `Accept: text/markdown` の裏技はレート制限の閾値を確認していない。大量並列アクセスをする前に、MCP のレート制限方針(「公平利用のための制限あり、詳細非公開」)と合わせて実測での確認が望ましい
