# aim — シンプルなモデル呼び出しCLIツール

**関連スキル: `.claude\skills\aim-cli`**

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
```

### オプション

| オプション      | 必須 | 説明                                                                             |
| --------------- | ---- | -------------------------------------------------------------------------------- |
| `--model`       | ○    | 利用するモデルの略記（下記「利用可能なモデル」参照。`--list-models` で一覧表示） |
| `--prompt`      | △    | プロンプト文字列。省略時は標準入力から読み込む（両方とも無ければエラー）         |
| `--list-models` | -    | 利用可能なモデルの一覧（略記と実際のモデルID）を表示して終了する                 |

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
  "generation_id": "gen-1783603352-zXMyzMZpyjJ88CJF5wwD"
}
```

- `cost` / `*_tokens` / `generation_id` は OpenRouter レスポンスの `usage` / `id` フィールドからそのまま転記（追加のAPI呼び出しは発生しない）
- 応答本文（completion）はログに含めない
- `logs/calls.jsonl` はプロンプト本文を含み得るため Git管理対象外（`.gitignore` 参照）。ディレクトリ自体は `.gitkeep` で追跡

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
