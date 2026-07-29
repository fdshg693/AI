# AWS ドキュメントの API / MCP 利用方法

## 選択肢は3つ

AWS 公式のドキュメントアクセス手段は、大きく3段階ある。

| #   | 手段                                         | セットアップ                              | 認証                   | 手軽さ                         |
| --- | -------------------------------------------- | ----------------------------------------- | ---------------------- | ------------------------------ |
| 1   | **AWS Knowledge MCP Server**（リモート）     | クライアント側にURLを1行設定するだけ      | 不要（レート制限あり） | ◎ 最も手軽                     |
| 2   | **AWS Documentation MCP Server**（ローカル） | `uvx` 経由でプロセス起動、`uv`/Python必要 | 不要                   | ○ ローカル実行の分だけ手間     |
| 3   | **生の検索/取得エンドポイントを直叩き**      | 自作スクリプトで `curl`/`httpx`           | 不要（非公式）         | △ 手軽だが非公式で壊れるリスク |

結論: **「手軽な方を選択する」なら AWS Knowledge MCP Server 一択**。ローカルプロセス管理も認証も不要で、`https://knowledge-mcp.global.api.aws` を Streamable HTTP でMCPクライアントに登録するだけ。

出典: [AWS Knowledge MCP Server 公式ページ](https://awslabs.github.io/mcp/servers/aws-knowledge-mcp-server), [AWS Documentation MCP Server 公式ページ](https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server), [awslabs/mcp リポジトリ](https://github.com/awslabs/mcp)

---

## 1. AWS Knowledge MCP Server（推奨）

- 2025年10月にGA（一般提供開始）。AWSがフルマネージドでホストするリモートMCPサーバー。
- **AWSアカウント不要**、ローカルセットアップ不要、公開エンドポイント。
- ドキュメント本体だけでなく、What's New投稿、ブログ、Well-Architected ガイダンス、CDK/CloudFormationのベストプラクティス、Strands Agents SDK ドキュメント、"Agent Skills"（ドメイン特化のワークフロー集）まで横断検索できる。
- リージョン可用性情報（`get_regional_availability`）や、APIがどのリージョンで使えるかの情報も持っている。

### 設定例（Streamable HTTP）

```json
{
  "mcpServers": {
    "aws-knowledge-mcp-server": {
      "url": "https://knowledge-mcp.global.api.aws",
      "type": "http",
      "disabled": false
    }
  }
}
```

HTTPトランスポート未対応のクライアントでは `fastmcp` でstdio↔HTTPをブリッジできる:

```json
{
  "mcpServers": {
    "aws-knowledge-mcp-server": {
      "command": "uvx",
      "args": ["fastmcp", "run", "https://knowledge-mcp.global.api.aws"]
    }
  }
}
```

### 提供ツール

| ツール                      | 用途                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------- |
| `search_documentation`      | ドキュメント/ブログ/Agent Skills/Strands SDK を横断検索。トピックでの絞り込み可     |
| `read_documentation`        | 指定URLをMarkdownに変換して取得（`docs.aws.amazon.com` および `strandsagents.com`） |
| `list_regions`              | AWSリージョン一覧                                                                   |
| `get_regional_availability` | サービス/機能/SDK API/CloudFormationリソースのリージョン提供状況                    |
| `retrieve_skill`            | Agent Skill（特定ドメインのベストプラクティス集）を取得                             |

telemetryはモデル学習に使われない旨が明記されている。

---

## 2. AWS Documentation MCP Server（ローカル実行）

- `uvx awslabs.aws-documentation-mcp-server@latest` で起動するローカルMCPサーバー。
- 中国リージョン（`aws-cn` パーティション）向けドキュメントにも対応（`AWS_DOCUMENTATION_PARTITION=aws-cn`）。Knowledge MCP Serverはグローバル版のみなので、**中国リージョンのドキュメントが必要な場合はこちらを使う**。

### 設定例

```json
{
  "mcpServers": {
    "awslabs.aws-documentation-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_DOCUMENTATION_PARTITION": "aws"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Windows では `uv tool run --from awslabs.aws-documentation-mcp-server@latest awslabs.aws-documentation-mcp-server.exe` 形式になる（`uvx` 直接だと差異が出るため）。企業ネットワークでUser-Agentがブロックされる場合は `MCP_USER_AGENT` を上書きする。

### 提供ツール

| ツール                                   | 用途                                               |
| ---------------------------------------- | -------------------------------------------------- |
| `read_documentation`                     | ページをMarkdown化して取得                         |
| `search_documentation`（グローバルのみ） | 公式検索APIで検索                                  |
| `read_sections`（グローバルのみ）        | ページの特定セクションのみ抽出（長いページで有効） |
| `recommend`（グローバルのみ）            | 関連ページのレコメンド。新着情報の発見にも使える   |
| `get_available_services`（中国のみ）     | 中国リージョンで使えるサービス一覧                 |

---

## 3. 検索APIを直接叩く（非公式・参考情報）

AWS Documentation MCP Server のソースを読むと、`search_documentation` は以下の非公開エンドポイントをそのまま叩いているだけだと分かった。

- 検索: `POST https://proxy.search.docs.aws.com/search?session=<uuid>`
- レコメンド: `GET/POST https://api.contentrecs.docs.aws.com/v1/recommendations`

出典: [server_aws.py（awslabs/mcp）](https://github.com/awslabs/mcp/blob/main/src/aws-documentation-mcp-server/awslabs/aws_documentation_mcp_server/server_aws.py)

### 実際に叩いて動作確認済み（認証不要）

```bash
curl -s -X POST "https://proxy.search.docs.aws.com/search?session=$(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
    "textQuery": {"input": "S3 bucket versioning"},
    "contextAttributes": [{"key": "domain", "value": "docs.aws.amazon.com"}],
    "acceptSuggestionBody": "RawText",
    "locales": ["en_us"]
  }'
```

レスポンス例（抜粋）:

```json
{
  "queryId": "5fa5a5f3-...",
  "suggestions": [
    {
      "textExcerptSuggestion": {
        "link": "https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html",
        "title": "Retaining multiple versions of objects with S3 Versioning - Amazon Simple Storage Service",
        "summary": "Use versioning in Amazon S3 to keep multiple variants of an object in the same bucket.",
        "context": [
          { "key": "aws-docs-search-guide", "value": "User Guide" },
          {
            "key": "aws-docs-search-product",
            "value": "Amazon Simple Storage Service"
          }
        ]
      }
    }
  ]
}
```

`product_types` / `guide_types` で絞り込みたい場合は `contextAttributes` に `{"key": "aws-docs-search-product", "value": "..."}` / `{"key": "aws-docs-search-guide", "value": "..."}` を追加する（MCPサーバーの実装がやっていること）。

### 注意点

- **非公開・非公式API**。AWSが正式にドキュメント化していないエンドポイントであり、予告なく仕様変更・遮断される可能性がある。恒久的な自作パイプラインの土台にはしない方がよい。
- `docs.aws.amazon.com/robots.txt` は `Disallow: /search/`（検索UI画面のクロール禁止）を宣言している。上記APIエンドポイント自体は別ホスト（`proxy.search.docs.aws.com`）だが、AWS公式ドキュメントの検索機能を横取りしている点は意識しておく。
- **実運用では MCP 経由（1か2）を優先**し、直叩きは調査・プロトタイピング用途に留めるのが安全。

---

## まとめ・使い分け指針

- 迷ったら **AWS Knowledge MCP Server**。セットアップが最小で、ドキュメント以外（ブログ、Well-Architected、Agent Skills）も一括でカバーできる。
- **中国リージョンのドキュメント**が必要なら AWS Documentation MCP Server（ローカル、`aws-cn` パーティション）。
- **AWSサービス自体を操作**したい（CLI/boto3相当の実行）なら、これらとは別に **AWS API MCP Server** がある（今回のスコープ外だが存在だけ記録）。
