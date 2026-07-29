---
name: claude-agent-sdk
description: Use when building, reviewing, or troubleshooting Python applications that use Anthropic's Claude Agent SDK, including agent loops, sessions, tools, MCP, permissions, hooks, streaming, structured output, and deployment. Use the official Claude Code documentation cache for API details that may have changed.
# Python版のClaude Agent SDKだけを対象にする。別言語のSDK、API名、コード例は扱わない。
# 公式ドキュメントの取得・抽出は claude-code-docs スキルに依存する。
meta:
  requires_repo_tools: none
  requires_env: ANTHROPIC_API_KEY
  dependencies: claude-agent-sdk, pydantic
  requires_install: pip install claude-agent-sdk
  requires_hooks: none
  requires_skills: claude-code-docs
  status: stable
  description: no description
  version: 1.0.0
---

# Python版 Claude Agent SDK

Claude Codeをライブラリとして組み込むPythonアプリケーションの設計・実装・レビュー・トラブルシューティングに使う。SDKのAPIや挙動は変わり得るため、記憶だけで回答せず、必ずリポジトリ内の `claude-code-docs` スキルが管理する公式ドキュメントを確認する。

## 対象範囲

- パッケージ名は `claude-agent-sdk`、Pythonからのimportは `claude_agent_sdk`。
- Python 3.10以上を前提にする。プロジェクトの仮想環境または `uv` を使う。
- 認証、インストール、エージェントループ、組み込みツール、セッション、ストリーミング、権限、フック、MCP、カスタムツール、サブエージェント、Agent Skills、構造化出力、コスト・運用・デプロイを扱う。
- 対象外の言語のSDKのAPI名や書き方を混ぜない。公式ページに複数言語の例があってもPythonの例とPythonリファレンスだけを読む。

## 公式情報を確認する手順

1. `claude-code-docs` スキルを使い、公式ドキュメントの取得スクリプトを実行する。通常は次のコマンドでキャッシュを更新・確認できる。

   ```text
   python ${CLAUDE_PROJECT_DIR}/.claude/skills/claude-code-docs/download_claude_code_reference.py
   ```

2. `${CLAUDE_PROJECT_DIR}/.claude/skills/claude-code-docs/output/llms.txt` で `agent-sdk/` のページを探す。
3. 本文が必要なページだけを、既存スキルの抽出スクリプトで取り出す。

   ```text
   python ${CLAUDE_PROJECT_DIR}/.claude/skills/claude-code-docs/extract_doc_section.py agent-sdk/python agent-sdk/quickstart
   ```

4. 回答・実装判断に使ったページの `Source:` URLを示す。キャッシュに該当情報がなければ、その不足を明示して公式サイトの該当ページを確認する。

質問の主題に応じた参照先は次の通り。ページの内容を丸ごと読み込まず、必要なページだけ抽出する。

| 主題                                         | 公式ページのslug                                                                                         |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 全体像・セットアップ                         | `agent-sdk/overview`, `agent-sdk/quickstart`                                                             |
| Python API・型・例外                         | `agent-sdk/python`                                                                                       |
| ループ・メッセージの意味                     | `agent-sdk/agent-loop`                                                                                   |
| 一回限りの処理・継続対話                     | `agent-sdk/sessions`, `agent-sdk/streaming-vs-single-mode`                                               |
| リアルタイム出力                             | `agent-sdk/streaming-output`                                                                             |
| 権限・許可・拒否                             | `agent-sdk/permissions`                                                                                  |
| コールバックフック                           | `agent-sdk/hooks`                                                                                        |
| 自作ツール                                   | `agent-sdk/custom-tools`                                                                                 |
| 外部MCP                                      | `agent-sdk/mcp`, `agent-sdk/tool-search`                                                                 |
| Agent Skills・CLAUDE.md等の読み込み          | `agent-sdk/skills`, `agent-sdk/claude-code-features`                                                     |
| サブエージェント・構造化出力                 | `agent-sdk/subagents`, `agent-sdk/structured-outputs`                                                    |
| セッション保存・復元・ファイル巻き戻し       | `agent-sdk/session-storage`, `agent-sdk/file-checkpointing`                                              |
| コスト・監視・ホスティング                   | `agent-sdk/cost-tracking`, `agent-sdk/observability`, `agent-sdk/hosting`, `agent-sdk/secure-deployment` |
| プラグイン・スラッシュコマンド・ユーザー入力 | `agent-sdk/plugins`, `agent-sdk/slash-commands`, `agent-sdk/user-input`                                  |

## 最初に行う設計判断

### `query()` と `ClaudeSDKClient`

| 要件                                             | 選ぶAPI                             |
| ------------------------------------------------ | ----------------------------------- |
| 独立した一回限りのタスク、単純な自動化           | `query()`                           |
| 同じ会話で質問を続ける、REPLやチャットUI         | `ClaudeSDKClient`                   |
| 割り込み、動的な入力、画像添付、明示的な接続管理 | `ClaudeSDKClient` + streaming input |
| 最終結果だけ必要な短い処理                       | `query()` の結果メッセージを読む    |

