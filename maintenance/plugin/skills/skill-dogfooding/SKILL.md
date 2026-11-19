---
# 1 回の周回（選ぶ → ドッグフーディング → 記録 → 改善）を進める。ファイル変更・API 費用を伴うので明示的に呼んだときだけ使う。
# 同梱: scripts/run_dogfood.py — 隔離した claude -p でシナリオを 1 件走らせ、要約だけを返す（stdlib のみ）
#       scripts/record_dogfood.py — 台帳 maintenance/skill-risk/dogfood.yaml の 1 エントリを書く（PyYAML）
# 仕組みの説明（シグナル・合成点・台帳・他のメタスキルとの棲み分け）の正本は maintenance/docs/skill-risk-maintenance.md。
# maintenance/plugin は配布しない。ai-tools.yaml には登録しない。
name: skill-dogfooding
description: Runs one skill-maintenance cycle in this repository — picks the riskiest skill from the skill-risk ranking, dogfoods it in an isolated `claude -p --plugin-dir` session with realistic requests, records the result in maintenance/skill-risk/dogfood.yaml (and skill-tools --fb), then fixes the skill. Use when explicitly asked to dogfood a skill or decide which skill to fix next.
disable-model-invocation: true
argument-hint: "[canonical ID (.../SKILL.md) or skill name — omit to pick from the ranking]"
allowed-tools: Bash(just --justfile maintenance/scripts/justfile skill-risk *), Bash(uv run python ${CLAUDE_SKILL_DIR}/scripts/*.py *)
meta:
  tag: []
  requires_repo_tools: maintenance/scripts/skill/query/rank_skill_risk.py, maintenance/skill-risk/dogfood.yaml, skill-tools
  requires_env: none
  dependencies: claude, uv, pyyaml
  requires_install: none
  requires_hooks: none
  requires_skills: writing-skill, changing-skills-and-tools, committing, skill-tools-cli
  status: experimental
  description: 危うさランキングで選んだスキルを隔離 claude -p でドッグフーディングし、台帳に記録して直す周回手順
  version: 0.1.1
---

## 危うさランキング（上位 5 件）

!`just --justfile maintenance/scripts/justfile skill-risk --top 5`

# スキルのドッグフーディング周回

1 回の周回で 1 スキルを、選ぶ → ドッグフーディング → 記録 → 改善 の順に進める。仕組みの説明（各要因と合成点、台帳、`skill-maintenance`・`audit-skills` との棲み分け）は[skill-risk-maintenance](../../../docs/skill-risk-maintenance.md)。

このプラグインはマーケットプレイスに無い。リポジトリルートで `claude --plugin-dir ./maintenance/plugin` として起動したセッションで使う。

引数: `$ARGUMENTS`

## 1. 選ぶ

- 引数があればそれを対象にする（スキル名なら canonical ID に直す）。
- 無ければ上のランキングを見せ、上位からユーザーと 1 件決める。`why:` の行が選んだ理由になる。外部へ書き込むスキル（`gh-pr`、Azure、Issue 作成など）は、読み取りだけのシナリオで足りるかをこの時点で確認する。
- 出力が期待と違う・もっと見たいときは `just --justfile maintenance/scripts/justfile skill-risk --top 20`（`--json` で内訳）。

1 周 = 1 スキル。複数件を一度に直すと、どの改善が効いたか分からなくなる。

## 2. シナリオを作る

対象の `SKILL.md`（と、本文が案内する参照ファイル）を読み、実際に頼まれそうな依頼を 2〜3 件作る。

- 1 件は **スキル名を出さない**依頼にする。description による自動起動を確かめるため。
- 1 件はスキルの中心の手順を最後まで通す依頼にする。参照型スキルなら「取り出せるか（必要な情報が見つかるか）」「応用できるか」を試す依頼にする。
- 依頼は外部に書き込まずに完了できる形にする（「PR を作って」ではなく「PR 本文の案を出して」）。
- 公式ドキュメントのスナップショット（`references/`・`output/` など）を正として答えるスキルは、シナリオとは別に、スナップショットと一次情報（元 URL の現行版、スキル同梱の取得・検査スクリプト）の差分を取る。隔離セッションはスナップショットを信じて答えるので、古さを自分からは報告しない。

## 3. ドッグフーディング

シナリオごとに同梱スクリプトで隔離した `claude -p` を走らせる。Agent ツールのサブエージェントは親と同じスキル集合しか持たないので、自動起動の確認には使わない。

```text
uv run python ${CLAUDE_SKILL_DIR}/scripts/run_dogfood.py \
  --plugin-dir <対象プラグインのディレクトリ> --expect-skill <スキル名> \
  --workdir <scratchpad>/dogfood-<スキル名>-<n> --prompt "<依頼>" \
  [--allow "Bash(<必要なコマンド>:*)" ...] [--add-dir <読ませるディレクトリ>]
```

- `--plugin-dir` は `SKILL.md` から上にたどって `.claude-plugin/plugin.json` がある最初のディレクトリ（例 `skills/plugins/topics`、`tools/_plugin/my-tools`、`maintenance/plugin`）。
- スクリプトは設定・フック・他プラグイン・MCP を切り離し（`--setting-sources ""`・`--strict-mcp-config`）、`--permission-mode dontAsk` で許可リスト外のツールを確認なしに拒否する。既定の許可は読み取り系（`Read`・`Grep`・`Skill`・`WebFetch`・`git log` など）だけで、push・PR・Issue・`gh api`・クラウド CLI は常に拒否する。中身は `--dry-run` で確認できる。
- **対象スキルが実行するコマンドは `--allow` で渡す**。動的コンテキスト（`` !`...` `` の行）と本文の手順にあるコマンドのうち、外部に書き込まないものを渡す（例: `--allow "Bash(uv run:*)"`）。渡し忘れると、スキル自体は起動しても動的コンテキストが「tool errors」に出て中身が空になる。それはスキルの不具合ではないので、許可を足して走らせ直す。
- リポジトリのファイルを読む・`just` を叩くスキルは `--add-dir C:/C/ai` などでリポジトリを読ませる。作業ディレクトリは scratchpad のままにする。
- 作業ディレクトリが scratchpad でも、`--allow` で渡したスクリプトはスキルの中のファイル（`output/` のスナップショットなど）を絶対パスで書き換えることがある。シナリオごとに対象リポジトリ（サブモジュールならその中）で `git status` を見て、走らせたことで変わったファイルは `git checkout -- <path>` で戻す。改善の材料にはしない。
- モデルの既定は `sonnet`。起動するかだけを見るなら `--model haiku` で安く済む。費用の上限は既定 $1（`--max-budget-usd`）。
- 依頼には「最後に 4 点（使ったもの・最後まで進めたか・実在しなかった/古かったもの・迷った箇所）を報告する」指示が自動で足される。スキル名は足さない。改善案は書かせない。採否はメインが決める。

結果の読み方:

| 出力                                      | 意味                                                                                                                     |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `plugin skills loaded: 0`・`plugin error` | プラグイン自体が読み込まれていない（マニフェストの `name` が不正など）。シナリオの結果は使えない。先にプラグインを直す   |
| `expected skill ...: NOT INVOKED`         | スキル名を出さない依頼で起動しなかった。description の書き方を疑う（スキル名を出した依頼でも起動しないなら別の原因）     |
| `tool errors` / `permission denials`      | 許可を渡し忘れたものか、スキルが前提にしているコマンド・パスが無いものかを切り分ける。前者は走らせ直す                   |
| 最終回答の 3・4                           | 古い仕様・存在しないパス・説明と違う挙動の候補。対象 `SKILL.md` と実物（`--help`、ファイル、公式ドキュメント）で裏を取る |
| `raw stream`                              | 要約で判断できないときだけ、`Grep` で該当箇所を探す。全文は読まない                                                      |

## 4. 記録

判定を決める: 直すべき問題が裏の取れた形で 1 つ以上あれば `needs-fix`、無ければ `ok`。

1. **本文（何が起きたか）**: シナリオ、起動したか、見つけた問題を `skill-tools --fb` に残す（[skill-tools-cli](../../../../tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md)）。

   ```text
   skill-tools --fb <canonical ID> --fb-kind skill --fb-text "<本文>"
   ```

   出力された保存パスのファイル名（`YYYYMMDD-HHMMSS-fb.md`）を控える。カタログ未登録のスキル（`maintenance/plugin/` の 7 件など。ランキングの `fb` 列が `n/a`）は `--fb` が使えないので飛ばし、要点を次の `--note` に 1 行で書く。

2. **台帳**: リポジトリルートから同梱スクリプトで書く（yaml を手で編集しない）。

   ```text
   uv run python ${CLAUDE_SKILL_DIR}/scripts/record_dogfood.py <canonical ID> --verdict <ok|needs-fix> [--fb <ファイル名> | --note "<1 行>"]
   ```

## 5. 改善

`needs-fix` なら直す。直さずに終えるときは台帳を `needs-fix` のまま残す（次回のランキングで上位に残る）。

1. 書き方の基準は [writing-skill](../../../../skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md)、影響範囲は [changing-skills-and-tools](../changing-skills-and-tools/SKILL.md)。ドッグフーディングで裏の取れた問題だけを直す。ついでの書き換えはしない。
2. `meta.version` を上げる（[skill-md-commits](../../../docs/skill-md-commits.md)）。
3. 直したシナリオだけ手順 3 をもう一度走らせ、問題が消えたことを確かめる。
4. [committing](../committing/SKILL.md) に従ってコミットする。対象がサブモジュール（`skills/`・`tools/`・`agent-compat/`）にあれば、中でコミットしてからアンブレラでポインタを更新する。
5. 台帳を `fixed` にし、改善コミットを `<repo>@<short-hash>`（`repo` は `umbrella` かサブモジュールのパス）で記録する。台帳の変更はアンブレラでコミットする。

   ```text
   uv run python ${CLAUDE_SKILL_DIR}/scripts/record_dogfood.py <canonical ID> --verdict fixed --fix skills@<short-hash> --keep
   ```

   `--keep` で既存の `fb`・`note` を残す。

## やらないこと

- 1 周で複数のスキルを直す
- ドッグフーディングの `claude -p` に、外部へ書き込む許可（`git push`・`gh pr create` など）を `--allow` で渡す。必要なシナリオは読み取りだけに組み替えるか、ユーザーに確認する
- 書き方の規則をこのスキルや対象スキルに新しく書き足す（正本は `writing-skill`）

## このスキルの位置づけ

`maintenance/plugin/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。`ai-tools.yaml`へ登録しないこと。
