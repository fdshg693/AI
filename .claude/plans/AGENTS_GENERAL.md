## `.claude/plans` 運用ルール（汎用版）

機能実装前のプランを置く場所。1機能 = 1サブフォルダ（または小さい機能なら1ファイル）。プランファイルの先頭には、Open Knowledge Format (OKF) 準拠のYAML frontmatter（`type: Plan`/`Plan Step`、リポジトリ独自のライフサイクル値を持つ`status`）を付ける。

新規プランを**書く前**にも、既存プランを**読み込んで実装を進める前**にも、場面に応じて以下を参照する。

| 場面             | 参照先                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------ |
| ラフプラン作成時 | [references/skills-general/rough-plan.md](references/skills-general/rough-plan.md)         |
| プラン作成時     | [references/skills-general/plan-writing.md](references/skills-general/plan-writing.md)     |
| プラン実行時     | [references/skills-general/plan-execution.md](references/skills-general/plan-execution.md) |

書き方の粒度感をつかむには、`references/` 配下のサンプル一式（`00-overview-example.md` 等）をテンプレートとして流用するとよい。サンプル中に特定AIツールのスキルへのリンクが残っている場合は元リポジトリ固有のものなので無視してよい。

このファイルは他プロジェクトへ導入するための汎用版。プロジェクト固有のスキル・ツール連携には触れていない（コピー先に存在するとは限らないため）。導入時は本ファイルを `AGENTS.md` にリネームする（`references/skills-general/` はフォルダ名のまま、上表のリンク先として使い続けてよい）。そのプロジェクト固有の運用（使えるサブエージェント・スキル、ルールファイルの格納先など）はこの3ファイルに書き足していく。
