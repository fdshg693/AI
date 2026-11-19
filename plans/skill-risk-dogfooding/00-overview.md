---
type: Plan
status: implementing-done
---

## 実装ステータス

- [x] [01-research-signals.md](01-research-signals.md) — 危うさの判断に使える既存シグナルの調査
- [x] [02-risk-inputs.md](02-risk-inputs.md) — 変化しやすさの宣言とドッグフーディング台帳の器を作る
- [x] [03-rank-skill-risk.md](03-rank-skill-risk.md) — スキルの危うさランキングを出す照会スクリプト
- [x] [04-dogfooding-skill.md](04-dogfooding-skill.md) — 選ぶ→ドッグフーディング→改善を回すメンテスキルと導線

# 全体スキルメンテの仕組み（危うさランキング → ドッグフーディング → 改善） 実装プラン - 概要

## 要件

- リポジトリ全体の `SKILL.md`（4 ルート `skills/plugins/`・`tools/_plugin/`・`agent-compat/_plugin/`・`maintenance/plugin/` の 136 件から、入れ子の部品 6 件を除いた 130 件）から、**いま一番危ういスキル**を根拠付きで選べるようにする。
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

| 決定                                                                                                                                                                                                                                                           | 理由                                                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 危うさは「点数 1 個」ではなく、要因ごとの内訳（最後の変更からの日数、最後のドッグフーディングからの日数、変化しやすさ、依存先の変化、未対応フィードバック数）と並べて出す                                                                                      | 選んだ理由を人とエージェントが確かめられないと、ランキングを信用できず周回が続かない                                                                                                                                                                                    |
| 「最後の変更」と変更頻度は git 履歴から毎回計算し、どこにも書き込まない。2026-11-10 より前は切り、取り込み以降に実質的な変更がないスキルは「基準日（2026-11-10 以前）」とする                                                                                  | 手で書く日付はすぐ古くなる。アンブレラもサブモジュールも履歴は 2026-11-10 の取り込み・移動から始まり、それより前の履歴はどこにも残っていない（Step1）                                                                                                                   |
| 一括書き換えのコミットは「件名が `refactor(repo)` か `chore(repo): import` で始まる、またはファイル数 > 100」で除外する                                                                                                                                        | type だけでは分けられない（`refactor(tools)` の 453 ファイルのパス書き換えと、`docs(skills)` の 13 SKILL.md の本物の更新がある）。この規則で移動・取り込み・大きなパス書き換えだけが落ちる（Step1）                                                                     |
| 対象は 4 ルートの前方一致で絞り、祖先ディレクトリにも `SKILL.md` がある入れ子（`special` の `sub_skills/`・`sub_commands/`）を外す                                                                                                                             | `find_skill_md_files` は `.claude/skills/`（sync-skills のコピー）・`temp/`・`templates/.claude/skills/` も返し、同じスキルを二重に数える（Step1）                                                                                                                      |
| スキルのキーは skill-tools の canonical ID（リポジトリ相対の `.../SKILL.md` パス）にそろえる                                                                                                                                                                   | `skill-tools --fb` と台帳を照合できるようにするため。名前だけの `meta.requires_skills` は名前→パスに変換し、同じ名前が複数あるときは「曖昧」として出す                                                                                                                  |
| `skill-tools --fb` が使えないスキル（`ai-tools.yaml` 未登録の `maintenance/plugin/`・`templates/.claude/skills/`）は、fb 件数を「対象外」とし、ドッグフーディングの本文は台帳の短い `note` に残す                                                              | `--fb` はカタログに登録されたものしか解決できない。`maintenance/plugin` を登録しない方針は変えない                                                                                                                                                                      |
| 「変化しやすさ」は `SKILL.md` の `meta:` に足さず、プラグイン・パス単位の規則で決め、個別の上書きだけを持つ（`maintenance/skill-risk/volatility.yaml`）                                                                                                        | `meta:` に足すと全 136 件の `meta.version` を上げることになり（`check_skill_version_bump.py`）、差分が大きすぎる。外部ツールの知識スキル（`ai-tools-knowledge`・`cc-knowledge` 等）はまとめて「高い」と言えるので規則で十分                                             |
| 2 つの手編集入力（規則・台帳）は `registry/` ではなく `maintenance/skill-risk/` に置く                                                                                                                                                                         | 読むのは Step3 のスクリプト 1 本だけで「複数の生成物・検査が読む」SSOT の条件に当たらず、リポジトリ都合（`repo-layout` の判定基準）。`registry/` だと `precommit-fix` の全体再生成と SSOT 一覧 3 ファイルの更新が付いてくる（Step2）                                    |
| ドッグフーディングの結果は 2 か所に分けて残す。本文（何が起きたか）は既存の `skill-tools --fb`、日付と判定（ok / 要改善 / 改善済み）はコミットする台帳                                                                                                         | `--fb` の保存先 `tools/skill-tools/fb/` は gitignore されていて端末をまたげず、ランキングの入力にできない。台帳は短い構造化データだけにして、本文を二重に持たない                                                                                                       |
| ドッグフーディングは、scratch ディレクトリで `claude -p --plugin-dir <対象プラグイン> --setting-sources "" --output-format stream-json` を起動し、「スキル名を伝えずに」現実的な依頼をさせて行う。起動したかは stream-json の `Skill` の `tool_use` で判定する | スキル名を伝えると description による自動起動を確かめられない。Agent ツールのサブエージェントは親と同じスキル集合（`.claude/skills/` の 10 件など）しか持たず、大半のスキルの起動を確かめられない。`--plugin-dir` なら全プラグインで確かめられることを Step1 で確認した |
| 利用頻度（`agent-logs`）は入れない                                                                                                                                                                                                                             | Skill ツールの呼び出しは数えられるが、30 日で 16 種・97 回しかなく、Skill ツールを通らない使われ方（`Read` で直接読む等）が多い（Step1）                                                                                                                                |
| 改善は既存の手順（`writing-skill`、`changing-skills-and-tools`、`committing`）に渡し、新しいスキルの中に書き方の規則を重ねない                                                                                                                                 | 書き方の正本は `writing-skill`。二重管理を避ける                                                                                                                                                                                                                        |
| Claude 関連スキルの公式ドキュメント追随（`skill-maintenance`）は置き換えず、ランキングの入力に使える範囲でだけつなぐ                                                                                                                                           | `skill-maintenance` は「上流が変わったか」を差分で見る仕組みで、役割が違う                                                                                                                                                                                              |

