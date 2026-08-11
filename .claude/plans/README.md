# .claude/plans

機能実装前のプランを置く場所。1機能 = 1サブフォルダ（または小さい機能なら1ファイル）。

## ラフプランの置き場所（オプション、複雑なタスク向け）

要件や実装方針がまだ固まっていない複雑なタスクでは、詳細プランを書く前に、そのプロジェクト用フォルダ配下の `rough/` に自由形式のラフプランを書いてよい（例: `.claude/plans/{project-name}/rough/*.md`）。複数案の比較や迷っている点をフォーマットに縛られず書き出せる。

- 形式は自由。以下の5点フォーマットに縛られない。比較検討中の案、迷っている点、未解決の疑問をそのまま書いてよい。サンプル: [references/rough/example.md](references/rough/example.md)（同じ架空機能を題材に、詳細プランを書く前段階の書き殴り方を示している）。
- シンプルなタスク（後述の「単一ファイルで完結」基準に収まるもの）ではラフプランは不要。直接、以下のフォーマットで詳細プランを書く。
- 方針が固まったら、ラフプランの内容を以下のフォーマットに従って詳細プランとして整理する。ラフプランは下書きであり実装時の正としては扱わない — 実装に着手する前に必ず詳細プランへ変換すること。ラフプラン自体は削除必須ではなく、検討経緯の記録として `rough/` に残しておいてよい。
- ラフプランにも軽量なOKF frontmatter（`type: Rough Plan`、`status`）を付ける。詳細プラン側（`type: Plan`/`Plan Step`）とは別の3値のみを使う。

  | 値               | 意味                                                                                                                                    |
  | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
  | `drafting`       | ラフプラン作成中                                                                                                                        |
  | `ready-for-plan` | ラフプラン作成完了。詳細プランに移れる状態                                                                                              |
  | `promoted`       | 詳細プランに着手した。ラフプランの役割はここで終わり、以降このstatusは更新しない（それ以降の進捗は詳細プラン側のfrontmatterで管理する） |

## プランの書き方（現行方針）

実装詳細（コードスニペット、具体的なプロパティ定義・メソッド本体など）は書かない。書くのは次の5点だけ。

- **やること**（1〜数行）
- **触るファイル**（新規／変更、パス＋一言）
- **読むべきファイル・実行推奨Grep**（実装前に理解しておくべき既存コード。「何を確認するために読むのか」という観点ごと、優先度ごとにグルーピングする。パスをフラットに並べるだけにしない）
- **決定事項・注意点／落とし穴**（判断の理由、既存コードとの衝突、競合状態など事前に言語化できるリスク）
- **ルール更新ポイント**（対象レポジトリのルール格納先に・いつ・何を追記するか。格納先はレポジトリにより異なる: `.claude/rules/`（Claude Code・複数ファイル＋`paths:`フロントマター）、`AGENTS.md`（レポジトリ直下）、`CLAUDE.md`（Claude Codeプロジェクトメモリ）、`.clinerules`（Cline）等。詳細は対象レポジトリの既存慣習に合わせる。新規ルールファイルを作る場合は、対象パスを決めるフロントマター（`paths:`）までプランに書く — ただしフロントマター方式は `.claude/rules/` のような複数ファイル方式の場合で、`AGENTS.md` 等の単一ファイル方式ではセクション見出しで対象を示す。既存ファイルへの追記でパスに変更が無い場合はフロントマターの記載は不要）

コードそのものは実装時に既存の類似ファイルを読んで導出すればよく、プランに書き切る必要はない。

## プランのfrontmatter（OKF準拠）

プランファイル（概要ファイル `00-overview.md`、ステップファイル `01-*.md`/`02-*.md`…、単一ファイル完結プラン）の先頭には、[Open Knowledge Format (OKF)](../skills/okf-spec/SKILL.md) 準拠のYAML frontmatterを付ける。フィールドの意味・一般的な書き方はOKFの規約（[okf-spec skillのSUMMARY.md](../skills/okf-spec/SUMMARY.md)・[WRITING_GENERAL.md](../skills/okf-spec/WRITING_GENERAL.md)）にそのまま従う。このリポジトリのプラン独自の意味を持たせるのは`status`の値だけ。

```yaml
---
type: Plan # 概要ファイル・単一ファイル完結プランはこの値
status: planning-breakdown
---
```

```yaml
---
type: Plan Step # ステップファイル（01-*.md, 02-*.md 等）はこの値
status: implementing-in-progress
---
```

