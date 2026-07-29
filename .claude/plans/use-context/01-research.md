# Step 1: Context7 API仕様の事前調査

> [00-overview.md](00-overview.md) の続き。

## やること

Context7のドキュメント取得手段について、(a) MCPを介さない素のREST APIが公開されているか、(b) 公開されていない場合に公式MCPサーバー（`https://mcp.context7.com/mcp`）をPythonから叩く実装方式、の両方を調査し、Step2（CLI実装）の判断材料を揃える。このステップではコードを書かない。

既存の`claude-plugins/my-tools/skills/use-context/memo/`は2026-07-26時点で`tav-cli`による調査済みだが、MCPサーバー経由の情報が中心で、素のREST APIの有無までは確定していない。ここを本ステップで確定させる。

## 調査観点・キーワード

- `Context7 API Guide site:context7.com` — [https://context7.com/docs/api-guide](https://context7.com/docs/api-guide) の内容。MCPを介さない直接HTTPエンドポイントの有無、エンドポイントURL、認証方式（APIキーのヘッダー名）、レスポンス形式
- `Context7 resolve-library-id REST endpoint` / `Context7 search library REST endpoint` — ライブラリ候補検索（`resolve-library-id`相当）がREST公開されているか
- `Context7 get-library-docs REST endpoint` / `Context7 query-docs REST` — ドキュメント取得（`query-docs`相当）がREST公開されているか。パラメータ（`libraryId`, `topic`/`query`, トークン上限等）
- `Context7 rate limit API key header` — APIキー無し/ありのレート制限値、429時の`Retry-After`等のヘッダー
- `Context7 CLI GitHub source ctx7` — 公式Node製CLI（`npx ctx7`）の実装（[https://github.com/upstash/context7](https://github.com/upstash/context7)）がREST・MCPのどちらを叩いているか、一次ソースとして確認できれば採用
- `Python MCP client library fastmcp streamable-http remote server` — RESTが無くMCP専用の場合、Pythonから公式MCPサーバーに接続する実装方法。`tools/mslearn`が使っている`fastmcp`パターンをそのまま流用できるか確認する

## 読むべきファイル・実行推奨Grep

**既存の類似実装（MCPサーバーをCLI化したパターン）を確認するため（優先度: 高）**

- 読む: `tools/mslearn/mslearn_core/client.py` — `fastmcp`でMCPサーバーに接続し、ツール呼び出し結果をCLIの戻り値に変換している実装
- 読む: `tools/mslearn/mslearn_core/config.py` / `output.py` / `rendering.py` — 環境変数の扱い、結果のファイル書き出し・`index.md`生成のパターン
- 読む: `tools/mslearn/mslearn_cli.py` — argparseベースのサブコマンド構成、`--json`フラグ、終了コード設計

**RESTを直叩きする場合の実装パターンを確認するため（優先度: 中）**

- 読む: `tools/tav-cli/tav_core/result_contract.py` / `output.py` — SDK（非MCP）を直接叩く場合の結果契約・出力先設計。RESTが使える場合はこちらに近い構成になる
- Grep: `httpx|requests` in `tools/` — 既存CLIがHTTP直叩きにどのライブラリを使っているか確認し、依存追加方針を揃える

**メモの既知情報を裏取りするため（優先度: 低）**

- 読む: `claude-plugins/my-tools/skills/use-context/memo/01-context7-mcp-and-cli.md` — 既存調査で分かっているMCPエンドポイント・ライブラリIDフォーマット・レート制限の記述（RESTの有無自体はここでは未確定）

## 実行した調査

- `tav-cli`スキル（`tav extract`）で以下の公式ドキュメントページを取得・読解した。
  - [API Guide](https://context7.com/docs/api-guide)
  - [CLI](https://context7.com/docs/clients/cli)
  - [MCP Clients](https://context7.com/docs/resources/all-clients)
  - [Search for libraries（APIリファレンス）](https://context7.com/docs/api-reference/search/search-for-libraries)
  - [Get documentation context（APIリファレンス）](https://context7.com/docs/api-reference/context/get-documentation-context)
- `tools/mslearn/mslearn_core/{client,config}.py`・`tools/tav-cli/tav_core/environment.py`・`tools/tav-cli/README.md`を読み、既存2パターン（fastmcp経由のMCPクライアント／SDK直叩き）の実装差分を確認した。

## 調査結果（後続ステップから参照する）

**1. REST APIの有無 → 公開されている（結論）**

Context7は`https://context7.com/api/v2/...`配下にMCPを介さない素のREST APIを公開している。根拠: [API Guide](https://context7.com/docs/api-guide)。したがって **MCPクライアント実装は不要**、REST直叩きで実装する。

主要エンドポイント（今回のスキルで使うのは上2つのみ）:

| Method | Endpoint                               | 用途                                             |
| ------ | -------------------------------------- | ------------------------------------------------ |
| `GET`  | `/api/v2/libs/search`                  | ライブラリ名候補検索（`resolve-library-id`相当） |
| `GET`  | `/api/v2/context`                      | ドキュメントコンテキスト取得（`query-docs`相当） |
| `POST` | `/api/v1/refresh`                      | ライブラリの再インデックス（今回不要）           |
| その他 | `/api/v2/policies`, `/api/v2/add/*` 等 | チームスペース管理・ライブラリ登録系（今回不要） |

**2. 認証**

- ヘッダー: `Authorization: Bearer <CONTEXT7_API_KEY>`
- 環境変数命名案: `CONTEXT7_API_KEY`（公式CLI・公式MCPと同名。ユーザーが既存の値をそのまま使い回せる）
- **矛盾する記述に注意**: [API Guide](https://context7.com/docs/api-guide#authentication)は「全APIリクエストにAPIキー必須」と明記する一方、[CLI](https://context7.com/docs/clients/cli#authentication)は「`ctx7 library`/`ctx7 docs`は未ログインでも動作し、ログインで上限が上がるだけ」と記載しており、REST APIとして本当にキー必須なのか（＝キー無しリクエストが401になるか、低レート制限で通るか）は未実機検証。**Step2で実際に無認証リクエストを1回試すこと。**

**3. パラメータ**

- `libs/search`: `libraryName`(必須, 1–500文字), `query`(必須, 1–500文字), `fast`(`true`/`false`, 既定`false`＝LLM再ランキングあり)
- `context`: `libraryId`(必須, 1–500文字, パターン`^/[^/]+/[^/]+([/@][^/]+)?$`), `query`(必須, 1–500文字), `type`(`json`/`txt`, **既定`txt`**), `fast`(`true`/`false`, 既定`false`)
- ライブラリIDフォーマット: `/owner/repo`(GitHub), `/websites/<name>`, `/llmstxt/<name>`, `/packages/<name>`または`/npm/<name>`, `/docs/<name>`(アップロード文書)。バージョン指定は`/owner/repo/v1.2.3`または`/owner/repo@v1.2.3`のどちらでも可。

**4. レスポンススキーマ**

- `libs/search`（200）: `{"results": [{"id","title","description","branch","lastUpdateDate","state","totalTokens","totalSnippets","stars","trustScore","benchmarkScore","versions"}], "searchFilterApplied": bool}`
- `context`（`type=json`）: `{"codeSnippets": [{"codeTitle","codeDescription","codeLanguage","codeTokens","codeId","pageTitle","codeList":[{"language","code"}]}], "infoSnippets": [{"pageId","breadcrumb","content","contentTokens"}], "rules": [...]（省略可）}`
- `context`（`type=txt`、既定）: 整形済みプレーンテキスト。公式`ctx7 docs`がターミナル表示に使っている形式と同種と推測されるが、実物は未確認（Step2で実クエリを打って確認する）。

**5. レート制限**

- キー無し: 低い制限。キーあり: プランに応じて高い制限（具体的な数値は非公開、ダッシュボードで確認する仕様）。
- `429`時のレスポンスヘッダー: `Retry-After`(秒), `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`(Unixタイムスタンプ)
- 公式サンプルコードは指数バックオフで最大3回リトライする実装を提示している。

**6. エラーハンドリング**

- ステータスコード: `200`成功 / `202`ライブラリ未確定（待って再試行）/ `301`リダイレクト（レスポンスの`redirectUrl`に新IDが入る）/ `400`不正パラメータ / `401`APIキー不正 / `403`アクセス拒否 / `404`ライブラリ無し / `409`既に登録済み / `422`処理不可 / `429`レート制限 / `500`/`503`/`504`
- エラー時は`{"error": "...", "message": "..."}`形式のJSONが返る。

**7. 典型的な分量（フォルダ書き出し vs terminal直接出力の判断材料）**

- 個々のスニペットには`codeTokens`/`contentTokens`（例では100〜200程度）が付くが、1クエリあたりのスニペット総数に明示的な上限パラメータは無い（旧来のMCPツールにあった`tokens`総量制御パラメータはREST APIには無い）。
- 公式`ctx7 docs`はターミナルにそのまま整形表示する設計であり、`mslearn`の`fetch`（Webページ丸ごと）ほど巨大にはならない想定だが、断定はできない。**Step2実装時に実クエリを打って実測し、`terminal直接出力`か`mslearn型（フォルダ+index.md）`かを最終判断する。**

**8. 採用方針（結論）**

- **MCPクライアントは不要。REST直叩きで実装する。**
- 依存ライブラリは`requests`を採用する。理由: 公式ドキュメントのコード例が`requests`を使用しており踏襲しやすいこと、Context7には`tavily-python`のような公式Python SDKが存在しない（[SDK and Libraries](https://context7.com/docs/api-guide#sdk-and-libraries)にあるのはTypeScript SDKのみ）ため生のHTTPクライアントが必要になること。
- 実装パターンは`tools/mslearn`（`fastmcp`でMCPサーバーに接続する型）ではなく、`tools/tav-cli`（SDK/APIを直接叩き`tav_core/environment.py`で`.env`・APIキー・出力先を管理する型）に近い構成になる。`fastmcp`依存は追加しない。

**9. 未確定・Step2の実装中に確認すべき事項**

- 無認証（`Authorization`ヘッダー無し）でのアクセスが実際に通るか（401になるかどうか）
- `type=txt`レスポンスの実際の見た目・分量
- `fast=true`と既定(`false`)の応答速度・品質の体感差
- `202`（ライブラリ未確定）が実際にどの程度の頻度で発生するか

## 00-overview.mdへの影響（決定事項の確定）

- [00-overview.md](00-overview.md)の決定事項表にある「CLIをMCP経由で叩くか素のREST APIで叩くかは断定せず、Step1の調査結果に基づき確定する」は、**REST直叩きに確定**した。
- Step2（[02-implement-cli.md](02-implement-cli.md)、未作成）の実装は、`fastmcp`ではなく`requests` + `python-dotenv`を依存に追加し、`tools/tav-cli`の構成（`*_core/environment.py`によるAPIキー・出力先管理、`README.md`のセットアップ手順）を土台にする。`tools/mslearn`のfastmcpパターンは参照不要。

## `.claude/rules` 更新ポイント

- 更新なし。調査結果はStep2の実装判断へ引き渡す。
