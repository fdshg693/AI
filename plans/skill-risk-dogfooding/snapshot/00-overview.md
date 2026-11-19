---
type: Plan
status: planning-breakdown
---

## 実装ステータス

- [ ] [01-research-signals.md](01-research-signals.md) — 危うさの判断に使える既存シグナルの調査
- [ ] [02-risk-inputs.md](02-risk-inputs.md) — 変化しやすさの宣言とドッグフーディング台帳の器を作る
- [ ] [03-rank-skill-risk.md](03-rank-skill-risk.md) — スキルの危うさランキングを出す照会スクリプト
- [ ] [04-dogfooding-skill.md](04-dogfooding-skill.md) — 選ぶ→ドッグフーディング→改善を回すメンテスキルと導線

# 全体スキルメンテの仕組み（危うさランキング → ドッグフーディング → 改善） 実装プラン - 概要

## 要件

- リポジトリ全体の `SKILL.md`（約 136 件。`skills/plugins/`・`tools/_plugin/`・`agent-compat/_plugin/`・`maintenance/plugin/`）から、**いま一番危ういスキル**を根拠付きで選べるようにする。
- 「危うさ」は少なくとも次の 2 つを認識して判断する（元の依頼の必須条件）。
  - **最後の変更**: そのスキルが最後に変わった日、最後に実際に使って確かめた（ドッグフーディングした）日。
  - **変更の入りやすさ**: 次の 3 つで測る。(a) git から計算する変更頻度（一定期間のコミット数、直近で直しが続いているか）、(b) スキルの題材（外部ツールの仕様など）が変わりやすいかの宣言、(c) 最後の変更以降に依存先（自作ツール・他スキル）が実際に変わったか。(a) と (c) は自動で計算し、手で書くのは (b) だけにする。
- 選んだスキルを実際の作業に近い形で使ってみて（ドッグフーディング）、壊れている・古い・起動しないといった問題を記録する。
- 記録した問題をもとにスキルを改善し、ドッグフーディングした事実を残して次回のランキングに反映する。1 回の周回で直すのは原則 1 スキル。

## 実装ステップ

1. [01-research-signals.md](01-research-signals.md) — 既存シグナル（git 履歴、`meta.status`、依存関係、`skill-tools --fb`、`agent-logs`）がどこまで使えるかの調査
2. [02-risk-inputs.md](02-risk-inputs.md) — git から取れない入力（変化しやすさの宣言・ドッグフーディング台帳）の置き場所と書式を作る
3. [03-rank-skill-risk.md](03-rank-skill-risk.md) — `maintenance/scripts/skill/query/` に危うさランキングの照会スクリプトと just レシピを足す
4. [04-dogfooding-skill.md](04-dogfooding-skill.md) — `maintenance/plugin/skills/` に周回手順のスキルを足し、`maintenance/docs/`・`meta` スキルから辿れるようにする

## 主要な決定事項

| 決定 | 理由 |
| ---- | ---- |
| 危うさは「点数 1 個」ではなく、要因ごとの内訳（最後の変更からの日数、最後のドッグフーディングからの日数、変化しやすさ、依存先の変化、未対応フィードバック数）と並べて出す | 選んだ理由を人とエージェントが確かめられないと、ランキングを信用できず周回が続かない |
| 「最後の変更」と変更頻度は git 履歴から毎回計算し、どこにも書き込まない | 手で書く日付はすぐ古くなる。サブモジュールの履歴は 2026-11-10 の再編から始まり、それより前はアンブレラ側に旧パスで残っている（対応表は `maintenance/scripts/reorg/tables/*.json`）。つなぐか切るかは Step1 で決める |
| スキルのキーは skill-tools の canonical ID（リポジトリ相対の `.../SKILL.md` パス）にそろえる | `skill-tools --fb` と台帳を照合できるようにするため。名前だけの `meta.requires_skills` は名前→パスに変換し、同じ名前が複数あるときは「曖昧」として出す |
| `skill-tools --fb` が使えないスキル（`ai-tools.yaml` 未登録の `maintenance/plugin/`・`templates/.claude/skills/`）は、fb 件数を「対象外」とし、ドッグフーディングの本文は台帳の短い `note` に残す | `--fb` はカタログに登録されたものしか解決できない。`maintenance/plugin` を登録しない方針は変えない |
| 「変化しやすさ」は `SKILL.md` の `meta:` に足さず、プラグイン・パス単位の規則で決め、個別の上書きだけを持つ（置き場所は Step2 で確定） | `meta:` に足すと全 136 件の `meta.version` を上げることになり（`check_skill_version_bump.py`）、差分が大きすぎる。外部ツールの知識スキル（`ai-tools-knowledge`・`cc-knowledge` 等）はまとめて「高い」と言えるので規則で十分 |
| ドッグフーディングの結果は 2 か所に分けて残す。本文（何が起きたか）は既存の `skill-tools --fb`、日付と判定（ok / 要改善 / 改善済み）はコミットする台帳 | `--fb` の保存先 `tools/skill-tools/fb/` は gitignore されていて端末をまたげず、ランキングの入力にできない。台帳は短い構造化データだけにして、本文を二重に持たない |
| ドッグフーディングは、新しいコンテキストのサブエージェントに「スキル名を伝えずに」現実的な依頼をさせて行う | スキル名を伝えると description による自動起動を確かめられない。起動しない・誤起動もよくある壊れ方 |
| 改善は既存の手順（`writing-skill`、`changing-skills-and-tools`、`committing`）に渡し、新しいスキルの中に書き方の規則を重ねない | 書き方の正本は `writing-skill`。二重管理を避ける |
| Claude 関連スキルの公式ドキュメント追随（`skill-maintenance`）は置き換えず、ランキングの入力に使える範囲でだけつなぐ | `skill-maintenance` は「上流が変わったか」を差分で見る仕組みで、役割が違う |