`query()` はデフォルトでは新しいセッションを開始し、非同期イテレータを返す。継続が必要なら `ClaudeAgentOptions` の `continue_conversation` / `resume` を公式リファレンスで確認する。複数ターン・割り込み・入力キューが必要なら、クライアントを `async with` で管理する。

### 最小のエージェントループ

```python
import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def main() -> None:
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep"],
        max_turns=10,
    )

    async for message in query(
        prompt="コードベースのTODOを調べ、要約してください。",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"終了: {message.subtype}")


asyncio.run(main())
```

実装時は、表示用のテキストだけを出すのか、ツール呼び出し・システムメッセージ・最終結果も保存するのかを先に決める。`ResultMessage` の `subtype` とエラー型を捨てると、失敗を成功と誤認しやすい。

## セットアップの既定手順

依存関係をプロジェクトの仮想環境へ入れ、APIキーは実行プロセスの環境変数へ渡す。SDKは `.env` を自動ロードしないため、使う場合はアプリ側で明示的にロードする。

```powershell
py -m venv .venv
.venv/Scripts/Activate.ps1
pip install claude-agent-sdk
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

PowerShellの実行ポリシーで有効化が拒否された場合は、現在のプロセスだけに対する設定を確認してから再実行する。秘密情報をソース、ログ、プロンプト、コミットへ書かない。Bedrock、Vertex、Foundryなどの認証を使う場合は、一般化した推測をせず、公式の該当セットアップページを追加で読む。

## `ClaudeAgentOptions` の使い分け

Pythonではオプション名をsnake_caseで書く。よく使う項目は次の通り。

- `allowed_tools`: 許可確認なしで実行するツール。これだけではツールの利用可能性を限定しない。
- `tools`: Claudeのコンテキストに載せる組み込みツールを限定する。
- `disallowed_tools`: ツール全体を外す、またはツール名・引数に対する拒否ルールを置く。
- `permission_mode`: 既定の許可フローを選ぶ。ファイル変更やコマンド実行を自動承認するモードは、隔離環境など安全性を確認できる場合に限る。
- `can_use_tool`: 動的なユーザー承認・拒否を実装する。自動許可のルールやモードで先に承認された呼び出しは、このコールバックを通らないため、ここだけを安全境界にしない。
- `system_prompt`: 役割や制約を与える。Claude Codeの既定プロンプト、ファイルからの読み込み、追記の可否は公式リファレンスで確認する。
- `cwd`: エージェントが操作する作業ディレクトリ。アプリのカレントディレクトリを暗黙に信頼しない。
- `max_turns`: 無限ループ・想定外のコストを防ぐ上限。
- `mcp_servers`: 外部MCPまたはプロセス内MCPの設定。
- `hooks`: ライフサイクルイベントで監査・検証・制御を行う。
- `output_format`: JSON Schemaで最終出力を構造化する。
- `resume` / `continue_conversation`: 既存セッションを継続する。復元要件は `sessions` を参照する。
- `setting_sources`, `skills`, `agents`: プロジェクト設定・スキル・サブエージェントを読み込む場合に使う。暗黙に読み込まれる前提にせず、公式ページで現在の既定値を確認する。

「使えるツール」と「確認なしで使えるツール」と「明示的に禁止するツール」を混同しない。削除、ネットワーク、秘密情報、デプロイに関係する操作は、最小権限の `tools` / `allowed_tools` / `disallowed_tools` と承認フローを組み合わせる。

## ストリーミングと入力

出力をリアルタイム表示する場合は `async for` でメッセージを処理する。複数入力を順番に送り、途中で割り込み、画像を添付し、ユーザー承認を扱う必要がある場合は、ストリーミング入力と `ClaudeSDKClient` を選ぶ。入力ジェネレーター内の例外はセッションが停止・ハングしたように見えることがあるため、ファイル読み込みや外部I/Oをジェネレーター内で行う場合は例外を記録し、入力を検証する。

```python
import asyncio

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, ResultMessage


async def main() -> None:
    async with ClaudeSDKClient(
        ClaudeAgentOptions(allowed_tools=["Read", "Grep"], max_turns=10)
    ) as client:
        await client.query("認証処理の構造を調べてください。")
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(message.result)

        await client.query("見つかったリスクを優先度順に整理してください。")
        async for message in client.receive_response():
            if isinstance(message, ResultMessage):
                print(message.result)


asyncio.run(main())
```

`interrupt()` の後は、割り込み対象の `ResultMessage` を含む残りのメッセージを `receive_response()` で読み切ってから次のクエリを送る。そうしないと、新しい要求ではなく古い応答を読む可能性がある。

## 自作ツールとMCP

アプリ内のPython関数をClaudeから呼ばせるだけなら、`@tool` と `create_sdk_mcp_server()` のインプロセスMCPを使う。ツール名はMCP公開時に `mcp__<server>__<tool>` になるため、必要ならその完全名を `allowed_tools` に指定する。

```python
from typing import Any

from claude_agent_sdk import ClaudeAgentOptions, create_sdk_mcp_server, tool


