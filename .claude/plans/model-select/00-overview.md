---
type: Plan
status: ready
---

# model-select ツール 実装プラン - 概要

OpenRouterのArtificial Analysisベンチマーク（`coding_index`）と価格を判断材料に、GPT/Claude/Gemini系列モデルの選択を行いやすくするツール。`tools/model-select/`に新規Pythonパッケージとして作る。

## 要件

- OpenRouterの`GET /api/v1/models`から取得したモデル情報のうち、`id`が`openai/`・`anthropic/`・`google/`のいずれかで始まるモデルのみを対象にする（`model_authors`クエリパラメータで絞り込む）。
- `id`に`:`を含むvariant（`:free`/`:batch`/`:thinking`等）は除外し、canonical modelのみを対象にする。
- `benchmarks.artificial_analysis.coding_index`が65未満、またはフィールド自体が無いモデルは対象外。65以上を3刻みでランク分けする（`[65,68)`, `[68,71)`, ...）。
- 価格は「入力重視」「出力重視」の2軸で完全に分けて比較する（1つのモデルが両方の一覧に別々に登場しうる）。
- 各軸の価格は、モデルの`pricing`ベース値と`pricing.overrides[]`（コンテキスト長閾値等による割増価格）の中の最大値を採用する（安全側＝最悪ケースで比較するため）。マルチプロバイダ間の価格差（`/endpoints` API）は考慮しない — OpenRouterが自動選択する前提で`/api/v1/models`の値をそのまま使う。
- 同じランク内で「価格・ベンチマーク双方において自分以上に優れる他モデル」が存在するモデルはPareto最適の考え方で除外し、Pareto frontier上のモデルだけを残す。入力重視・出力重視それぞれ独立に判定する。
- 結果はシンプルな最小限のWebアプリ（自己完結HTML、サーバー不要）でUI表示する。実行のたびにOpenRouter APIをライブ取得する（キャッシュ無し）。
- 将来モデル・ベンチマーク種別が増えても対応しやすいよう、ランク付け・Pareto判定ロジックは特定の指標名（`coding_index`等）にベタ書きせず、汎用的なパラメータ化された関数として書く（過度な抽象化はしない）。

## 実装ステップ

1. [01-core-pipeline.md](01-core-pipeline.md) — データ取得・スコープ絞り込み・価格算出・ランク分け・Pareto フィルタ（純粋ロジック層、ユニットテスト込み）
2. [02-render-cli-packaging.md](02-render-cli-packaging.md) — 自己完結HTML生成・CLIエントリポイント・パッケージ化（`tools/model-select/`のuv登録、README等）

外部API仕様（`pricing.overrides`の実データ）は本プラン作成時に実APIレスポンスで確認済みのため、独立した調査ステップは置かない（詳細は下記「主要な決定事項」）。

## 主要な決定事項

