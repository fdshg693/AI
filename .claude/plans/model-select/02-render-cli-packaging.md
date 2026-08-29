---
type: Plan Step
status: ready
---

# Step 2: HTML生成・CLIエントリポイント・パッケージング

[01-core-pipeline.md](01-core-pipeline.md) の続き。Step1の純粋関数群を組み合わせてCLIとして動かし、結果を自己完結HTMLとして出力できるようにする。`tools/model-select/`をuvワークスペースの1パッケージとして登録するところまでを含む。

## やること

- `render.py`: Step1で作った「入力重視ビュー」「出力重視ビュー」（それぞれ bucket → モデル一覧）を受け取り、2セクション構成の自己完結HTML文字列を組み立てる（サーバー・JS不要、Python側でテーブルHTMLを直接生成）。モデルが0件のbucketは見出しごと出力しない。各セクション冒頭に、スコープ内の対象モデル総数（ランク分け前）を表示し、「なぜ表示件数が少ないか」が分かるようにする。
- `cli.py`: `fetch → scope → rank(coding_index) → dominance(入力軸) / dominance(出力軸) → render → ファイル書き出し` を順に呼び出すエントリポイント。出力先は固定パス`tools/model-select/output/report.html`（実行のたびに上書き）。書き出した絶対パスを標準出力に表示する。
- パッケージ化: `pyproject.toml`（`model-select`コマンドとして`uv tool install --editable`可能にする）、`README.md`/`AGENTS.md`/`CLAUDE.md`、`.gitignore`、`output/.gitkeep`。
- リポジトリルート`pyproject.toml`の`[tool.uv.workspace].members`に`"tools/model-select"`を追加。

## 読むべきファイル・実行推奨Grep

**パッケージ定義・ワークスペース登録のテンプレートとして（優先度: 高）**

- 読む: `tools/aim/pyproject.toml` — `[project.scripts]`でのコマンド登録、`[tool.setuptools] py-modules`の書き方（今回は`packages = ["model_select"]`になる点が異なる。パッケージ内モジュール構成は`tools/aim-use/aim-summarize/pyproject.toml`の方が近い）
- 読む: ルート`pyproject.toml`の`[tool.uv.workspace].members` — 追加箇所と既存の並び順

**READMEの書き方の粒度を揃えるため（優先度: 中）**

- 読む: `tools/aim/README.md` — 「インストール」「使い方」「オプション」「ファイル構成」の節立て。今回は認証不要・キャッシュ無しなので「セットアップ」節は不要（その旨を明記する）
- 読む: `tools/aim/AGENTS.md` / `CLAUDE.md` — `@./README.md`一行インクルードのみの中身をそのまま踏襲する

**HTML生成の落とし穴確認のため（優先度: 中）**

- Grep: `html.escape` — 既存コードでモデル名・ID等の外部由来文字列をHTMLに埋め込む際にエスケープしている前例が無いか確認（無ければ`pricing.py`同様、新規に`html.escape`をそのまま使えばよい）

## 触るファイル

### 新規

- `tools/model-select/model_select/render.py` — HTML組み立て（2セクション: 入力重視/出力重視、各bucket見出し+モデルテーブル、モデル数・生成日時のフッター）
- `tools/model-select/model_select/cli.py` — エントリポイント（`main()`）
- `tools/model-select/pyproject.toml` — `requests`依存、`model-select = model_select.cli:main`
- `tools/model-select/README.md` — 使い方（`uv tool install --editable tools/model-select`→`model-select`実行→`output/report.html`をブラウザで開く）、判定ロジックの要約（スコープ・ランク・Pareto）、関連スキルへのリンク
- `tools/model-select/AGENTS.md` / `tools/model-select/CLAUDE.md` — `@./README.md`のみ
- `tools/model-select/.gitignore` — `output/*.html`を無視（`.gitkeep`は追跡）
- `tools/model-select/output/.gitkeep`

### 変更

- `pyproject.toml`（リポジトリルート）— `[tool.uv.workspace].members`に`"tools/model-select"`を追加

## 決定事項・注意点／落とし穴

| 決定                                                                            | 理由                                                                                                                                                                                      |
| ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 出力ファイル名は固定`output/report.html`（実行のたびに上書き）                  | 「毎回ライブ取得」でスナップショット履歴を残す要件が無いため、タイムスタンプ付きファイル名で溜め続ける複雑さを避ける                                                                      |
| 価格は$/token（OpenRouter API生の単位）から$/M tokensに変換して表示             | 生の値（例: `0.0000025`）はそのままでは比較しづらい。`references/models-pricing-benchmarks.md`内の`min_price`等の慣例（$/M tokens）に合わせる                                             |
| bucket内のモデル表示順は価格の安い順にソートする                                | Pareto frontier上のモデルを安い順に並べると「価格を上げると指標がどう上がるか」がそのまま読み取れ、比較目的に合う                                                                         |
| HTMLはPythonのf文字列で直接組み立て、Jinja2等のテンプレートエンジンは使わない   | テーブル2つを組み立てるだけの規模でテンプレートエンジン導入は過剰。`html.escape`でモデル名等はエスケープする                                                                              |
| `--open`（生成後に既定ブラウザで自動的に開く）等の付加フラグはMVPでは実装しない | 「シンプルな最小限」の要望に対し必須ではない。標準出力にファイルパスを出せば十分。将来必要になれば追加できる                                                                              |
| モデルが0件のbucketは見出しごと省略し、"該当なし"表示もしない                   | ランク幅（3刻み・65以上）に対し対象モデル数が少ない（プラン作成時点のライブ確認で23件程度）ため、空bucketを律儀に表示すると縦に間延びする。件数はセクション冒頭のサマリで分かるようにする |

## 計画との差分（実行時に判明・クリティカル）

（実行前のため、まだ無し）

## ルール更新ポイント

このリポジトリは`AGENTS.md`ベースのルール管理。既存の共有ルールファイルへの追記は無い。`tools/model-select/AGENTS.md`・`CLAUDE.md`は新規ファイルだが、他ツール（例: `tools/aim/AGENTS.md`）と同一の`@./README.md`インクルードのみなので、内容は本ステップの「触るファイル」の説明で足りる（新規ルール本文の設計は不要）。

## 推奨の進め方

- **実行主体**: メインエージェント。Step1の関数群を組み合わせるだけの配線作業であり分割の必要が薄い。
- **TODO化**: 「render.py実装」「cli.py実装+手動での動作確認（実際にOpenRouter APIを叩いてHTMLが生成されるか）」「パッケージング一式（pyproject.toml/README/AGENTS.md等/ワークスペース登録)」の3項目程度に分ける。
- **関連スキル**: 特になし。

---

## 実装後の確認

- `uv tool install --editable tools/model-select`でインストールし、`model-select`コマンドを実行してエラー無く`output/report.html`が生成されることを確認する。
- 生成された`output/report.html`をブラウザで開き、入力重視/出力重視の2セクションにGPT/Claude/Gemini系列のモデルのみが表示され、各bucket内でPareto支配されたモデルが消えていることを目視確認する。