@tool("lookup_order", "注文番号から注文情報を取得する", {"order_id": str})
async def lookup_order(args: dict[str, Any]) -> dict[str, Any]:
    order_id = args["order_id"]
    # 実運用では認証、入力検証、タイムアウト、監査ログを実装する。
    return {"content": [{"type": "text", "text": f"order={order_id}"}]}


order_server = create_sdk_mcp_server(
    name="orders",
    version="1.0.0",
    tools=[lookup_order],
)

options = ClaudeAgentOptions(
    mcp_servers={"orders": order_server},
    allowed_tools=["mcp__orders__lookup_order"],
)
```

ツールは自然言語の指示だけで安全になるとは考えず、サーバー側でも認証・認可・入力検証・タイムアウト・レート制限・監査を行う。外部プロセスやHTTPのMCPを接続する場合は、`agent-sdk/mcp` のトランスポート、認証、エラー処理を読む。ツール数が多い場合はツール検索を検討する。

## 構造化出力

アプリケーションが読むデータを返すなら、自由文を正規表現で解析せず、`output_format={"type": "json_schema", "schema": ...}` を使う。PythonではPydanticモデルからJSON Schemaを生成し、結果の `structured_output` を再度モデルで検証する。

```python
import asyncio

from pydantic import BaseModel
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


class Finding(BaseModel):
    title: str
    severity: str


async def main() -> None:
    options = ClaudeAgentOptions(
        output_format={
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "findings": {
                        "type": "array",
                        "items": Finding.model_json_schema(),
                    }
                },
                "required": ["findings"],
            },
        }
    )
    async for message in query(
        prompt="コードの問題を調査し、構造化された結果を返してください。",
        options=options,
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            print(message.structured_output)


asyncio.run(main())
```

JSON Schemaの形、検証失敗時のリトライ上限、`ResultMessage` の成功・エラー条件は `agent-sdk/structured-outputs` で確認する。スキーマが大きい場合やPydanticのネストを使う場合は、公式例を優先する。

## フック・権限・安全性

- `PreToolUse` はツール実行前の検証・拒否、`PostToolUse` は監査や結果処理、`Stop` / `SessionEnd` は後処理に使う。イベント名・入力型・返却型は `agent-sdk/hooks` とPythonリファレンスから確認する。
- フックのタイムアウト、例外、`additionalContext`、allow/deny/deferの意味を推測しない。特にポリシーゲートにするフックは失敗時の扱いをテストする。
- `bypassPermissions` のような広い自動承認を本番や未隔離のワークスペースで使わない。許可確認の省略は安全境界ではない。
- `cwd`、環境変数、MCPの資格情報、ファイルシステム、ネットワークをテナントごとに分離する。外部入力をそのままプロンプト・シェル・パス・MCP引数へ連結しない。
- 本番化ではサブプロセス、コンテナやサンドボックス、セッション永続化、観測性、キャンセル、リソース上限、秘密管理を `hosting` と `secure-deployment` で確認する。

## セッションと運用

セッションIDをユーザーIDや独自DBのIDと同一視しない。継続・resume・fork・外部保存のどれが必要かを先に決め、`agent-sdk/sessions` と `agent-sdk/session-storage` の制約を確認する。ファイルの巻き戻しが必要なら `enable_file_checkpointing=True` と `rewind_files()` の関係を `agent-sdk/file-checkpointing` で確認する。

コストや障害を見えるようにするため、少なくともセッションID、結果subtype、turn数、入力・出力トークン、ツール実行時間、エラー種別を、秘密情報とプロンプト本文を不用意に記録しない形で監査する。トークン使用量・キャッシュ・OpenTelemetryの現在のフィールドは公式ページを参照する。

## トラブルシューティング

1. `ModuleNotFoundError` は、SDKを入れた仮想環境と実行に使ったPythonが同じか、`python -m pip show claude-agent-sdk` で確認する。
2. APIキーエラーは、SDKを起動したプロセスの環境変数を確認する。`.env` の自動ロードを前提にしない。
3. ツールが見えない場合は、`tools`（利用可能性）、`allowed_tools`（自動承認）、`disallowed_tools`（禁止）、MCP公開名の4つを分けて確認する。
4. 応答が止まる場合は、入力ジェネレーターの例外、`max_turns`、権限待ち、MCP接続、タイムアウト、プロセスログを順に確認する。
5. 構造化出力が失敗する場合は、JSON Schemaの型・必須項目・draft-07互換性と、結果subtypeおよび例外を確認する。
6. 仕様が曖昧またはキャッシュにない場合は、Pythonリファレンスと該当機能ページを再抽出し、推測でAPI名や既定値を補わない。

## 回答・実装時の完了条件

- Pythonのimport、snake_caseのオプション名、非同期処理の形が一貫している。
- `query()` と `ClaudeSDKClient` の選択理由、ツール権限、セッション境界、失敗時の扱いが明示されている。
- 公式キャッシュで確認したページの `Source:` URLを示している。
- 外部I/O、コマンド実行、ファイル編集、秘密情報を伴う例には、最小権限・入力検証・タイムアウト・監査の考慮がある。
- 公式ドキュメントにない仕様を断定していない。