## 未決事項（Step1 の結果で決める）

- 再編より前の履歴をつなぐか切るか。一括書き換えのコミット（`chore`、`refactor(repo)` のパス書き換えなど）を除外するか。
- ランキングの対象範囲。`find_skill_md_files` が返す全件か、`templates/.claude/skills/` を除くか。
- 変化しやすさの段階（例: high / medium / low）と、プラグイン単位の既定値。
- 点数の重み付け。最初は単純な合成（変化しやすさ × 経過日数 + 依存先の変化 + 未対応 fb）で始め、数回回して直すか。
- 利用頻度（`agent-logs` で Skill ツールの呼び出し回数が取れるなら）を「よく使うのに古い＝危うい」として入れるか。入れるなら端末ローカルの情報なので任意入力にする。
- 定期実行（`workflow/schedule/`）にするか、手動起動だけにするか。本プランは手動起動までを対象とする。

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照。パスは Step1・Step2 の結果で変わりうる）

### 新規

- 変化しやすさの規則と上書き（候補: `registry/skill-volatility.yaml`）
- ドッグフーディング台帳（候補: `maintenance/state/skill-dogfood.yaml`）
- `maintenance/scripts/skill/query/rank_skill_risk.py` とそのテスト（`maintenance/scripts/tests/`）
- `maintenance/plugin/skills/skill-dogfooding/SKILL.md`（必要なら `scripts/`）
- 仕組みの説明（`maintenance/docs/skill-improving-meta-skills.md` への追記か、新規 `maintenance/docs/skill-risk-maintenance.md`）

### 変更

- `maintenance/scripts/justfile`（`skill-risk` レシピ）
- `maintenance/scripts/skill/AGENTS.md`（`query/` の一覧）
- `maintenance/plugin/skills/meta/SKILL.md`（選び方の表）
- 新しい yaml を `registry/` に置くなら、yaml 名を列挙している `AGENTS.md`・`README.md`・`README_EN.md`
- `maintenance/state/` を新しく作るなら `maintenance/README.md`（サブフォルダの一覧）

## ルール更新ポイント

- `AGENTS.md`・`README.md`・`README_EN.md` の SSOT yaml 一覧（Step2）: `registry/` に新しい yaml を足した場合だけ名前を追加する。
- `maintenance/README.md`（Step2）: `maintenance/state/` を作った場合、サブフォルダの一覧に追加する。
- `maintenance/scripts/skill/AGENTS.md`（Step3）: `query/` の列挙に `rank_skill_risk.py` を足す。
- `maintenance/docs/`（Step4）: 仕組み全体（シグナル、台帳、周回手順、`skill-maintenance` との棲み分け）を書く。`meta` スキルのキーワード表に「どのスキルを直すべきか」「ドッグフーディング」を足す。

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま 1 つの TODO にする。Step1 の結果で Step2〜4 の「触るファイル」「決定事項」を書き換えてから Step2 に着手する。
- Step2〜3 が終わった時点で一度ランキングを出してユーザーに見せ、上位が直感と合うかを確かめてから Step4 に進む。
