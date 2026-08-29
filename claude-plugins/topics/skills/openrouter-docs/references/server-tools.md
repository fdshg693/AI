# Server Tools

Source: `guides/features/server-tools`（Beta、API・挙動は変わりうる）

OpenRouterがサーバー側で実行するツール群。モデルが「呼ぶかどうか・何回呼ぶか」を判断し、実行はOpenRouterが行う点でPluginsやユーザー定義Tool Callingと異なる。

|                  | Server Tools           | Plugins             | User-Defined Tools     |
| ---------------- | ---------------------- | ------------------- | ---------------------- |
| 呼ぶか決めるのは | モデル                 | 常に実行            | モデル                 |
| 実行するのは     | OpenRouter             | OpenRouter          | 自アプリ               |
| 呼び出し回数     | リクエストあたり0〜N回 | リクエストあたり1回 | リクエストあたり0〜N回 |
| 指定方法         | `tools`配列            | `plugins`配列       | `tools`配列            |
| type prefix      | `openrouter:*`         | N/A                 | `function`             |

## 利用可能なServer Tools

| Tool                                                                                         | type                          | 概要                                                                                                                        |
| -------------------------------------------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| [Web Search](https://openrouter.ai/docs/guides/features/server-tools/web-search)             | `openrouter:web_search`       | Web検索でリアルタイム情報を取得                                                                                             |
| [Datetime](https://openrouter.ai/docs/guides/features/server-tools/datetime)                 | `openrouter:datetime`         | 現在日時を取得                                                                                                              |
| [Image Generation](https://openrouter.ai/docs/guides/features/server-tools/image-generation) | `openrouter:image_generation` | テキストから画像生成                                                                                                        |
| [Web Fetch](https://openrouter.ai/docs/guides/features/server-tools/web-fetch)               | `openrouter:web_fetch`        | URLの内容を取得・抽出                                                                                                       |
| [Apply Patch](https://openrouter.ai/docs/guides/features/server-tools/apply-patch)           | `openrouter:apply_patch`      | V4A diffでファイル編集を提案（Responses API限定）                                                                           |
| [Files](https://openrouter.ai/docs/guides/features/server-tools/files)                       | `openrouter:files`            | Files API経由でワークスペースファイルの読み書き・編集・一覧（詳細は[beta-files-classifiers.md](beta-files-classifiers.md)） |
| [Fusion](https://openrouter.ai/docs/guides/features/server-tools/fusion)                     | `openrouter:fusion`           | 複数モデル＋judgeモデルによる多角的分析                                                                                     |
| [Advisor](https://openrouter.ai/docs/guides/features/server-tools/advisor)                   | `openrouter:advisor`          | 生成途中でより強いモデルに助言を求める                                                                                      |
| [Subagent](https://openrouter.ai/docs/guides/features/server-tools/subagent)                 | `openrouter:subagent`         | 自己完結タスクを小型・高速なモデルに委譲                                                                                    |

## 使い方

`tools`配列に`{"type": "openrouter:web_search"}`のように追加するだけ（ユーザー定義の`function`ツールと同一リクエストで併用可）。使用状況はレスポンスの`usage.server_tool_use`で追跡できる。

```json
{
  "model": "openai/gpt-5.2",
  "messages": [...],
  "tools": [
    { "type": "openrouter:web_search", "parameters": { "max_results": 3 } },
    { "type": "openrouter:datetime" },
    { "type": "function", "function": { "name": "get_stock_price", "...": "..." } }
  ]
}
```

個別ツールの詳細（パラメータ・レスポンス形式）は上表のリンク先を`extract_doc_section.py`で取得すること。