## 未決事項

- 点数の重み付け。最初は単純な合成（変化しやすさ × 経過日数 + 依存先の変化 + 未ドッグフーディング + 未対応 fb）で始め、Step3 の後にユーザーに上位を見せて直す。今は履歴が 9 日分しかなく、経過日数の差が小さいことに注意する。
- 定期実行（`workflow/schedule/`）は本プランの対象外とし、手動起動だけにする。

## Step1 で決めたこと

- 再編より前の履歴: つながない（存在しない）。
- 対象範囲: 4 ルート − 入れ子 = 130 件。`templates/.claude/skills/` は外す。
- 変化しやすさ: `high` / `medium` / `low` の 3 段階。プラグイン単位の既定値は Step2 に記載。
- 変更頻度の期間: 履歴が短いので直近 30 日のコミット数にする（90 日は意味を持たない）。

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照。パスは Step2 の結果で変わりうる）

### 新規

- 変化しやすさの規則と上書き: `maintenance/skill-risk/volatility.yaml`（Step2 で作成済み）
- ドッグフーディング台帳: `maintenance/skill-risk/dogfood.yaml`（Step2 で空の器を作成済み）
- `maintenance/scripts/skill/query/rank_skill_risk.py` とそのテスト（`maintenance/scripts/tests/`）
- `maintenance/plugin/skills/skill-dogfooding/SKILL.md` と `scripts/run_dogfood.py`・`scripts/record_dogfood.py`
- 仕組みの説明: `maintenance/docs/skill-risk-maintenance.md`（新規。`skill-improving-meta-skills.md` からは 1 行で辿る）

### 変更

- `maintenance/scripts/justfile`（`skill-risk` レシピ）
- `maintenance/scripts/skill/AGENTS.md`（`query/` の一覧）
- `maintenance/plugin/skills/meta/SKILL.md`（選び方の表）
- `maintenance/README.md`（サブフォルダの一覧に `skill-risk/` を追加。Step2 で済み）
- `maintenance/plugin/.claude-plugin/plugin.json`（`name` を `maintenance` に。Step4 で判明）
- `maintenance/docs/skill-improving-meta-skills.md`（メタスキル一覧に 1 行）

## ルール更新ポイント

- `maintenance/README.md`（Step2）: サブフォルダの一覧に `skill-risk/` を追加した（済み）。`registry/` には置かなかったので SSOT yaml 一覧（`AGENTS.md`・`README.md`・`README_EN.md`）は変えない。
- `maintenance/scripts/skill/AGENTS.md`（Step3）: `query/` の列挙に `rank_skill_risk.py` を足す。
- `maintenance/docs/`（Step4）: 仕組み全体（シグナル、台帳、周回手順、`skill-maintenance` との棲み分け）を書く。`meta` スキルのキーワード表に「どのスキルを直すべきか」「ドッグフーディング」を足す。

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま 1 つの TODO にする。Step1 の結果は Step2〜4 に反映済み（2026-11-19）。
- Step2〜3 が終わった時点で一度ランキングを出してユーザーに見せ、上位が直感と合うかを確かめてから Step4 に進む。

## 実行中に判明した変更

- 2026-11-19（Step1）: 履歴の扱い・一括コミットの除外・対象範囲・ドッグフーディングの起動方法・利用頻度を決定事項に追加し、「未決事項」を残りだけにした。詳細は [01-research-signals.md](01-research-signals.md) の調査結果。
- 2026-11-19（Step2）: 規則と台帳の置き場所を `maintenance/skill-risk/volatility.yaml`・`maintenance/skill-risk/dogfood.yaml` に確定し、決定事項・ファイル一覧・ルール更新ポイントから `registry/`・`maintenance/state/` の分岐を消した。
- 2026-11-19（Step3）: ランキングを実装した（`just --justfile maintenance/scripts/justfile skill-risk`）。計画に無かった加点として、台帳の判定 `needs-fix` を足した。経過日数は最後の変更と最後のドッグフーディングの新しい方から数える。重みの初期値は [03-rank-skill-risk.md](03-rank-skill-risk.md) の「実行中に判明した変更」にある。上位 10 件をユーザーが確認し、重みは初期値のままで了承された。
- 2026-11-19（Step4）: ドッグフーディングの権限は `dontAsk` ＋ 読み取り系の既定許可 ＋ 外部書き込みの常時拒否に決め、未決事項から外した。`maintenance/plugin` のマニフェスト名がスラッシュを含み `--plugin-dir` で読み込めなくなっていたので `maintenance` に直した。1 周目は `claude-code-openai-gateway` を直して台帳を `fixed` にした。詳細は [04-dogfooding-skill.md](04-dogfooding-skill.md) の「実行中に判明した変更」。
