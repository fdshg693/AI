---
type: Plan Step
status: planning-breakdown
---

# Step4: 選ぶ → ドッグフーディング → 改善を回すメンテスキルと導線

## やること

`maintenance/plugin/skills/skill-dogfooding/` に、1 回の周回を進める手順スキルを足す。ユーザーが明示的に呼んだときだけ動く（`disable-model-invocation: true`）。あわせて仕組みの説明を `maintenance/docs/` に書き、`meta` スキルから辿れるようにする。

周回の流れ（スキル本文に書く内容）:

1. **選ぶ**: `just ... skill-risk --top 5` の結果を動的コンテキストで読み込み、上位からユーザーと 1 件決める（引数でスキルを指定したら飛ばす）。
2. **シナリオを作る**: 対象スキルの description と本文から、実際に頼まれそうな依頼を 2〜3 件作る。うち 1 件はスキル名を出さない依頼にする（自動起動の確認）。
3. **ドッグフーディング**: シナリオごとに scratch ディレクトリで `claude -p --plugin-dir <対象プラグインのディレクトリ> --setting-sources "" --no-session-persistence --output-format stream-json --verbose` を起動して作業させ（`--tools` を絞るときは必ず `Skill` を含める）、stream-json の `Skill` の `tool_use` で起動を判定する。そのうえで「スキルが起動したか」「手順どおりに進められたか」「コマンド・パス・仕様が実在・最新か」「迷った・遠回りした箇所」を報告させる。外部への書き込み（push、Issue、Azure など）は止めさせる。
4. **記録**: 起きたことの本文を `skill-tools --fb <canonical ID> --fb-kind skill` で残し、台帳 `maintenance/skill-risk/dogfood.yaml` に日付・判定（`ok` / `needs-fix`）・fb ファイル名を書く。カタログ未登録のスキル（`maintenance/plugin/` など）は `--fb` が使えないので、本文の要点を台帳の `note` に書く。
5. **改善**: 要改善なら `writing-skill` と `changing-skills-and-tools` に従って直す。`meta.version` を上げ、`committing` の 2 段階コミットに従う。改善したら台帳の判定を `fixed` にして改善コミットを `fix: <repo>@<short-hash>` で記録する。直さずに終える場合も、台帳は「要改善」のまま残す（次回のランキングで上位に残る）。

## 読むべきファイル

- 前例のメンテスキル（最優先）
  - `maintenance/plugin/skills/skill-maintenance/SKILL.md` — 動的コンテキスト、サブエージェントへの委譲、`disable-model-invocation` の使い方
  - `maintenance/plugin/skills/skill-maintenance/README.md` — `state/` の扱い
  - `maintenance/plugin/README.md` — 保守用プラグインの置き方と読み込み方（`--plugin-dir ./maintenance/plugin`）
- ドッグフーディングの方法
  - `skills/plugins/cc-knowledge/skills/writing-skill-complex/SKILL.md` — サブエージェントでスキルを試す手順。流用するのは「新しいコンテキストに現実的なシナリオを渡して観察する」部分と参照型スキルの検証観点だけで、圧力シナリオと RED-GREEN-REFACTOR は持ち込まない
  - [progress/01-research-results.md](progress/01-research-results.md) の「5. ドッグフーディングの実行方法」— 実際に試した `claude -p` のコマンドと結果
  - `skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md`・`bestpractices.md` — 改善時の基準
- 改善とコミット
  - `maintenance/plugin/skills/changing-skills-and-tools/SKILL.md`
  - `maintenance/plugin/skills/committing/SKILL.md`
  - `maintenance/docs/skill-md-commits.md` — `SKILL.md` をコミットするときの pre-commit の挙動
- フィードバック
  - `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`・`tools/skill-tools/README.md` の `--fb` 節
- 導線
  - `maintenance/plugin/skills/meta/SKILL.md` の「選び方」
  - `maintenance/docs/skill-improving-meta-skills.md` — 既存のメタスキル層の説明と、新しい docs を足すかの判断
  - `maintenance/plugin/skills/exploring-this-repo/SKILL.md`・`discovering-skills/SKILL.md` — 新しいスキルを載せる必要があるか

