---
type: Plan Step
status: implementing-done
---

# Step 2: サブモジュールの定型ファイルをそろえる

## やること

`templates/` の中に、既存サブモジュール（`infra/` を手本）と同じ定型ファイルを足し、templates 自身の `plans/` をアンブレラの `plans/` への Junction に置き換える。整形（Prettier・ruff）を別コミットで一括適用する。

## 読むべきファイル・実行推奨Grep

**手本を確認するため（優先度: 高）**

- 読む: `infra/.links.yaml`・`infra/lefthook.yml`・`infra/.gitignore`・`infra/.gitattributes`・`infra/CLAUDE.md`・`infra/AGENTS.md`・`infra/.claude/skill-tools.hooks.example.yaml` — そのまま写す土台
- 読む: `skills/.links.yaml` — `plans` の Junction 宣言の書き方（`infra` には無い）
- 読む: `maintenance/docs/repo-layout.md`「サブモジュールを単体で開く」「Junction はコミットせず `.links.yaml` で宣言する」「禁止事項」

**templates 側の現状を確認するため（優先度: 中）**

- 読む: `templates/CLAUDE.md` — 現状は README 相当の本文が CLAUDE.md に直接書かれている
- 読む: `templates/core/threads/link_plans.py`・`templates/.gitignore` 末尾 — `core/threads/planning` の作り方と除外
- 読む: `templates/.claude/skills/template-*/SKILL.md` — 指示ファイルの移動で壊れる相対リンクが無いか
- Grep: `rg -n 'plans/' templates --glob '!core/**' --glob '!starter/**'` — templates の `plans/` を前提にした記述

## 触るファイル

### 新規

- `templates/lefthook.yml` — `extends: [../maintenance/lefthook/submodule.yml]`
- `templates/.links.yaml` — `.claude/skills/committing`、`plans`（→ アンブレラ `plans`）、`_umbrella/maintenance-docs`、`core/threads/planning`（→ `templates/core/plans`）
- `templates/README.md` — 現 `CLAUDE.md` の本文（人間向けの説明）
- `templates/AGENTS.md` — `@./README.md` ＋「このフォルダだけを開いたとき」節
- `templates/.gitattributes`・`templates/LICENSE`（MIT、他サブモジュールと同じ）
- `templates/.claude/skill-tools.hooks.example.yaml`

### 変更

- `templates/CLAUDE.md` — `@./AGENTS.md` の 1 行だけにする
- `templates/.gitignore` — `infra/.gitignore` の共通部分（Claude Code のフック生成物・`.skill-tools/`・`.codegraph/` 等）を足し、templates 固有の行（`vault_index.sqlite`・`core/threads/planning/`）は残す。`plans` の Junction は `links-sync` が `info/exclude` に登録するので gitignore 不要
- `templates/plans/` — 削除（完了済みプラン `threads-template/` は Step 1 の初回コミットに残っている）

## 決定事項・注意点／落とし穴

| 決定                                                                                                 | 理由                                                                                                                                       |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `core/threads/planning` の Junction は `.links.yaml` に宣言し、`link_plans.py` は単体 clone 用に残す | アンブレラ配下では `just links-sync` に一本化する規約。`link_plans.py` は templates を単体で使う人向けの公開手順で、消すと単体利用が壊れる |
| 整形の一括適用は定型ファイルとは別コミット（`style:`）にする                                         | 取り込み直後に既存 md・py を初めて編集した時点で Prettier・ruff の大きな差分が混ざるのを避ける                                             |

- `.links.yaml` の `target` はアンブレラ相対。`core/threads/planning` の target は `templates/core/plans` と書く。宣言したら `just links-check` が通ること（祖先を指さない・重なりなし）を確認する。
- templates の lint スクリプト（`lint_*.py`・`check_starters.py`）が `core/threads/planning` の Junction を辿らないこと。`temp/web-lookup/0002-*` に `rglob` が Junction を辿る問題の調査メモがあるので、取り込み前に対処済みか確認する。
- サブモジュールの pre-commit は `precommit-check` で SKILL.md を検査する。`.claude/skills/template-*/SKILL.md` が meta フィールド・version バンプ検査の対象になるか、最初のコミットで確認する（対象なら `meta` を `registry/meta_field.yaml` に合わせる）。
- `CLAUDE.md` から `README.md` に本文を移すと、`.claude/skills/template-*` などから `CLAUDE.md` へのリンクが切れる可能性がある。上の Grep で確認する。

## ルール更新ポイント

- `templates/AGENTS.md`「このフォルダだけを開いたとき」節: `plans/` はアンブレラに属する、`core/threads/planning` は `just links-sync` で作る（単体 clone なら `uv run core/threads/link_plans.py`）、共通手順は repo-layout へのリンク。

## 進め方

- メインのエージェントが直接進める。TODO は「定型ファイル追加と `plans/` 削除」「整形の一括適用」の 2 つ（各 1 コミット）。コミットは `committing` スキルのラッパーを使う。
- 各コミット後、アンブレラで `git add templates` してポインタを更新する（Step 3 のコミットにまとめてもよい）。
