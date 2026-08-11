# プラン実行時

進捗記録・完了後の後片付けの基本ルールは [references/skills-general/plan-execution.md](../skills-general/plan-execution.md) を参照（この2ファイルの内容はほぼ共通）。このファイルではこのリポジトリ固有の補足のみ記す。

## 進捗記録のサンプル

- [references/progress/README.md](../progress/README.md) — 進捗記録の棲み分け方（何をプランファイル本体に残し、何を progress に置くか）
- [references/progress/01-research-results-example.md](../progress/01-research-results-example.md) — 調査ステップの詳細結果・後続ステップへの引継ぎ
- [references/progress/02-implementation-notes-example.md](../progress/02-implementation-notes-example.md) — 実装ステップの計画との差分・実装メモ・後続タスクへの引継ぎ

## 実行時に使えるスキル

**スキル選定は必ず [discovering-skills](../../../../repo-meta/skills/discovering-skills/SKILL.md) スキルの手順に従う。** 先に同梱の [BEST_PRACTICES.md](../../../../repo-meta/skills/discovering-skills/BEST_PRACTICES.md) でこのリポジトリの典型パターンを確認し、該当が無ければ `skill-search` サブエージェントで探す。以下は代表例に過ぎず、90件超あるこのリポジトリの全スキルを網羅していない。

- ルール更新（`AGENTS.md` への追記のフォーマット）: [writing-rules](../../../../claude-plugins/meta/skills/writing-rules/writing.md)
- 再利用するサブエージェントを作る場合: [writing-subagents](../../../../claude-plugins/meta/skills/writing-subagents/SKILL.md)
- 複数ステップをサブエージェントで並行させる場合（Dynamic Workflow）: [writing-workflows](../../../../claude-plugins/meta/skills/writing-workflows/SKILL.md)

実行主体・スキル選定の判断軸は [README.md](../../README.md) の「ステップの推奨の進め方」節のメニューを参照。
