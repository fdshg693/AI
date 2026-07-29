# Step 1: Linear GraphQL API仕様・Python実装方式の事前調査

> [00-overview.md](00-overview.md) の続き。Linear API は外部知識が必要なため、実装前に調査を独立ステップとして切り出す。このステップではコードは書かない。

## やること

Linear の GraphQL API 仕様と、Python CLI から叩くための実装方式（ライブラリ選定）を調査し、後続の Step2 に引き渡す。

## 調査観点・キーワード

- `Linear GraphQL API endpoint authentication` — APIエンドポイントURL、認証ヘッダ（`Authorization` の値・Bearer形式）、個人APIキー取得手順（Linear Settings > API）
- `Linear GraphQL schema issues teams projects labels comments` — 主要操作のクエリ/ミューテーション名・必須引数・戻りフィールド
- `Linear API pagination cursor` — Relay 仕様のページネーション（first/after/last/before + hasNextPage）の形式
- `Linear API rate limit` — レート制限（1,500 req/hour 等の数値）と残量ヘッダの有無
- `linear python package pypi maintenance` — サードパーティ `linear` PyPIパッケージの対応操作範囲・メンテ状況・最終更新
- `httpx GraphQL Python request` — 生 GraphQL リクエスト（httpx/requests）の最小構成とエラーハンドリング

## 実行した調査

tav-digest スキルで収集 → aim-ask 並列抽出のフローで実施。

1. **収集（tav）**: `tav crawl https://developers.linear.app/docs --topic linear-api-research --query "Linear GraphQL API authentication endpoint schema ... pagination cursor rate limit" --detail balanced --select-domain developers.linear.app` → 8ページ。**ただし Linear 開発者サイトは SPA（クライアントサイドレンダリング）のため、crawl/extract でも本文が取れずナビゲーションHTMLのみ**（各ページ char_count 1300前後で内容はリンク集）。
2. **補完収集（tav）**: `tav extract .../api-keys .../authentication` → 2ページ（同様に本文薄い）。`tav search-extract "linear python PyPI package GraphQL API client SDK" --include-domain pypi.org,github.com` → 5ページ。`tav search-extract "httpx GraphQL POST request Python Authorization header Bearer example"` → 5ページ。計20ページ。
3. **並列抽出（aim-ask, glm-5.2, jobs=6）**: 無関係 gist 2件(0013/0015)を除外した18件を投入 → `temp/web/linear-api-research/results.json`。公式ドキュメント系(0001-0010)は全て「ナビゲーションのみ、要フルページ再取得」。`0011`(linear-python-client GitHub)、`0012`(linear-api PyPI)に具体的情報あり。`0014/0016-0020`は「関連なし」と正しくフィルタ。
4. **SPA本文の代替取得（fetch_web_content）**: 公式ドキュメント(5URL)はSPAで本文取得不可。代わりに GitHub raw README と PyPI ページ（静的HTML）を直接取得して認証・操作・メンテ状況を補完。

**参照URL**:

- 公式ドキュメント（SPA本文取得不可、ナビゲーションのみ）: https://developers.linear.app/developers/graphql, /api-keys, /authentication, /pagination, /rate-limiting, /filtering
- GraphQL Schema（Apollo Studio）: https://studio.apollographql.com/public/Linear-API/schema/reference?variant=current
- linear-python-client (Hacker0x01): https://github.com/Hacker0x01/linear-python-client （README raw 取得済: https://raw.githubusercontent.com/Hacker0x01/linear-python-client/main/README.md）
- linear-api (PyPI): https://pypi.org/project/linear-api/

## 調査結果（後続ステップから参照する）

### クライアント方式

2つのサードパーティ Python パッケージを確認（公式SDKはTypeScriptのみ）:

- **linear-python-client**（Hacker0x01）: Pydantic ベースの同期的クライアント。viewer/issue/issues/create_issue/update_issue/create_comment/archive_issue/find_team/find_user/find_label/users/teams/projects/labels/states/comments を網羅。`execute()` で生 GraphQL 実行可（エスケープハッチ、data オブジェクト返却・エラー時例外）。テストカバレッジ~99%（fails under 90%）。smoke test が全メソッドをCI実行。GitHub Release → PyPI 自動公開（Trusted Publishing）。**活発**だが **Python 3.13+ 必要**。フィールド名は snake_case（camelCase エイリアス）。
- **linear-api**（MotleyCrew, PyPI 0.2.0, 2025-05-15）: `LinearClient` + リソースマネージャ（IssueManager/ProjectManager/TeamManager/UserManager）。`auto_unwrap_connections=True`（既定）で GraphQL connection ページネーション自動処理。CacheManager。MIT。Python >=3.9。ただし 0.1.0(2025-04)→0.2.0(2025-05) のみで更新頻度に停滞感。

