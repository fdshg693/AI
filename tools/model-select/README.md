# model-select — OpenRouterモデル選定ツール

**関連スキル: `claude-plugins/topics/skills/openrouter-docs/SKILL.md`（特に[references/models-pricing-benchmarks.md](../../claude-plugins/topics/skills/openrouter-docs/references/models-pricing-benchmarks.md)）**

OpenRouterの[Models API](https://openrouter.ai/api/v1/models)から取得したArtificial Analysisベンチマーク（`coding_index`）と価格を判断材料に、GPT/Claude/Gemini系列モデルの選択を行いやすくするCLIツール。実行するたびにOpenRouter APIをライブ取得し（キャッシュ無し）、結果を自己完結HTML（サーバー・JS不要）として出力する。

## セットアップ

認証不要。APIキー等の事前設定は無い。

## インストール

グローバルCLIとして使う場合は `uv tool install --editable`（`pip install -e` の代替）でエディタブルインストールする。リポジトリルートから実行可能。

```bash
uv tool install --editable tools/model-select
```

インストール後は `model-select` コマンドが PATH 上でどこからでも使える。

## 使い方

```bash
model-select
```

実行すると `tools/model-select/output/report.html` に結果を書き出し（実行のたびに上書き）、書き出した絶対パスを標準出力に表示する。生成された `report.html` をブラウザで開いて見る。

## 判定ロジック

1. **スコープ**: `id`が`openai/`・`anthropic/`・`google/`のいずれかで始まるモデルのみ（`model_authors`クエリで絞り込み）。`id`に`:`を含むvariant（`:free`/`:batch`/`:thinking`等）と、`benchmarks.artificial_analysis.coding_index`を持たないモデルは除外する。
2. **価格**: 「入力重視（`prompt`価格）」「出力重視（`completion`価格）」の2軸で完全に分けて比較する（1モデルが両方の一覧に別々に登場しうる）。各軸の価格は、`pricing`のベース値と`pricing.overrides[]`（コンテキスト長閾値等による割増価格）の中の最大値を採用する（安全側=最悪ケースでの比較）。マルチプロバイダ間の価格差（`/endpoints` API）は考慮しない。
3. **ランク分け**: `coding_index`が65以上のモデルを対象に、3刻みの半開区間（`[65,68)`, `[68,71)`, ...）でbucket分けする。65未満・フィールド自体が無いモデルは対象外。
4. **Pareto フィルタ**: 同じbucket内で「価格・ベンチマーク双方において自分以上に優れる他モデル」が存在するモデルを除外し、Pareto frontier上のモデルだけを残す。入力重視・出力重視それぞれ独立に判定する。

モデルが0件のbucketは見出しごと省略する。各セクション冒頭にスコープ内の対象モデル総数（ランク分け前）を表示するので、最終的な表示件数が少ない理由はそこで確認できる。

## 既知の制約

- キャッシュを持たず毎回ライブ取得するため、レート制限に頻繁に触れる場合はAPIキー対応を追加検討する。
- ランク分け・Pareto判定ロジック（`rank.py`/`dominance.py`）は指標名・価格キーを引数として受け取る汎用関数であり、`coding_index`固有のロジックではない。将来ベンチマーク種別・モデル系列が増えても`cli.py`の呼び出し側を変えるだけで対応しやすい。

## ファイル構成

```text
tools/model-select/
├── README.md              # 本ファイル
├── AGENTS.md / CLAUDE.md  # @./README.md インクルードのみ
├── pyproject.toml          # `model-select` コンソールコマンドのパッケージング
├── .gitignore               # output/*.html を無視（.gitkeepは追跡）
├── model_select/
│   ├── __init__.py
│   ├── fetch.py             # OpenRouter Models API呼び出し（model_authors絞り込み）
│   ├── scope.py              # variant除外 + coding_index必須のフィルタ
│   ├── pricing.py             # pricingベース値とoverridesの最大値算出
│   ├── rank.py                 # 指標に基づくbucket分類（汎用パラメータ化）
│   ├── dominance.py             # bucket内Paretoフィルタ（汎用パラメータ化）
│   ├── render.py                 # 自己完結HTML組み立て
│   └── cli.py                     # エントリポイント（main）
├── tests/
│   ├── test_scope.py
│   ├── test_pricing.py
│   └── test_rank_dominance.py
└── output/
    └── report.html            # 実行のたびに上書き生成（gitignore対象）
```
