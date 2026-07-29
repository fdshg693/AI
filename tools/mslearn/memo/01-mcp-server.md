# Microsoft Learn MCP Server

## 概要

- 正式名称: Microsoft Learn MCP Server(旧称 Microsoft Learn Docs MCP Server)
- 公式ドキュメント: https://learn.microsoft.com/en-us/training/support/mcp
- GitHub リポジトリ: https://github.com/MicrosoftDocs/mcp (`aka.ms/learnmcpdocs/repo` からリダイレクト)
- 用途: GitHub Copilot などの AI エージェントに、Microsoft 公式ドキュメントの最新情報を直接渡すためのリモート MCP サーバー
- **認証不要・無料・公開エンドポイント**
- Streamable HTTP 方式(SSE ではない)

## エンドポイント

```
https://learn.microsoft.com/api/mcp
```

- ブラウザから直接アクセスすると `405 Method Not Allowed` になる(MCP クライアント経由が前提)
- 標準的なクライアント設定例:

```json
{
  "servers": {
    "ms-learn": {
      "type": "http",
      "url": "https://learn.microsoft.com/api/mcp"
    }
  }
}
```

### 実験的エンドポイント

- OpenAI Deep Research 互換: `https://learn.microsoft.com/api/mcp/openai-compatible`
- トークン予算制御: `https://learn.microsoft.com/api/mcp?maxTokenBudget=2000`
  - 検索結果のみに効く(`fetch` は常にフルページを返す)
  - エージェントループで1ターンに何度も呼ぶ場合は低めに、リッチな単発応答が欲しい場合は高めに設定

## 提供ツール

| ツール名                       | 説明                                                 | 入力パラメータ                                  |
| ------------------------------ | ---------------------------------------------------- | ----------------------------------------------- |
| `microsoft_docs_search`        | Microsoft 公式技術ドキュメントへのセマンティック検索 | `query` (string)                                |
| `microsoft_docs_fetch`         | 指定 URL の Learn ページを Markdown 形式で取得       | `url` (string)                                  |
| `microsoft_code_sample_search` | 公式の Microsoft/Azure コードサンプル検索            | `query` (string), `language` (string, optional) |

**注意**: 開発者向けリファレンス(https://learn.microsoft.com/en-us/training/support/mcp-developer-reference )では「これは伝統的な意味での API ではない」と明言されている。ツール一覧やスキーマは動的に変わりうるため、クライアント側は `tools/list` を都度呼んでハードコードを避けるべき、とベストプラクティスに明記(https://learn.microsoft.com/en-us/training/support/mcp-best-practices )。

## 制限事項・FAQ からの要点

出典: https://learn.microsoft.com/en-us/training/support/mcp (overview) / mcp-faq / mcp-best-practices

- 含まれるのは公開ドキュメントのみ(トレーニング内容やユーザープロファイル情報は含まない)
- 裏側のナレッジサービスは、コンテンツ更新のたびに逐次更新 + 1日1回のフルリフレッシュ
- レート制限は存在する(具体的な数値は非公開。公平利用のため)。問題があれば GitHub リポジトリで報告可能
- フィルタリング機能は無い(クエリの中でスコープを指定する形で代替する)
- リンク切れ(404)は基本的に発生しないよう、コンテンツ移動時はリダイレクトされる設計

## Microsoft Learn CLI(`mslearn`)— MCP クライアントを持たない環境向け

- npm パッケージ: `@microsoft/learn-cli`(preview)
- MCP サーバーと同じツールをターミナルから叩ける
- Node.js 22+ が必要

```bash
# インストール不要で実行
npx @microsoft/learn-cli search "azure functions timeout"

# グローバルインストール
npm install -g @microsoft/learn-cli
mslearn search "azure functions timeout"
mslearn fetch "https://learn.microsoft.com/azure/azure-functions/functions-versions"
mslearn fetch "<url>" --section "Function app timeout duration"
mslearn fetch "<url>" --max-chars 3000
mslearn code-search "cosmos db change feed processor" --language csharp
mslearn doctor --format json
```

- `search` / `code-search` は `--json` で構造化出力(`jq` などパイプライン処理向け)
- エンドポイント変更は `MSLEARN_ENDPOINT` 環境変数 or `--endpoint`

## 公式 Agent Skills(そのまま使える出来合いのスキル)

GitHub リポジトリ(`MicrosoftDocs/mcp`)内で、MCP サーバーとセットで **公式の Agent Skills** が配布されている。

| スキル                     | 用途                                                              | 向いている場面                                          |
| -------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------- |
| `microsoft-docs`           | 概念理解・チュートリアル・設定・制限値の調査                      | 「〜はどう動くか」「クイックスタート」など              |
| `microsoft-code-reference` | API 検索・コードサンプル・エラー修正の検証                        | コードを書く/直す/API 署名を確認する                    |
| `microsoft-skill-creator`  | 任意の Microsoft 技術向けにカスタムスキルを自動生成するメタスキル | 新しい Azure ライブラリ等に特化したスキルを作りたいとき |

Claude Code へのインストール:

```
/plugin install microsoft-docs@claude-plugins-official
```

これで MCP サーバー本体 + 上記スキル一式が入る。**「Microsoft Learn を効率よく検索するスキルを作りたい」という目的に対して、まずこの公式プラグインを試すのが最短ルート**。自作するなら、この2スキルの設計(クエリの具体性を上げるコツ、search→fetch の使い分け基準、CLI フォールバック明記など)がそのまま参考になる。

- `microsoft-docs` SKILL.md: https://github.com/MicrosoftDocs/mcp/blob/main/skills/microsoft-docs/SKILL.md
- `microsoft-code-reference` SKILL.md: https://github.com/MicrosoftDocs/mcp/blob/main/skills/microsoft-code-reference/SKILL.md

いずれも `context: fork` が指定されており、探索的な調査でメインの会話コンテキストを汚さない設計になっている点は自作スキルでも踏襲する価値がある。
