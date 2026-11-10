## `plans` 運用ルール

機能実装前のプランを置く場所。1機能 = 1サブフォルダ `{plan-name}/`（または小さい機能なら1ファイル `{plan-name}.md`）。プランファイルの先頭には、Open Knowledge Format (OKF) 準拠のYAML frontmatter（`type: Plan`/`Plan Step`、リポジトリ独自のライフサイクル値を持つ`status`）を付ける。

新規プランを**書く前**にも、既存プランを**読み込んで実装を進める前**にも、場面に応じて以下を参照する。

| 場面             | 参照先                                                                     |
| ---------------- | -------------------------------------------------------------------------- |
| ラフプラン作成時 | [guides/rough-plan.md](guides/rough-plan.md)         |
| プラン作成時     | [guides/plan-writing.md](guides/plan-writing.md)     |
| プラン実行時     | [guides/plan-execution.md](guides/plan-execution.md)、[guides/progress.md](guides/progress.md) |

## 不変条件

- `status` は決められた値だけを使い、ステップの開始・完了のたびに更新する → [plan-writing.md「frontmatter」](guides/plan-writing.md#frontmatterokf準拠)
- 複数ステップの概要は frontmatter 直下に「実装ステータス」チェックボックスを置き、`status` と同時に更新する → [plan-execution.md「実行中に必ず行うこと」](guides/plan-execution.md#実行中に必ず行うこと)
- プラン間の依存は概要の `order`/`depends_on`/`blocks` に書き、両端を対で更新する。`depends_on` の条件を満たすまで着手しない → [plan-writing.md「プランフォルダ間の依存関係」](guides/plan-writing.md#プランフォルダ間の依存関係)
- 予定外の事実は影響を受けるプラン本文へ直接反映する。progress は詳細な根拠だけを置く場所で、引継ぎ先にしない → [plan-execution.md](guides/plan-execution.md)
- フォルダ方式のプランは実行着手前に `snapshot/` へ初版を凍結し、以降 `snapshot/` は編集しない → [plan-writing.md「初版の凍結スナップショット」](guides/plan-writing.md#初版の凍結スナップショットsnapshot)
- プランを更新したら `lint_plans.py` で整合を確認する → [plan-writing.md「整合性チェック」](guides/plan-writing.md#整合性チェックlint)
- 完了前に完了記録（フォルダ方式は progress、単一ファイル完結は本体の「完了記録」節）を書いてから、状態を完了にする → [plan-execution.md](guides/plan-execution.md)

## サンプル

書き方の粒度感は、書こうとしているファイルに対応するサンプルだけを読んでつかみ、テンプレートとして流用してよい。

サンプルは**実行完了状態**（`status: implementing-done`、チェックボックスは `- [x]`）で書かれている。新規プランは `status: planning-research` か `planning-breakdown`、チェックボックスは `- [ ]` で、「実行中に判明した変更」節や progress へのリンクは無しで書き始める。実際のプランは完了後に削除するが（[plan-execution.md「完了後の後片付け」](guides/plan-execution.md#完了後の後片付け)）、サンプルは残す。

`references/` は導入先の `plans/` と同じ構造で、複数ステップのプラン1つ（`postal-code-autofill/`）と単一ファイル完結プラン1つ（`tag-popularity-sort.md`）を置いている。

| 書くもの                      | サンプル                                                                                                                                                                                                                         |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 複数ステップの概要            | [references/postal-code-autofill/00-overview.md](references/postal-code-autofill/00-overview.md)                                                                                                                                 |
| 調査ステップ                  | [references/postal-code-autofill/01-research-zipcloud-api.md](references/postal-code-autofill/01-research-zipcloud-api.md)                                                                                                       |
| 実装ステップ                  | [references/postal-code-autofill/02-api-client-and-form.md](references/postal-code-autofill/02-api-client-and-form.md)                                                                                                           |
| 1ファイルで完結する小さい機能 | [references/tag-popularity-sort.md](references/tag-popularity-sort.md)（末尾に完了記録）                                                                                                                                         |
| ラフプラン                    | [references/postal-code-autofill/rough/01-initial-idea.md](references/postal-code-autofill/rough/01-initial-idea.md)                                                                                                             |
| progress（進捗・完了記録）    | [guides/progress.md](guides/progress.md)（棲み分け）、[調査結果](references/postal-code-autofill/progress/01-research-results.md)、[実装メモ・完了記録](references/postal-code-autofill/progress/02-implementation-notes.md) |

サンプルには `snapshot/` を置いていない（初版の逐語コピーなので、中身は親フォルダのプランと同じ形になる）。

## このテンプレートを編集するとき

- 共通ルールの正本は `guides/`。本ファイルとサンプルにはルールを重複して書かず、リンクにする。
- プレースホルダは `{plan-name}` のように `{}` で書く。
- サンプルを変更したら `uv run plans/lint_plans.py --examples plans/references` でサンプル自体が lint 規約に合っているか確認する。
- 必須の節を変えるときは、[plan-writing.md「節構成」](guides/plan-writing.md#節構成lint-で検査)の表と `lint_plans.py` の `REQUIRED_SECTIONS` を同時に更新する。

## 導入先固有の運用

使えるサブエージェント・スキル、ルールファイルの格納先など、導入先プロジェクト固有の運用はこの節に書き足す。
