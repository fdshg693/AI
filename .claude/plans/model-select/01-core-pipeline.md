---
type: Plan Step
status: ready
---

# Step 1: データ取得・スコープ絞り込み・価格算出・ランク分け・Paretoフィルタ

[00-overview.md](00-overview.md) の続き。外部APIを叩く部分とモデル選定ロジック本体（純粋関数）を実装する。まだHTML生成・CLIワイヤリング・パッケージング（`pyproject.toml`等）には触れない（Step2）。

## やること

`tools/model-select/model_select/` 配下に以下5モジュールを実装する。

- `fetch.py` — `GET https://openrouter.ai/api/v1/models?model_authors=openai,anthropic,google` を認証無しで呼び、レスポンスの`data`配列（Modelオブジェクトのリスト）をそのまま返す。ネットワーク例外は握りつぶさずそのまま伝播させる（呼び出し元のcli.pyでもcatchしない — 失敗時はPython標準のtracebackで終了する簡素な挙動でよい）。
- `scope.py` — `id`に`:`を含むモデル（`:free`/`:batch`/`:thinking`等のvariant）を除外し、かつ`benchmarks.artificial_analysis.coding_index`を持つモデルだけを残すフィルタ。author絞り込みは`fetch.py`側の`model_authors`クエリで完結するため、ここではやらない。
- `pricing.py` — 1モデル・1価格フィールド（`prompt`または`completion`）を受け取り、ベース値と`pricing.overrides[]`内の同フィールドの中から最大値を返す汎用関数。$/token → $/M tokens への変換ヘルパーも持つ。
- `rank.py` — `coding_index`（または将来の他指標）を受け取り、最低基準・刻み幅をパラメータとして bucket（半開区間）に分類する汎用関数。
- `dominance.py` — 同一bucket内のモデル集合を受け取り、「価格を最小化・指標を最大化する」Pareto最適でないモデルを除外する汎用関数（メトリック取得・価格取得はどちらも呼び出し側が関数として渡す）。

これらは全て純粋関数（ネットワークI/Oは`fetch.py`のみ）とし、`tests/`でモック無しにテストできるようにする。

## 読むべきファイル・実行推奨Grep

**価格・ベンチマークのフィールド仕様を確認するため（優先度: 高）**

- 読む: [claude-plugins/topics/skills/openrouter-docs/references/models-pricing-benchmarks.md](../../../claude-plugins/topics/skills/openrouter-docs/references/models-pricing-benchmarks.md) — `pricing`/`benchmarks.artificial_analysis`/`overrides`のフィールド定義。特に「Pricing」節と「Benchmarksオブジェクト」節
- 実データ確認（このプラン作成時にWebFetchで確認済み。実装時に価格仕様が変わっていないか不安なら再取得）: `curl https://openrouter.ai/api/v1/model/google/gemini-2.5-pro` — `pricing.overrides`に`min_prompt_tokens: 200000`条件の割増prompt/completion価格が入っている実例

**同種の「薄いREST APIラッパーCLI」の書き方を確認するため（優先度: 中）**

- 読む: `tools/ctx7/pyproject.toml` — `requests`を唯一の外部依存として使う薄いCLIツールの依存定義の書き方
- 読む: `tools/aim-use/aim-summarize/aim_summarize/` 配下（`scanner.py`/`summarizer.py`/`formatter.py`等） — 小さな責務ごとにモジュールを分ける既存の粒度感の参考（今回のモジュール分割もこれに合わせる）

**リポジトリのPythonツール共通の作法を確認するため（優先度: 低）**

- 読む: ルート`pyproject.toml`の`[tool.pytest.ini_options]` — `--import-mode=importlib`が既に設定済みなので、`tests/`配下に`__init__.py`は置かない（他パッケージのテストとモジュール名が衝突しても問題ない設定）

## 触るファイル

### 新規

