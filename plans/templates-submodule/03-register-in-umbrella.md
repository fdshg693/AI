---
type: Plan Step
status: implementing-done
---

# Step 3: アンブレラへの登録と検証

## やること

アンブレラの規約・README・保守スキル・コメントのサブモジュール一覧に `templates/` を足し、Junction・フック・ブランチ操作・CI 相当の検査が通ることを確認する。

## 読むべきファイル・実行推奨Grep

**登録箇所を洗い出すため（優先度: 高）**

- `git show --stat 579bb43` — `infra/` 登録時に触った 14 ファイル（このステップの一覧の元）
- Grep: `rg -n "infra/" AGENTS.md README.md README_EN.md CONTRIBUTING.md justfile maintenance/` — サブモジュールを列挙している箇所（`workflow / infra` のような並び）
- Grep: `rg -n "6 つ|6 submodules|six" README.md README_EN.md maintenance/` — サブモジュールの数

**検査の仕組みを確認するため（優先度: 中）**

- 読む: `maintenance/scripts/repo_git.py` — サブモジュールは `.gitmodules` から読む（スクリプト側の一覧更新は不要なはず。確認のみ）
- 読む: `.github/workflows/umbrella-check.yml` — `paths:` にサブモジュールのパスを列挙しているか

## 触るファイル

### 変更

- `AGENTS.md` — Behaviour のサブモジュール一覧
- `README.md`・`README_EN.md` — 「取得」の一覧、「サブモジュール」節に `templates/` の項目、`.gitmodules` の説明の数
- `CONTRIBUTING.md` — サブモジュール一覧
- `justfile`・`maintenance/lefthook/submodule.yml` — コメントの一覧
- `maintenance/docs/repo-layout.md` — description・冒頭の数・サブモジュール表・置き場所の判定基準に「運用テンプレート」行
- `maintenance/docs/index.md` — repo-layout の description（生成物なら再生成で更新）
- `maintenance/docs/gh-actions-lifecycle.md` — サブモジュール一覧
- `maintenance/plugin/skills/exploring-this-repo/SKILL.md`・`committing/SKILL.md`（・`discovering-skills/SKILL.md` に一覧があれば） — 一覧と数。frontmatter を変えたら `meta.version` を上げる
- `.github/workflows/*.yml` — `paths:` にサブモジュールを列挙しているものがあれば `templates` を足す

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                | 理由                                                                                            |
| ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 置き場所の判定基準の行: 「AI エージェントと使うリポジトリ運用のテンプレート（コピーして使う雛形・lint）→ `templates/core/<name>/`」 | スキル（`skills/`）・ツール（`tools/`）・保守用（`maintenance/`）のどれとも区別できるようにする |
| marketplace・`ai-tools.yaml`・スキル公開サイトには載せない                                                                          | templates はプラグインを含まない。`.claude/skills/template-*` はリポジトリ内作業用              |

- `README.md` の `ai-tools-section` は生成物なので触らない。
- アンブレラのコミットは「ポインタ・`.gitmodules`」と「文書の登録」を分ける（前例 c3cb74a / 579bb43 と同じ）。

### 検証

- `just sub-status`・`just branch-status` — `templates` が一覧に出て、作業ブランチにいる
- `just links-sync && just links-check` — `templates/` の Junction（`plans`・`committing`・`_umbrella/maintenance-docs`・`core/threads/planning`）が作られ、違反なし
- `just sub-hooks-install` 後、templates で空でない変更をコミットして pre-commit（Prettier・ruff・secretlint・main ガード）が走る
- `uv lock --check`
- templates の lint を一通り: `uv run core/plans/lint_plans.py --examples core/plans/references`、`uv run core/threads/link_plans.py --check`、`uv run starter/check_starters.py` ほか各 `lint_*.py`
- `uv run plans/lint_plans.py plans`（このプラン自身）
- `templates/` だけを Claude Code で開き、`committing` スキルが見えることを確認（任意）
- 全部通ったら `temp/templates` を削除する（削除前に中身が `templates/` と同一か `git -C templates status` と diff で確認）

## ルール更新ポイント

- `AGENTS.md`・`maintenance/docs/repo-layout.md`: 上の「触るファイル」のとおり（このステップ自体がルール更新）。

## 進め方

- 登録箇所の洗い出し（Grep）はメインのエージェントが行う。数が多ければ文書の書き換えだけ Explore ではなく general-purpose サブエージェントに委任してもよいが、repo-layout の判定基準の文言はメインが決める。
- TODO は「文書・スキルの登録（1 コミット）」「検証」「`temp/templates` 削除」の 3 つ。最後に完了記録を書いて overview を `implementing-done` にし、プランを削除する。