- `type`はOKF同様、中央登録されない自由文字列（[WRITING_GENERAL.md](../skills/okf-spec/WRITING_GENERAL.md)参照）。このリポジトリのプランでは `Plan`（概要・単一ファイル完結プラン）／`Plan Step`（ステップファイル）の2値のみ使う。
- `title`/`description`/`tags`/`generated`/`verified`等、OKFのその他のフィールドは任意。使う場合はOKF本来の意味のまま使ってよいが、プランでは必須にしない（H1見出しや本文と重複する情報をfrontmatterに書き直さない）。
- `progress/`配下のファイルは自由形式のメモであり、このfrontmatterを必須としない（[references/progress/README.md](references/progress/README.md)参照）。`rough/`配下は軽量な専用frontmatter（`type: Rough Plan`、3値のみの`status`）を持つ — 詳細は「ラフプランの置き場所」節を参照。

### `status`の値（このリポジトリのプラン用ライフサイクル）

OKF本来の`status`（`draft`/`stable`/`deprecated`、[SUMMARY.md §5.4](../skills/okf-spec/SUMMARY.md)）はプランの進捗粒度には合わないため使わず、代わりに次の6値を使う。値は「プラン中」2値と「実行中」3値、および両者の間を橋渡しする`ready`で構成する。

| 値                         | 意味                                                                       |
| -------------------------- | -------------------------------------------------------------------------- |
| `planning-research`        | プラン中。内容を確定させるための追加調査がまだ必要（方針が固まっていない） |
| `planning-breakdown`       | プラン中。調査は完了/不要だが、実装できる粒度への分割・詳細化がまだ必要    |
| `ready`                    | プラン確定。調査/実装の実行にはまだ着手していない                          |
| `implementing-started`     | 着手した直後。全体のごく一部にしか手を付けていない                         |
| `implementing-in-progress` | 実行が部分的に完了し、継続中                                               |
| `implementing-done`        | 完了                                                                       |

- 調査ステップ（[01-research-step-example.md](references/01-research-step-example.md)）でも同じ6値を使う。「`implementing-*`」とあるが、調査ステップにとってはコード実装ではなく「そのステップの作業（Web調査等）の実行」を指す。
- 省略時のデフォルトは定義しない。OKF本来は省略時`stable`だが、プランでは進捗が曖昧になるため`status`は必須とし、書き始めた時点で`planning-research`か`planning-breakdown`のいずれかを明示する。
- 概要ファイル・単一ファイル完結プランの`status`は機能全体の代表ステータスを手動更新する。個々のステップの詳細な状態は各ステップファイル側のfrontmatterを見る（自動集計はしない）。

## 外部知識が必要な場合: 事前調査ステップ

外部API・外部ライブラリなど、実装前にWeb上のドキュメントを確認しないと決定事項が固まらない機能では、調査を**独立した1ステップ**として先に切り出す。

- そのステップでは、関連しそうなキーワード・URLをまず洗い出し、WebSearch/WebFetchで取得・理解する。
- 調査結果は「要約 + 参照URL」として出力する。読んだページの全文は書かない。後続の実装ステップはこの出力を前提に書き、調査時の文脈を持ち込まない。
- 調査は無駄なページ取得も含めてコンテキストを多く消費するため、実装ステップと同じファイルに混ぜない。
- 設計判断を伴わない軽量なコードベース内調査（既存パターンの有無をgrepで洗い出すだけ、等）は、コストの低いHaikuモデルのサブエージェントに委任してよい（Agent toolを`model: haiku`で起動）。決定事項の採否そのものはプランを書く側が判断する。

サンプル: [01-research-step-example.md](references/01-research-step-example.md)。

## ステップの推奨の進め方（サブエージェント・スキル・TODO化）

各ステップには「やること・触るファイル・読むべきファイル・決定事項」に加え、**そのステップをどう進めるかの推奨（実行主体・使えるスキル・TODO化の粒度）**を1〜3行で書いておく。書かないと「誰が・何を使って・どこまでを1作業単位として進めるか」が実行時の思いつきに委ねられ、サブエージェントの過剰/過小分割・スキルの未活用・TODOの粒度のバラつきが出る。

各ステップファイル（[references/](references/) 配下）にはステップ種別ごとの推奨を「推奨の進め方」節として示してある。以下はそのメニュー。