| 決定                                                                                                                                                     | 理由                                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 価格は`pricing.prompt`/`pricing.completion`と、`pricing.overrides[].prompt`/`.completion`の中の最大値を採用する                                          | `google/gemini-2.5-pro`の実レスポンスで、`overrides`に`min_prompt_tokens: 200000`条件下のprompt/completion割増価格が入っていることを確認済み。閾値判定は行わず常に最悪ケースを採用                                                            |
| プロバイダ間の価格差（`/api/v1/models/{author}/{slug}/endpoints`）は使わない                                                                             | OpenRouterが自動的にプロバイダを選択するため、比較には`/api/v1/models`の値（実質そのモデルの最安値ベース）だけで十分というユーザー判断                                                                                                        |
| 認証無しで`GET /api/v1/models`を呼ぶ                                                                                                                     | このエンドポイントは認証不要で200が返ることを確認済み（レート制限を将来的に踏むならAPIキー対応を追加検討）                                                                                                                                    |
| キャッシュを持たず毎回ライブ取得する                                                                                                                     | ユーザー確定事項。キャッシュ管理コードが不要になりシンプルさを優先                                                                                                                                                                            |
| 結果表示は自己完結HTML（サーバー無し、JS無しでPython側が直接HTMLテーブルを生成）                                                                         | ユーザー確定事項。ローカルサーバー管理・フロントエンドJSの複雑さを避け、`tools/`配下の他CLIツールと同じ「実行して終わり」の使い勝手にする                                                                                                     |
| ランク分け・Pareto判定は指標名・価格キーをパラメータとして受け取る汎用関数にする（`coding_index`等をベタ書きしない）                                     | 将来ベンチマーク種別・モデル系列が増える見込みがあり、「ほどほどの抽象性」の要望に沿う。ただしプラグイン機構・設定ファイル化はしない（過剰設計を避ける）                                                                                      |
| 依存ライブラリは`requests`のみ（HTML生成もPython標準機能で完結、Jinja2等は使わない）                                                                     | `tools/ctx7`が同様の「REST APIを直叩きするだけの薄いCLI」で`requests`を使っている前例に合わせる。テーブルを静的に埋め込むだけなのでテンプレートエンジンは不要                                                                                 |
| `id`に`:`を含むvariant（`:free`/`:batch`/`:thinking`等）はスコープから除外する                                                                           | プランレビューで実データ確認: `anthropic/claude-sonnet-4.5:batch`等の`:batch`系variantは同一`coding_index`を継承しつつ価格が約半額のため、除外しないとPareto比較で通常版を常に支配し、対話利用できないbatch専用モデルだけが結果に残ってしまう |
| モデル取得は`GET /api/v1/models?model_authors=openai,anthropic,google`のクエリパラメータで絞り込み、クライアント側でのid prefix判定は行わない            | プランレビューでの指摘。API側フィルタの方がシンプルでレスポンスサイズも減らせる                                                                                                                                                               |
| bucketに該当モデルが0件の場合、その見出し自体を出力しない（"該当なし"表示もしない）                                                                      | 要求どおりのランク幅（coding_index>=65を3刻み）では対象が少なく、プラン作成時点のライブ確認で対象は23件程度・多くのbucketが1〜2件以下になる想定。空bucketの通知表示は過剰なので単純に省く（仕様であり実装漏れではない）                       |
| `pricing.overrides`は`openrouter-docs`スキルのreference未収録の未検証フィールドだが、本プラン作成時に実データ（`google/gemini-2.5-pro`等）で構造確認済み | 一次情報が無いことを明記した上で採用する。将来フィールド仕様が変わった場合はStep1のテストが失敗して検知できるようにする                                                                                                                       |
| エージェント向けの`SKILL.md`は本プランのスコープ外                                                                                                       | 人間がローカルで`model-select`を実行しHTMLをブラウザで見るツールであり、AIエージェントから呼ぶ想定は無い。必要になれば別プランで追加する                                                                                                      |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `tools/model-select/pyproject.toml`
- `tools/model-select/README.md` / `AGENTS.md` / `CLAUDE.md`
- `tools/model-select/model_select/__init__.py`
- `tools/model-select/model_select/fetch.py`
- `tools/model-select/model_select/scope.py`
- `tools/model-select/model_select/pricing.py`
- `tools/model-select/model_select/rank.py`
- `tools/model-select/model_select/dominance.py`
- `tools/model-select/model_select/render.py`
- `tools/model-select/model_select/cli.py`
- `tools/model-select/tests/test_scope.py`
- `tools/model-select/tests/test_pricing.py`
- `tools/model-select/tests/test_rank_dominance.py`
- `tools/model-select/.gitignore`
- `tools/model-select/output/.gitkeep`

### 変更

- `pyproject.toml`（リポジトリルート）— `[tool.uv.workspace].members`に`tools/model-select`を追加

## ルール更新ポイント

このリポジトリは`AGENTS.md`ベースのルール管理（`.claude/rules`は不採用）。新規に追記が必要な既存ルールファイルは無い — `tools/model-select/AGENTS.md`は既存の他ツール（`tools/aim/AGENTS.md`等）と同じ`@./README.md`インクルードのみの新規ファイルであり、共有ルールの変更ではない（詳細はStep2）。

## 推奨の進め方（概要ファイル）

- **立案時**: 既に2ステップへの分割は完了。追加のflow-proposer提案は不要な規模。
- **TODO化**: ステップ一覧の各項目をそのままTODO項目にする。
- **関連スキル**: 実装時に価格・ベンチマークのフィールド仕様を再確認する場合は[openrouter-docs](../../../claude-plugins/topics/skills/openrouter-docs/SKILL.md)スキルの[references/models-pricing-benchmarks.md](../../../claude-plugins/topics/skills/openrouter-docs/references/models-pricing-benchmarks.md)を参照。
