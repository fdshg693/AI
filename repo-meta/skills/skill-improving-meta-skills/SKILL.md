---
# 例: .claude/skills/writing-skill, .claude/skills/skill-maintenance, repo-meta/skills/skill-meta-fields, repo-meta/skills/skill-md-commits
name: skill-improving-meta-skills
description: Explains this repository's pattern of meta-skills whose job is to maintain or evaluate other skills — auditing SKILL.md files against best practices, refreshing doc snapshots and propagating diffs into dependent skills, backfilling frontmatter metadata — rather than doing task work themselves. Use when deciding whether new guidance belongs in this meta layer versus as one-off instructions in some other skill, or when looking for the right tool to review/refresh/audit existing skills.
meta:
  requires_repo_tools: .claude/skills/writing-skill, .claude/skills/skill-maintenance, repo-meta/skills/skill-meta-fields, repo-meta/skills/skill-md-commits
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: writing-skill, skill-meta-fields, skill-md-commits, claude-code-first-skills
  status: stable
  description: no description
  version: 1.0.0
---

# スキルを改善するスキル（メタスキル層）

このリポジトリには、タスクそのものをこなすのではなく、**他のスキルの品質・鮮度を保つ**ためのスキルが複数の粒度で散らばっている。新しいガイダンスを書くとき、それが「タスクをこなす手順」なのか「スキル自体の面倒を見る手順」なのかを区別し、後者ならこの層に置く。

## 既存の例

- [.claude/skills/writing-skill](../../../.claude/skills/writing-skill/SKILL.md)（+ `writing-skill-complex`） — 新規作成・編集・評価。あらゆる`SKILL.md`が満たすべきチェックリストの一次情報源
- [.claude/skills/skill-maintenance](../../../.claude/skills/skill-maintenance/SKILL.md) — Claude CLI/Claude Code公式ドキュメントのスナップショットを更新し、意味のある差分を検出して依存スキルへ伝播させる
- `audit-skills`（Workflow） — 多数のスキルを一括でベストプラクティス採点する
- このリポジトリ自身: [skill-meta-fields](../skill-meta-fields/SKILL.md)（`meta:`frontmatterの補完）、[skill-md-commits](../skill-md-commits/SKILL.md)（コミット時の生成物・バージョンバンプ挙動の説明）

## 他ツールにも同種のメタスキルがある

Cline（`cline-skill-writer`）、Codex（`codex-skill-authoring`）、Copilot（`copilot-plugins/meta/writing-skills`）にも、それぞれ自分のツール向けの「スキルの書き方スキル」がある。これは[claude-code-first-skills](../claude-code-first-skills/SKILL.md)の方針どおり、**そのツール自身のスキル機構についてのスキル**であり、Claude Codeの`writing-skill`をポートしたものではない。

## この層のスキル自体もベストプラクティスに従う

メタスキルだからといって特別扱いはせず、通常の`SKILL.md`と同じ`bestpractices.md`のチェックリスト（[writing-skill](../../../.claude/skills/writing-skill/SKILL.md)参照）に従う。対象がたまたま「他のスキル」であるだけで、frontmatter・自由度の設計・分量の目安は変わらない。

## この層に置くべきかの判断

新しいガイダンスが「スキル自体の形・品質・鮮度」（frontmatterの網羅性、チェックリストへの準拠、外部ドキュメントに対する陳腐化）についてのものであれば、既存のツールを使い回す手順の一部として書くのではなく、この層のスキルとして独立させることを検討する。

## 関連

- [writing-skill](../../../.claude/skills/writing-skill/SKILL.md) — 新規作成・編集・評価の共通チェックリスト
- [skill-meta-fields](../skill-meta-fields/SKILL.md) / [skill-md-commits](../skill-md-commits/SKILL.md) — `meta:`ブロックというこのリポジトリ独自の観点に絞ったメタスキル
- [claude-code-first-skills](../claude-code-first-skills/SKILL.md) — 他ツールのメタスキルとの棲み分け
- [repo-ssot-pattern](../repo-ssot-pattern/SKILL.md) — 同じ「ドリフトを防ぐ」発想を生成ファイル側に適用したもの

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、このスキルを`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](../ai-tools-config/SKILL.md)参照。
