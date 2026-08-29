---
name: aim-cli
description: OpenRouter経由でAIモデルを単発呼び出しする`aim` CLIツールの使い方を説明する。プロンプトをAIモデルに投げて応答を得たい、利用可能なモデル一覧を確認したい、タスクの難易度に応じてどのモデルを使うか選定したい場合に使う。
# 前提条件: `aim`コマンドがPATH上にインストール済み（`uv tool install --editable tools/aim`）であり、OPENROUTER_API_KEYが設定済みであること。このスキルはインストール・セットアップは一切行わない
# このスキルの設計意図・前提条件の背景は同階層のREADME.md参照（人間のメンテナ向け）
meta:
  tag: []
  requires_repo_tools: aim
  requires_env: OPENROUTER_API_KEY
  dependencies: none
  requires_install: uv tool install --editable tools/aim
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.1
---

# aim CLI の使い方

`aim`はエージェント機能を持たない、AIモデルへの単発呼び出し専用CLI。system プロンプトやマルチターンは扱わず、ユーザーメッセージ1件を投げて応答テキストのみを標準出力に返す。

## 前提条件

- `aim`コマンドが既にインストールされ、PATH上で実行可能であること
- `OPENROUTER_API_KEY`が環境変数または`tools/aim/.env`で設定済みであること
- 未インストール・未設定の場合はこのスキルでは対処しない。エラーが出た場合はユーザーに`tools/aim/README.md`のセットアップ手順を案内する

## モデル選択の方針

`--model`には以下のいずれかを指定する（値は固定enum）。

| 略記           | 実際のモデルID             | 使いどころ                                                                       |
| -------------- | -------------------------- | -------------------------------------------------------------------------------- |
| `minimax-m3`   | `minimax/minimax-m3`       | **デフォルト**。特に理由がなければこれを使う                                     |
| `gpt-oss-120b` | `openai/gpt-oss-120b:free` | 非常に簡単で精度が求められないタスク（雑な下書き、定型的な短い変換など）。無料枠 |
| `glm-5.2`      | `z-ai/glm-5.2`             | `minimax-m3`では力不足な、より高い精度・推論力が必要なタスク                     |
| `gpt-5.6-luna` | `openai/gpt-5.6-luna`      | 同上。特に高精度が求められる場合のエスカレーション先                             |

判断基準:

1. まず`minimax-m3`を基本線とする
2. タスクが単純すぎて精度を求められない場合は`gpt-oss-120b`に下げてコストを節約する
3. `minimax-m3`の応答が不十分・タスクが複雑な推論を要する場合は`glm-5.2`や`gpt-5.6-luna`にエスカレーションする

## 使い方

```bash
# 引数でプロンプトを渡す
aim --model minimax-m3 --prompt "フランスの首都は？"

# 標準入力からプロンプトを渡す（--prompt省略時はstdinを読む）
echo "フランスの首都は？" | aim --model minimax-m3
cat prompt.txt | aim --model gpt-5.6-luna

# 利用可能なモデル一覧を表示
aim --list-models

# Web Search/Web Fetch を有効にして呼び出す
aim --model minimax-m3 --web --prompt "2026年8月時点の最新ニュースは？"
```

| オプション      | 必須 | 説明                                                                                                  |
| --------------- | ---- | ----------------------------------------------------------------------------------------------------- |
| `--model`       | ○    | 利用するモデルの略記（上表参照。`--list-models`で一覧表示）                                           |
| `--prompt`      | △    | プロンプト文字列。省略時は標準入力から読み込む（両方とも無ければエラー）                              |
| `--list-models` | -    | 利用可能なモデルの一覧（略記と実際のモデルID）を表示して終了する                                      |
| `--web`         | -    | Web Search/Web Fetch（OpenRouter Server Tools）を有効にする（モデルが必要と判断した場合のみ呼ばれる） |

`--web`はツールを使えるようにするだけで、実際に呼ぶかはモデル依存（呼ばない場合もある）。使わせたい場合はプロンプト中で明示的にWeb検索を指示すると成功率が上がる。

標準出力にはモデルの応答テキストのみが出る（パイプで後続処理しやすい）。system プロンプトやマルチターンなど、エージェント的な機能は扱わない。

## ログ

呼び出しごとに`tools/aim/logs/<trace.tool>/<YYYY-MM-DD>.jsonl`（JSON Lines）へ1行追記される。`trace.tool`（`aim-cli`/`aim-ask`/`aim-summarize`等。無ければ`unknown`）でフォルダ分けし、日付でファイル分割することで1ファイルへの際限ない肥大化を防いでいる。CLIのソースディレクトリ基準の絶対パスを使うため、実行時のカレントディレクトリには依存しない。`cost`・`*_tokens`・`generation_id`はOpenRouterレスポンスの`usage`/`id`フィールドからそのまま転記される。応答本文（completion）はログに含めない。

各呼び出しには`trace.trace_id`（32桁hexのOTel準拠trace id）が自動付与される。OpenRouterのGrafana Cloud連携（Broadcast機能、任意設定）を有効化している場合、このtrace_idがGrafana Cloud側のTrace IDと一致するため、ログの`trace.trace_id`をGrafana CloudのTempoで検索すれば対応するトレースを特定できる（詳細は`tools/aim/README.md`の「Grafana Cloudへのログ配信」参照）。

## エラー時の挙動

APIキー未設定・モデルID誤り・OpenRouter側エラー（401/402/429など）が発生した場合、エラーメッセージを標準エラー出力に表示し、非ゼロで終了する。
