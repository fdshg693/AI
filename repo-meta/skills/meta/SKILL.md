---
# 同梱: scripts/list_sibling_skills.py — 同階層(repo-meta/skills/*)のSKILL.mdをスキャンし、
# name/descriptionの一覧をこのSKILL.md読み込み時に動的注入する（手書きの一覧は持たない）
name: meta
description: Points to the single most relevant sibling skill under repo-meta/skills/ for a given repository-maintenance task (SKILL.md quality checklist, meta: frontmatter fields, SSOT+regeneration pattern, tools/ directory layout, lefthook/justfile wiring, aim automation, etc.). Use when starting work under repo-meta/, or hitting a skill/tooling drift, staleness, or consistency question and unsure which existing repo-meta skill already covers it, before writing new one-off guidance.
meta:
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: no description
  version: 1.0.0
---

!`python ${CLAUDE_SKILL_DIR}/scripts/list_sibling_skills.py`

# repo-meta配下のスキル選択

`repo-meta/skills/`には、このリポジトリ自身のメンテナンスを扱う複数のメタスキルが並んでいる。新しい判断ロジックをその場で書く前に、まず上の一覧（このスキル読み込み時にスクリプトが同階層の各`SKILL.md`から生成した最新の`name`/`description`）から既存スキルが対象を既にカバっていないか確認する。

## 選び方

1. 上の一覧の`description`を読み、対象タスクのキーワード（触ろうとしているファイル・症状・操作）に最も一致する1件を選ぶ。
2. 複数該当しそうな場合は、対象がどの事実・仕組みについてかで絞り込む。
   - `SKILL.md`の`meta:`フィールドの意味・埋め方 → `skill-meta-fields`
   - `SKILL.md`をコミットした時のlefthook挙動（生成物再生成・バージョンバンプ） → `skill-md-commits`
   - 複数ファイルに渡って一致させたい事実をSSOT+生成で管理するパターン全般 → `repo-ssot-pattern`（`ai-tools.yaml`固有の話なら`ai-tools-config`）
   - `tools/`配下の新規スクリプト・CLIの置き方 → `tools-directory-layout`（Pythonパッケージ化の要否は`uv-workspace`）
   - 便利ツールに使い方スキルを併設するかの判断 → `tool-companion-skills`
   - lefthook/justfileのレシピ追加・挙動 → `lefthook-automation` / `justfile-conventions`
   - `aim`系ツールで単純作業を自動化すべきか → `aim-automation`
   - スキルをClaude Code以外（Cline/Codex/Copilot等）へポートすべきか → `claude-code-first-skills`
   - この「他スキルの面倒を見るスキル」という層自体の存在意義・新規追加の判断 → `skill-improving-meta-skills`
3. 一覧のどれにも合致しなければ、無理に既存スキルへ寄せない。新規スキルとして追加すべきかの判断・フロントマター規約は[skill-improving-meta-skills](../skill-improving-meta-skills/SKILL.md)と[writing-skill](../../../.claude/skills/writing-skill/SKILL.md)を使う。

## 一覧が期待と違うとき

一覧生成スクリプトは`repo-meta/skills/`直下でこのスキルと同階層にある`SKILL.md`だけを対象にする。新しいスキルを追加したのに出てこない場合、そのfrontmatterが`---`で始まり`name`/`description`が（`meta:`のようなネストではなく）トップレベルのキーになっているかを確認する。`[ERROR]`行が出た場合は該当`SKILL.md`のfrontmatterを直接確認する。

## 関連

- [skill-improving-meta-skills](../skill-improving-meta-skills/SKILL.md) — このメタスキル層自体の存在意義、新規追加の判断基準
- [writing-skill](../../../.claude/skills/writing-skill/SKILL.md) — 新規スキルのフロントマター・チェックリスト

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、このスキルを`ai-tools.yaml`へ登録しないこと。