### 実行主体の選択（サブエージェント活用）

| 実行主体                                  | 使う場面                                                                                                            | 方法                                                                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| メインエージェント                        | ユーザーとの対話・判断を要する作業、後続ステップ全体の前提になる調査、1〜2ファイルで分割コストの方が高い作業        | そのまま実行                                                                                                                             |
| 読み取り専用サブエージェント（`Explore`） | 既存パターンの有無をgrepで洗い出すだけの軽量なコードベース調査。設計判断を伴わない                                  | Agent tool `subagent_type: Explore`。必要なら `model: haiku` でコスト低下                                                                |
| 汎用サブエージェント（`general-purpose`） | 独立して並行実行できる実装単位・書き込みを伴わない検証（レビュー・テスト結果確認）。resume して継続作業させたい場合 | Agent tool `subagent_type: general-purpose`。同時に複数体が同じファイルへ書き込むなら worktree isolation を要する                        |
| `flow-proposer` サブエージェント          | プラン立案時、ステップ分割と実行主体の提案が欲しいとき                                                              | [proposing-flow](skills/proposing-flow/SKILL.md) スキル経由で Agent tool `subagent_type: flow-proposer` を呼ぶ（読み取り専用・提案のみ） |
| Claude CLI ワンショット                   | 大量の読み取り・重い独立タスクをメイン会話のコンテキストを汚さず実行したいとき                                      | [claude-cli-use](skills/claude-cli-use/SKILL.md) スキル。タスク難度で Sonnet/Haiku を選ぶ                                                |

サブエージェントは真っ新なコンテキストで始まる（メイン会話の文脈・`CLAUDE.md` 等のプロジェクト指示を知らない前提）。委譲時のプロンプトには必要な前提・出力フォーマットを明示する。サブエージェントの作成・設計は [writing-subagents](skills/writing-subagents/SKILL.md) スキル、並列・パイプライン編成は [writing-workflows](skills/writing-workflows/SKILL.md) スキルを参照。

### 関連スキル活用

ステップ種別ごとに使えそうなスキルの目安。実際の適用は対象レポジトリの既存慣習に合わせる。

| ステップ種別         | 使えるスキル                                           | 用途                                                                  |
| -------------------- | ------------------------------------------------------ | --------------------------------------------------------------------- |
| 調査ステップ         | [claude-cli-use](skills/claude-cli-use/SKILL.md)       | 重いWeb/コード調査をCLIワンショットへ委譲（モデル選択）               |
| 実装ステップ         | [writing-rules](skills/writing-rules/writing.md)       | ルール更新（フロントマター・規約本文のフォーマット）                  |
| 実装ステップ         | [writing-subagents](skills/writing-subagents/SKILL.md) | 再利用するサブエージェントを作る場合                                  |
| 実装ステップ（並行） | [writing-workflows](skills/writing-workflows/SKILL.md) | Dynamic Workflow（`.claude/workflows/*.js`）で並列/pipeline 編制      |
| 立案時               | [proposing-flow](skills/proposing-flow/SKILL.md)       | flow-proposer によるステップ分割提案                                  |
| セッションまたぎ     | [task-tracker](skills/task-tracker/SKILL.md)           | 複数セッションをまたぐタスク追跡（`.claude/tasks/<name>/CURRENT.md`） |

### TODO化

各ステップは実行時にTODO（タスク）として追跡できる形に書く:

- **1セッションで完結する小機能**: ステップの「やること」1行をそのままチェックリスト（TodoWrite 等）の1項目にする。サブエージェントを跨ぐ場合でも、メインエージェント側でステップ完了をマークする。
- **複数セッションをまたぐ・一時中断が前提の機能**: [task-tracker](skills/task-tracker/SKILL.md) スキルで `.claude/tasks/<task-name>/CURRENT.md` に現状・次にやることを残す。プランの各ステップ（✅マーク）と task-tracker の CURRENT.md は二重管理にならないよう棲み分ける — ステップの完了マークはプラン側、進行中の細かい現状は task-tracker 側。
- **サブエージェントに委譲したステップ**: 委譲単位を1つのTODO項目にし、戻り（結果）を受けて完了マーク。並列で複数体を走らせる場合は worktree isolation の要否もTODOに添える。

TODOの粒度は「1項目 = 1コミット/1レビュー単位」を基準にする。1ステップが大きいときはTODOを小分けし、詳細は progress へ引継ぎを残す（[references/progress/README.md](references/progress/README.md)）。

