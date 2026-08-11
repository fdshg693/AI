## `.claude/plans` 運用ルール

機能実装前のプランを置く場所。新規プランを**書く前**にも、既存プランを**読み込んで実装を進める前**にも、必ず [.claude/plans/README.md](../plans/README.md) を読むこと。

要点（詳細は README.md 参照）:

- 複雑なタスクでは、詳細プランを書く前にプロジェクト用フォルダ配下の `rough/`（例: `.claude/plans/{project-name}/rough/`）で自由形式のラフプランを書いてもよい（任意）。方針が固まったら本フォーマットで詳細プランに整理する。ラフプランにも軽量なfrontmatter（`type: Rough Plan`、`status`は`drafting`／`ready-for-plan`／`promoted`の3値のみ）を付け、`promoted`（詳細プラン着手）以降はこのstatusを更新しない。詳細は README.md の「ラフプランの置き場所」節参照。
- プランファイル（概要・ステップ・単一ファイル完結プランいずれも）の先頭にはOKF準拠のYAML frontmatter（`type: Plan`/`Plan Step`、`status`）を付ける。`status`はこのリポジトリのプラン独自のライフサイクル値（`planning-research`／`planning-breakdown`／`ready`／`implementing-started`／`implementing-in-progress`／`implementing-done`）を使い、本文に状態を示す文言を重複して書かない。フィールドの意味は README.md の「プランのfrontmatter（OKF準拠）」節、OKF一般の書き方は [okf-spec](../skills/okf-spec/SKILL.md) スキルを参照。
- プランに実装詳細（コードスニペット、具体的なプロパティ/メソッド本体）を書かない。書くのは「やること」「触るファイル」「決定事項・落とし穴」「ルール更新ポイント」の4点のみ（[[roles]] の指示どおり、ルール更新箇所は各ステップに必ず含める。ルールの格納先はレポジトリにより異なる: `.claude/rules/`・`AGENTS.md`・`CLAUDE.md`・`.clinerules` 等、対象レポジトリの既存慣習に合わせる）。
- 書き方は [.claude/plans/references/](../plans/references/) をテンプレートとして流用する。プラン実行中の進捗記録（frontmatterの`status`更新・✅マーク・計画との差分・progressフォルダへの導線）は [references/progress/](../plans/references/progress/) 配下を参照。
- 全ステップが `implementing-done` になり作業が完了したら、プランファイル自体（フォルダまたは単一ファイル）を削除し、他の変更済みファイルに残るそのプランファイルへの参照（デッドリンク）も除去する。実行中の参照は残してよい。詳細はREADME.mdの「完了後の後片付け（プランファイルの削除）」節参照。
- ステップ分割の目安（触るファイル3〜4個以内かつレイヤーをまたぐ新規追加なしなら単一ファイル、それ以外は `00-overview.md` + ステップ分割）も README.md に従う。
- このレポジトリでは、 `.claude/rules` は採用せず、 `AGENTS.md` を使ったルール管理を行う
  - `.github/instructions`・`.clinerules` などのAIツールのルールファイルは、`lefthook.yml`による自動同期が走るので気にしなくていい