- `tools/model-select/model_select/__init__.py` — 空でよい（パッケージマーカー）
- `tools/model-select/model_select/fetch.py` — OpenRouter Models API呼び出し（`model_authors`クエリ付き）
- `tools/model-select/model_select/scope.py` — variant（`:`付きid）除外 + coding_index必須のフィルタ
- `tools/model-select/model_select/pricing.py` — ベース値とoverridesの最大値算出
- `tools/model-select/model_select/rank.py` — 指標に基づくbucket分類（最低基準・刻み幅パラメータ化）
- `tools/model-select/model_select/dominance.py` — bucket内Paretoフィルタ
- `tools/model-select/tests/test_scope.py` — `:free`/`:batch`等のvariant除外、coding_index欠落モデルの除外、両条件を満たすモデルが残ることのテスト
- `tools/model-select/tests/test_pricing.py` — overrides無し/有りの両パターン、overrides要素内で一部フィールドが欠けているパターン（例: `input_cache_write`が無い要素）、input/output両フィールドのテスト
- `tools/model-select/tests/test_rank_dominance.py` — bucket境界値（ちょうど65, 68等）のテスト、Pareto除外・非除外の代表ケース（同値タイのケースを含む）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                   | 理由                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pricing.overrides[]`の閾値条件（`min_prompt_tokens`等）は判定せず、フィールドが存在すれば常に比較対象に含めて最大値を取る                             | ユーザー要望は「安全側（最悪ケース）で比較したい」であり、閾値を跨ぐかどうかの動的判定はスコープ外と割り切る。実装をシンプルに保てる                                                                                                               |
| `overrides`に対象フィールド（`prompt`/`completion`）が存在しない要素はその要素をスキップする                                                           | 実データ（`google/gemini-2.5-pro`）でも`overrides`要素は変化するフィールドだけを含み、全フィールドを含むとは限らない                                                                                                                               |
| Paretoフィルタは「価格が同じ以下 かつ 指標が同じ以上」で、少なくとも一方が厳密に優れる場合のみ除外する（両方完全に同値のモデル同士は互いに除外しない） | 厳密支配のみを除外対象にしないと、価格・指標が完全一致する2モデルが両方消えてしまい「対抗馬がいれば削除」の意図（劣っている側を消す）に反する                                                                                                      |
| bucket分類は`coding_index`の生の値で行い、Pareto比較も同じbucket内の生の値同士で行う                                                                   | 要求どおり「そのランクに収まった範囲のモデルの中で」比較するため。bucket境界をまたいだモデル同士（例: 67.9と68.1）は比較しない — これは仕様であり漏れではない                                                                                      |
| `rank.py`/`dominance.py`は指標取得関数・価格取得関数を引数として受け取る形にし、`coding_index`や`prompt`をモジュール内にハードコードしない             | 「将来ベンチマーク・モデルが増えても対応しやすい抽象性」の実現ポイント。ただし呼び出し側（Step2のcli.py）でのconfig化・CLIフラグ化はしない（過剰設計を避ける）                                                                                     |
| `id`に`:`を含むモデル（`:free`/`:batch`/`:thinking`等）は`scope.py`で除外する                                                                          | プランレビューで実データ確認: `anthropic/claude-sonnet-4.5:batch`等は本体と同じ`coding_index`を持ちながら価格が約半額のため、除外しないと同ランク内で通常版を常にPareto支配してしまい、対話利用できないbatch専用モデルだけが結果に残る事故が起きる |
| author絞り込みは`fetch.py`側の`model_authors=openai,anthropic,google`クエリパラメータで行い、`scope.py`側でのid prefix判定はしない                     | プランレビューでの指摘。API側フィルタの方がシンプルでレスポンスサイズも減らせる                                                                                                                                                                    |

## 推奨の進め方

- **実行主体**: メインエージェント。5モジュール+テスト2ファイルは相互依存が強く（`dominance.py`は`rank.py`のbucket構造・`pricing.py`の価格取得を前提にする）、並行分割してもすり合わせコストの方が高い規模。
- **TODO化**: 「モジュールごとに実装→対応するテストを書く」を1モジュール=1TODOにする（`fetch.py`はネットワークI/Oのためテスト対象外、手動確認のみでよい）。
- **関連スキル**: 特になし（外部知識は本ステップの「読むべきファイル」で足りる）。

---

## 計画との差分（実行時に判明・クリティカル）

（実行前のため、まだ無し）
