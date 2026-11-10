---
type: Plan Step
status: planning-breakdown
---

# Step 9: README・AGENTS.md・docs・探索スキルの最終更新

> [00-overview.md](00-overview.md) の続き。08 まで完了していること。05〜08 で各ステップのルール更新は済んでいる前提で、全体を最終構成に揃え、残った古い記述を消す。

## やること

- ルートの `README.md`・`README_EN.md`・`AGENTS.md`・`CONTRIBUTING.md` を最終構成に合わせる。README のフォルダ構成節は、`ai-tools.yaml` の `readme` ブロックからの生成部分と手書き部分の境界を見直す（生成部分を増やせるなら増やす）。
- `docs/` の残り（`docs/integrations`、`docs/topics`）の行き先を 02 の決定どおりにし、`docs/index.md` と `maintenance/docs/index.md` の索引を直す。
- repo-meta スキル（`exploring-this-repo`、`meta`、`discovering-skills`、`changing-skills-and-tools`、`committing`）の地図・手順を新構成に合わせる。
- 旧パスの残存を全リポジトリで `rg` し、意図した残存（変更履歴など）以外をなくす。
- 完了記録を書き、`codegraph sync` で索引を作り直す。

## 読むべきファイル

### 全体ドキュメント

- `README.md`、`README_EN.md`、`AGENTS.md`、`CONTRIBUTING.md`
- `docs/index.md`、`maintenance/docs/index.md`、`docs/log.md`
- `tools/internal/plugin_meta/generate/generate_readme_tools_section.py`（05 の後は `maintenance/scripts/` 配下）

### repo-meta スキル

- `maintenance/plugin/skills/*/SKILL.md` と `maintenance/plugin/README.md`

## 触るファイル

- 変更: 上の全ファイル、`ai-tools.yaml`（`readme` ブロック）
- 変更: repo-meta スキルの SKILL.md（`meta.version` を上げる）
- 変更: 各サブモジュールの README（アンブレラ README との重複を消し、リンクにする）

## 決定事項・注意点／落とし穴

- README の ai-tools 節は生成物なので手で直さない。
- `README_EN.md` は日本語版と内容がずれやすい。日本語版の確定後にまとめて訳す。
- `.agents/rules/`、`.github/instructions/`、`.cursor/rules/` などは AGENTS.md からの生成物。ネストした AGENTS.md の移動で生成物の構成が変わるので、`agents-rules` を手動で再生成し、旧パス向けの生成ファイルが残っていないか確認する（lefthook では動かない）。

## ルール更新ポイント

- ルート `AGENTS.md`（本ステップで確定）: 新しい地図への入口、サブモジュール作業の 2 段階コミット、`just links-sync`、旧パスの記述を全削除。
- `maintenance/docs/repo-layout.md`（本ステップで確定）: 05〜08 で足した節を整理し、境界の判断基準を 1 か所にまとめる。

## 進め方

- **実行主体**: メインが進める。旧パスの残存確認と README_EN の翻訳はサブエージェントへ委任してよい。
- **TODO 化**: (1) ルートの文書、(2) docs の索引、(3) repo-meta スキル、(4) 旧パスの残存掃除と生成物の再生成、(5) 完了記録、の 5 TODO。
- **コミット**: (1)〜(4) をそれぞれ 1 コミット（`docs(repo): ...`。サブモジュール内の文書を変えたら、そのサブモジュール側のコミットとアンブレラのポインタ更新の 2 段階）。(5) の完了記録はプラン全体の `implementing-done` と同じ `docs(plans): ...` の 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（06 完了時）: [progress/06-agent-compat-results.md](progress/06-agent-compat-results.md)。06 で更新済みのもの: ルート README の AI ツール節（生成）・README_EN の同じ節・`maintenance/docs/claude-code-first-skills.md`・`ai-tools-config.md`・`repo-layout.md`・`docs/integrations/{codex,cline,claude-code}.md`・`docs/index.md`。09 で行うこと:
  - ルート `AGENTS.md`・README の「フォルダ構成」の残り（`agent-compat/` の説明、`.cline`・`.kilo` の生成コピー）を最終構成に合わせる。
  - `agent-compat/AGENTS.md` を含めて `agents-rules` を再生成する。
  - 06 の残課題（progress の「残課題」）を確認する。
- 2026-11-10（07 完了時）: [progress/07-submodule-results.md](progress/07-submodule-results.md)。07 で更新済み: `maintenance/docs/repo-layout.md` の「サブモジュール」節、`committing` スキル（2 段階コミット）、`lefthook-automation.md`・`gh-actions-lifecycle.md`、README の「取得」節、ルート `AGENTS.md` の 1 項目、CONTRIBUTING、`docs/integrations/{cli-tools,codex,claude-code}.md`。09 で行うこと:
  - README・README_EN の「フォルダ構成」で、4 つのフォルダがサブモジュールであることと各リポジトリへのリンクを示す。README_EN に「取得」節を足す。
  - `exploring-this-repo` の地図にサブモジュールと 2 段階コミットを反映する。`agents-rules` を再生成する（サブモジュールの中の AGENTS.md も対象になるか確認する）。
  - `site/tools-site/docs/index.md` が参照するルートの `repo-tools.yaml`（互換コピー）を `registry/repo-tools.yaml` に直すか決める。
