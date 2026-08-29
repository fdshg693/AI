# aim — シンプルなモデル呼び出しCLIツール

- **関連スキル**:
  - `claude-plugins\my-tools\skills\aim-cli\SKILL.md`
  - `claude-plugins\topics\skills\openrouter-docs\SKILL.md`

- エージェント機能は扱わず、AIモデルの単発呼び出しに集中したCLIツール
- 複数プロバイダに対応するため [OpenRouter](https://openrouter.ai/) の Python SDK（`openrouter`）を使う

## インストール

グローバルCLIとして使う場合は `uv tool install --editable`（`pip install -e` の代替）でエディタブルインストールする。リポジトリルートから実行可能。

```bash
uv tool install --editable tools/aim
```

インストール後は `aim` コマンドが PATH 上でどこからでも使える。

## セットアップ（APIキー）

以下のいずれかで `OPENROUTER_API_KEY` を指定する（環境変数が優先）。

1. 環境変数 `OPENROUTER_API_KEY`
2. `tools/aim/.env`（`.env.example` をコピーして値を設定。`aim` 実行時のカレントディレクトリに依存せず、常にこのファイルを参照する）

```bash
cp tools/aim/.env.example tools/aim/.env
# .env を編集して OPENROUTER_API_KEY=sk-or-... を設定
```

## 使い方

```bash
# 引数でプロンプトを渡す
aim --model gpt-oss-120b --prompt "フランスの首都は？"

# 標準入力からプロンプトを渡す（--prompt 省略時は stdin を読む）
echo "フランスの首都は？" | aim --model gpt-oss-120b
cat prompt.txt | aim --model gpt-5.6-luna

# 利用可能なモデル一覧を表示
aim --list-models

# Web Search/Web Fetch（OpenRouter Server Tools）を有効にして呼び出す
aim --model minimax-m3 --web --prompt "2026年8月時点の最新ニュースは？"
```

### オプション

| オプション      | 必須 | 説明                                                                                                  |
| --------------- | ---- | ----------------------------------------------------------------------------------------------------- |
| `--model`       | ○    | 利用するモデルの略記（下記「利用可能なモデル」参照。`--list-models` で一覧表示）                      |
| `--prompt`      | △    | プロンプト文字列。省略時は標準入力から読み込む（両方とも無ければエラー）                              |
| `--list-models` | -    | 利用可能なモデルの一覧（略記と実際のモデルID）を表示して終了する                                      |
| `--web`         | -    | Web Search/Web Fetch（OpenRouter Server Tools）を有効にする（モデルが必要と判断した場合のみ呼ばれる） |

### 利用可能なモデル

`--model` に指定できる値は以下のみ（enumで固定）。略記は元のモデルIDが推測できる形にしている。

| 略記（`--model` に指定する値） | 実際のモデルID             |
| ------------------------------ | -------------------------- |
| `gpt-oss-120b`                 | `openai/gpt-oss-120b:free` |
| `minimax-m3`                   | `minimax/minimax-m3`       |
| `glm-5.2`                      | `z-ai/glm-5.2`             |
| `gpt-5.6-luna`                 | `openai/gpt-5.6-luna`      |

- system プロンプトやマルチターンなど、エージェント的な機能は扱わない（単発の user メッセージ 1件のみ）
- 標準出力にはモデルの応答テキストのみを出力する（パイプで後続処理しやすい）

### Web Search / Web Fetch（`--web`）

`--web`を付けると、OpenRouterのServer Tools（`openrouter:web_search`・`openrouter:web_fetch`）がそのリクエストで使えるようになる。あくまでモデルに「使える状態」を渡すだけで、実際に呼ぶかどうか（0回か複数回か）はモデル自身の判断。Server Toolsの実行はOpenRouter側でリクエスト/レスポンス1往復の中に収まるため、この CLI の「プロンプト1件→応答テキスト1件」という単発設計は変わらない。

- 付けない場合は従来通り（ツール定義は送らない）
- 付けた場合、ツール定義がリクエストに追加される分、使わなかったとしてもprompt tokens・costがわずかに増える
- モデルによっては関連するプロンプトでも検索を呼ばないことがある（`minimax-m3`で検証時、最新情報が必要なプロンプトでも`--web`だけでは検索が呼ばれないケースを確認済み）。使わせたい場合はプロンプト内で明示的にWeb検索の利用を指示すると成功率が上がる
- ログ（`calls.jsonl`）にツール使用有無を記録するフィールドは無い。Server Tools分のコストは既存の`cost`フィールド（`usage`由来）に含まれる

## ログ

呼び出しごとに `tools/aim/logs/calls.jsonl`（JSON Lines）へ1行追記される。CLIのソースディレクトリ基準の絶対パスを使うため、実行時のカレントディレクトリには依存しない。

```json
{
  "timestamp": "2026-07-09T22:22:34+09:00",
  "model": "minimax/minimax-m3",
  "prompt": "フランスの首都は？",
  "cost": 8.85e-6,
  "prompt_tokens": 15,
  "completion_tokens": 11,
  "total_tokens": 26,
  "generation_id": "gen-1783603352-zXMyzMZpyjJ88CJF5wwD",
  "user": null,
  "session_id": null,
  "trace": { "tool": "aim-cli" }
}
```

- `cost` / `*_tokens` / `generation_id` は OpenRouter レスポンスの `usage` / `id` フィールドからそのまま転記（追加のAPI呼び出しは発生しない）
- 応答本文（completion）はログに含めない
- `logs/calls.jsonl` はプロンプト本文を含み得るため Git管理対象外（`.gitignore` 参照）。ディレクトリ自体は `.gitkeep` で追跡
- `call()`/`call_async()` は呼び出し元が `user`/`session_id`/`trace` を渡せる（いずれも省略時は `None`）。`trace` はOpenRouterのSDKの `trace`（`trace_id`/`trace_name`/`span_name`/`generation_name`/`parent_span_id`の既知キー + 任意の追加キーを持つdict）にそのまま渡され、Grafana Cloudへのブロードキャスト設定時にはトレースのカスタム属性としても反映される（詳細は`claude-plugins/topics/skills/openrouter-docs`スキルの`references/observability.md`参照）
- `aim` コマンドを直接実行した場合は常に `trace: {"tool": "aim-cli"}` が記録される。これにより、`aim`直接利用と`aim-ask`/`aim-summarize`経由の利用（それぞれ`trace.tool`が`"aim-ask"`/`"aim-summarize"`）をログ上で区別できる

## Grafana Cloudへのログ配信（任意）

OpenRouterのBroadcast機能を使うと、`aim`経由の呼び出し（および`aim-ask`/`aim-summarize`経由の呼び出し）をGrafana Cloud（OTLP/Tempoトレース）にも並行して送信できる。ローカルの`logs/calls.jsonl`は今まで通り残るため、これは二重化であり置き換えではない。

- 設定はOpenRouterダッシュボード（[`https://openrouter.ai/settings/observability`](https://openrouter.ai/settings/observability)）での手動設定のみ。このCLI/リポジトリ側に自動設定コードは持たない（Broadcast設定にはManagement API Keyという別種の強い権限を持つキーが必要になるため）
- 設定手順・カスタムメタデータのマッピング（`user`→`user.id`、`session_id`→`session.id`、`trace`の各キー→`trace.metadata.*`等）・TraceQLクエリ例の詳細は `claude-plugins/topics/skills/openrouter-docs` スキルの `references/observability.md` を参照

## エラー時の挙動

APIキー未設定・モデルID誤り・OpenRouter側エラー（401/402/429など）が発生した場合、エラーメッセージを標準エラー出力に表示し、非ゼロで終了する。

## ファイル構成

```
tools/aim/
├── README.md       # 本ファイル
├── PLAN.md          # 実装プラン
├── pyproject.toml    # パッケージ定義 + console script (aim)
├── aim_cli.py         # CLI本体
├── .env.example
├── .env               # gitignore対象
├── .gitignore
└── logs/
    ├── .gitkeep
    └── calls.jsonl    # gitignore対象
```