**推奨**: linear-python-client は判定基準（主要操作網羅・活発）を満たし `execute()` で生 GraphQL も可能なため採用候補。ただし **Python 3.13+ 要件**と Pydantic 依存に注意。tav-cli の薄い httpx+json パターンとの整合性・依存最小化を最優先する場合は **生 GraphQL (httpx)** も有力（Linear API は単一エンドポイント・Authorization 生キー・Relay ページネーションで実装容易、依存は httpx のみ）。**最終判断は Step2**（Step2 はリポジトリの Python 環境と tav-cli 整合性を踏まえて決定）。

### APIエンドポイント

- GraphQL **単一エンドポイント**: `https://api.linear.app/graphql`（linear-python-client README には明記なし、Linear developer docs およびパッケージ実装で確認。Step2 で linear-python-client の client.py ソースを参照して確定）。
- GraphQL Schema は Apollo Studio で公開（上記参照URL）。

### 認証

- **個人APIキー**: `LinearClient(api_key="lin_api_...")` — **Authorization ヘッダの値として生のキーをそのまま送信（Bearer 不要）**。README 明記「sent as the raw `Authorization` header value」。キーは `lin_api_` プレフィックス。
- **OAuth 2.0**: `LinearClient(access_token="...")` — `Authorization: Bearer <token>` 形式。
- **LINEAR_API_KEY 環境変数**で `LinearClient()` 無引数呼び出し可（tav-cli の `TAVILY_API_KEY` と同じ .env 運用に揃う）。
- 個人APIキーの取得: Linear Settings > API（README に画面詳細なし、公式 /api-keys ページも SPA で本文取得不可）。スコープはアカウント権限範囲（README 明記なし）。

### ページネーション

- **Relay/Connections パターン**: クエリ引数 `first`/`after`（+ `last`/`before`）、戻りは `.nodes` と `.page_info.has_next_page` / `.page_info.end_cursor`。
- linear-python-client: `client.issues(IssuesRequest(first=20, filter={...}, order_by="updatedAt"))` → `.nodes`, `.page_info`。`client.paginate(client.issues, request)` で cursor 跨ぎ自動取得。
- linear-api: `auto_unwrap_connections=True` で connection を検出したら追加リクエストで全ページ自動取得・結合。
- **CLI 側の件数制御方針**: `--limit`/`--first` を `first` 引数に変換し、残ページは `after=end_cursor` で追跡（linear-python-client の `paginate()` または生 httpx で同様実装。tav-cli の ResultEnvelope 的な戻り値契約に合わせる）。

### レート制限

- 公式ドキュメント（/developers/rate-limiting）は SPA で本文取得不可。linear-python-client/linear-api の README にも記載なし。
- **本調査では数値・残量ヘッダ・429 の扱いを公式ソースから確認できず**。Step2 実装時に Apollo Studio Schema または linear-python-client の client.py 実装で確認。実務上は **429 検出時に指数バックオフでリトライする最小実装**で十分（tav-cli/aim-ask と同等の安全機構）。

### httpx で生 GraphQL を送る最小構成（参考）

- linear-python-client の `execute()` が実質これを担う（任意の GraphQL 文字列を POST、`data` 返却・エラー時例外）。
- 生 httpx の場合は: `POST https://api.linear.app/graphql`、`Authorization: lin_api_...`（生キー）、`Content-Type: application/json`、body `{"query": "...", "variables": {...}}`。`0019`(GraphQL via HTTP) に一般例あり。

---

## 書き方のポイント

- 調査ステップの目的は「Step2 を読むエージェントが Web検索・ページ全文を読み直さずに済むこと」。読んだページの全文は書かず、**要約 + 参照URL** だけ残す。
- 調査観点は検索前に洗い出しておく。クライアント方式（サードパーティ vs 生 GraphQL）は本機能の最大の設計分岐なので、判定基準まで書いておく。
- 軽量なコードベース内調査（tav-cli の client生成パターンの再利用可否など）は必要に応じて Haiku サブエージェントへ委任してよい。決定（採用するか）は本ステップで行う。
- このステップ自体は `.claude/rules` を更新しない（知識がまだコードに反映されていないため。ルール更新は Step2）。