## 触るファイル

- 新規: `maintenance/plugin/skills/skill-dogfooding/SKILL.md` — 周回の手順（`meta:` 付き。`requires_repo_tools` に Step3 のスクリプトと `skill-tools`）
- 新規（必要なら）: `maintenance/plugin/skills/skill-dogfooding/scripts/record_dogfood.py` — 台帳の 1 エントリを更新する小さなスクリプト（手編集で yaml を壊さないため）
- 変更: `maintenance/skill-risk/dogfood.yaml` — 最初の 1 周の記録
- 変更: `maintenance/docs/skill-improving-meta-skills.md` に節を足すか、新規 `maintenance/docs/skill-risk-maintenance.md` — シグナル、合成点、台帳、周回、`skill-maintenance`・`audit-skills` との棲み分け
- 変更: `maintenance/plugin/skills/meta/SKILL.md` — キーワード表に「どのスキルを直すべきか／ドッグフーディング」

## 決定事項・注意点／落とし穴

- 1 周 = 1 スキル。複数件を一度に直すと、どの改善が効いたか分からなくなり、台帳の記録も粗くなる。
- ドッグフーディングのサブエージェントには、スキルの改善案を書かせない（観察の報告だけ）。採否はメインが決める。
- 対象スキルが外部サービスに書き込むもの（`gh-pr`、Azure、Issue 作成など）は、読み取りだけのシナリオに絞るか、ユーザーの確認を挟む。スキル本文に明記する。
- Agent ツールのサブエージェントは親と同じスキル集合しか持たないので、自動起動の確認には使わない。`claude -p --plugin-dir` なら `.claude/skills/` に入っていないスキルも確かめられる（Step1 で `topics:linear-docs` の自動起動を確認済み）。`maintenance/plugin` も `--plugin-dir maintenance/plugin` で読み込める。
- 手順を最後まで試すには Bash・WebFetch などが要る（Step1 では外したためスキル本体がエラーになった）。渡すツールと外部への書き込みの止め方（`--disallowedTools`・`--permission-mode`）を本ステップで決め、スキル本文に書く。
- `maintenance/plugin/` は配布しないので、`ai-tools.yaml`・マーケットプレイスに載せない。そのため使うには `--plugin-dir ./maintenance/plugin` で読み込む必要がある。スキル本文の冒頭に書く。
- 動的コンテキストでランキングを出すと、起動のたびに git 履歴を全件走査する。Step1 の試作では約 1.6 秒なので動的コンテキストでよい見込み。Step3 の実装で改めて測る。
- 記録スクリプトは台帳をキー順に並べて書き、改善コミットはリポジトリ名とハッシュの組で記録する（改善はサブモジュール側のコミットになることが多い）。
- 新しい docs を作るか既存に足すかは `skill-improving-meta-skills.md` の判断順（既存に統合できるならそうする）に従う。

## ルール更新ポイント

- `maintenance/docs/`（本ステップ）: 仕組み全体の説明。新規 doc なら OKF frontmatter を付ける（`maintenance/docs/index.md` は pre-commit が生成するので手で足さない）。
- `maintenance/plugin/skills/meta/SKILL.md`（本ステップ）: キーワード表に追加。

## 進め方

- **実行主体**: スキル本文と docs はメイン。完成後、実際に 1 周（選ぶ→ドッグフーディング→記録→改善）を回して、スキル自身の手順の穴を直す。ドッグフーディング部分はスキルの手順どおりサブエージェントに委任する。
- **TODO化**: 「スキル本文（+ 記録スクリプト）」「docs と meta の導線」「実際の 1 周と、その結果によるスキル修正」の 3 項目。

## 実行中に判明した変更

- 2026-11-19（Step1）: ドッグフーディングを `claude -p --plugin-dir` で行う方式に変え、「起動は未確認」の代替手順を削除した。動的コンテキストの速度見込みを追記した。
- 2026-11-19（Step2）: 台帳が `maintenance/skill-risk/dogfood.yaml` に決まり、判定値を `ok` / `needs-fix` / `fixed` にした。