## 書き方の参考: `.claude/plans/references/`

新しくプランを書く前に、まず [`references/`](references/) 配下の4ファイルを読むこと。架空のサンプル機能を題材に、上記フォーマットの粒度感を示している。

- [00-overview-example.md](references/00-overview-example.md) — 複数ステップに分割する場合の概要ファイル
- [01-research-step-example.md](references/01-research-step-example.md) — 事前調査ステップ（Web調査・Haikuサブエージェントへの委任の書き方）
- [02-implementation-step-example.md](references/02-implementation-step-example.md) — 実装ステップ（「読むべきファイル・推奨Grep」「触るファイル」「落とし穴」、新規ルールファイルのフロントマターの書き方）
- [03-single-file-example.md](references/03-single-file-example.md) — 小さい機能を1ファイルで完結させる場合

各ファイル末尾の「書き方のポイント」節に、なぜその粒度・構成にしているかの解説がある。実際にプランを書くときはこの4ファイルをテンプレートとして流用してよい。

### プラン実行中の進捗記録

上記4ファイルは**初期プラン**の書き方を示す。実行が進むにつれ、各プランファイルには薄い進捗導線を追記していく:

- 各プランファイルのfrontmatter `status` を「プランのfrontmatter（OKF準拠）」節の値に更新する（正はfrontmatter。本文に状態を示す文言を書き直さない）
- `00-overview.md` のステップ一覧に✅を付ける（クイックスキャン用の目印。詳細な状態は各ステップファイルのfrontmatterを見る）
- 必要なら本文冒頭に progress フォルダへのリンクを残す
- 計画通りにいかなかった変更は「計画との差分」節として1〜2行のサマリを残す（理由の詳細は progress 側）

詳細な調査結果・実装メモ・差分の理由・後続タスクへの引継ぎは、プランファイル本体には書かず [`references/progress/`](references/progress/) 配下にまとめる。プランファイル本体は「目次・導線」として薄く保ち、詳細を分離することでスキャン性を落とさない（クリティカルな内容＝計画どおりにいかず変更した内容・実装進捗のみ本体に残し、詳細な実装内容・後続タスクへの引継ぎは progress に置く）。書き方のサンプル:

- [references/progress/README.md](references/progress/README.md) — 進捗記録の棲み分け方（何をプランファイル本体に残し、何を progress に置くか）
- [references/progress/01-research-results-example.md](references/progress/01-research-results-example.md) — 調査ステップの詳細結果・後続ステップへの引継ぎ
- [references/progress/02-implementation-notes-example.md](references/progress/02-implementation-notes-example.md) — 実装ステップの計画との差分・実装メモ・後続タスクへの引継ぎ

progress フォルダは実行開始時点では空（または未作成）でよい。詳細が溜まったときに初めて作る。

### 完了後の後片付け（プランファイルの削除）

プラン実行中（`status: implementing-*` の間）は、他ファイルのコメント等からプランファイル（`.claude/plans/{plan-name}/...md`）を参照するのは意図した使い方であり、むしろ進捗のトラッキングのために望ましい。

しかし全ステップが `implementing-done` になり作業が完了したら、そのプランフォルダ／ファイルは不要になる。削除せず放置すると、他の変更済みファイルに残る「プランファイルへの参照（デッドリンク）」がそのまま残り続けてしまう。完了時は次の2点を後片付けとして行う:

1. プランファイル自体を削除する（`00-overview.md` + ステップファイル群の場合はそのプランフォルダ一式、単一ファイル完結プランの場合はそのファイル単体）。
2. 削除に伴い、他の変更済みファイル中にそのプランファイルへの参照が残っていないか確認し、残っていれば除去する。

既に完了扱いになっている過去の既存プランを遡って削除する必要はない。このステップは今後完了するプランから適用する。

### ステップ分割の目安

- 触るファイルが3〜4個以内で、既存レイヤーをまたぐ新規追加（新しいEntity/Repository/Serviceの新設など）がなく、独立した調査ステップも不要 → 単一ファイルで完結させる（`03-single-file-example.md`）
- 新規ドメイン追加、複数レイヤー（Controller/Service/Repository/View/Migration）にまたがる、または外部API・外部ライブラリの事前調査が必要 → `00-overview.md` + ステップ分割ファイル群（`00-overview-example.md` / `01-research-step-example.md` / `02-implementation-step-example.md`）
