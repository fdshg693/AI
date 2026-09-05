# model-select — OpenRouterモデル選定ツール

**関連スキル: `claude-plugins/topics/skills/openrouter-docs/SKILL.md`（特に[references/models-pricing-benchmarks.md](../../claude-plugins/topics/skills/openrouter-docs/references/models-pricing-benchmarks.md)）**

OpenRouterの[Models API](https://openrouter.ai/api/v1/models)から取得したArtificial Analysisベンチマーク（`coding_index`）と価格を判断材料に、OpenAI/Anthropic/Google/Z.ai/MiniMax/xAI/Moonshot AI/DeepSeek系列モデルの選択を行いやすくするCLIツール。実行するたびにOpenRouter APIをライブ取得し（キャッシュ無し）、結果を自己完結HTML（サーバー・外部JS/CSS取得不要）として出力する。ランク分けの閾値・bucketステップ幅はHTML上でインタラクティブに変更できる。

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

Python側（生データ取得）とHTML側（埋め込みJSでの動的計算）で責務が分かれている。

**Python側（`model-select`実行時に確定する部分）**

1. **スコープ**: `id`が`openai/`・`anthropic/`・`google/`・`z-ai/`・`minimax/`・`x-ai/`・`moonshotai/`・`deepseek/`のいずれかで始まるモデルのみ（`model_authors`クエリで絞り込み）。`id`に`:`を含むvariant（`:free`/`:batch`/`:thinking`等）と、`benchmarks.artificial_analysis.coding_index`を持たないモデルは除外する。
2. **足切り**: `coding_index`が50未満のモデルは、OpenRouter APIへの`min_coding_index`クエリ（転送量削減）と`scope.py`側のフィルタ（安全網）の二重で除外する。この50という下限はHTML側の閾値入力でも下回れない。
3. **価格**: 「入力重視（`prompt`価格）」「出力重視（`completion`価格）」の2軸それぞれについて、`pricing`のベース値と`pricing.overrides[]`（コンテキスト長閾値等による割増価格）の中の最大値を採用する（安全側=最悪ケースでの比較）。マルチプロバイダ間の価格差（`/endpoints` API）は考慮しない。

**HTML側（埋め込みJSがブラウザ上で動的に再計算する部分）**

4. **ランク分け**: `coding_index`の下限（閾値、初期値65・最小50）とbucketステップ幅（初期値3）を数値入力で変更でき、変更のたびに半開区間（`[閾値, 閾値+step)`, ...）でbucket分けし直す。
5. **Pareto フィルタ**: 同じbucket内で「価格・ベンチマーク双方において自分以上に優れる他モデル」が存在するモデルを除外し、Pareto frontier上のモデルだけを残す。入力重視・出力重視それぞれ独立に判定する。

モデルが0件のbucketは見出しごと省略する。各セクション冒頭にスコープ内の対象モデル総数（ランク分け前）を表示するので、最終的な表示件数が少ない理由はそこで確認できる。

## 既知の制約

- キャッシュを持たず毎回ライブ取得するため、レート制限に頻繁に触れる場合はAPIキー対応を追加検討する。
- 生成HTMLは外部CDNからのJS/CSS読み込みを行わない完全インライン構成（サーバー・外部JS/CSS取得不要の自己完結）。
- `coding_index < 50`のモデルはPython側取得段階で恒久的に除外されており、HTML側の閾値入力を下げても復活しない。
- ランク分け・Pareto判定ロジックはHTML埋め込みJSのみに存在し、Python側の自動テストは無い。動作確認は`model-select`実行後にブラウザで`output/report.html`を開き、閾値・ステップ入力を変えて手動確認する。

## ファイル構成

```text
tools/model-select/
├── README.md              # 本ファイル
├── AGENTS.md / CLAUDE.md  # @./README.md インクルードのみ
├── pyproject.toml          # `model-select` コンソールコマンドのパッケージング（jinja2依存を含む）
├── .gitignore               # output/*.html を無視（.gitkeepは追跡）
├── model_select/
│   ├── __init__.py
│   ├── fetch.py             # OpenRouter Models API呼び出し（model_authors絞り込み・min_coding_index）
│   ├── scope.py              # variant除外 + coding_index必須・下限フィルタ
│   ├── pricing.py             # pricingベース値とoverridesの最大値算出
│   ├── render.py               # Jinja2テンプレートへのレンダリング呼び出し
│   ├── templates/
│   │   └── report.html.jinja    # ページ全体のHTML/CSS + 埋め込みJSON + インタラクティブJS（bucket分け・Pareto最適フィルタ）
│   └── cli.py                     # エントリポイント（main）
├── tests/
│   ├── test_scope.py
│   └── test_pricing.py
└── output/
    └── report.html            # 実行のたびに上書き生成（gitignore対象）
```
