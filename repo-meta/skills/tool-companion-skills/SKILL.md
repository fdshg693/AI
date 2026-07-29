---
# 例: claude-plugins/my-tools/skills/aim-cli（tools/aimの使い方スキル）
name: tool-companion-skills
description: Explains the repository's pattern of pairing a tools/ convenience script with a SKILL.md that documents just its non-obvious usage decisions (e.g. claude-plugins/my-tools/skills/aim-cli for the `aim` CLI), so a human or agent isn't left guessing which flag/model/enum value to pick. Use when adding a new tool under tools/ and deciding whether it needs a companion skill, or when writing one.
meta:
  requires_repo_tools: claude-plugins/my-tools/skills/aim-cli/SKILL.md, tools/aim
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: ai-tools-config, skill-meta-fields, claude-code-first-skills
  status: stable
  description: no description
  version: 1.0.0
---

# ツールへの使い方スキル併設

`tools/`配下のCLI・スクリプトは、必要に応じて対応する使い方スキル（例: `tools/aim`に対する`claude-plugins/my-tools/skills/aim-cli`）を持つ。人間・エージェントが実行方法に迷わないための補助であり、すべてのツールに機械的に用意するものではない。

## 併設するかどうかの判断

`--help`だけで完結するツールには不要。次のように**判断が絡む**部分がある場合にだけ検討する。

- どのenum値・フラグを選ぶべきかの判断基準（`aim-cli`スキルのモデル選択表とエスカレーション方針: `minimax-m3`を基本線に、簡単すぎるタスクは`gpt-oss-120b`、力不足なら`glm-5.2`/`gpt-5.6-luna`へ）
- 出力フォーマットや終了コードの意味論で、扱いを誤ると後続処理に影響するもの
- ログファイルの意味論（例: `tools/aim/logs/calls.jsonl`は応答本文を含まず`cost`/`*_tokens`のみ記録、という制約を知らないと誤った前提で後続処理を組んでしまう）

## 置き場所

使い方スキルは`repo-meta/skills/`ではなく、Claude Codeプラグイン配下（例: `claude-plugins/my-tools/skills/<tool-name>/`）に置き、`ai-tools.yaml`へ通常のスキルとして登録する（[ai-tools-config](../ai-tools-config/SKILL.md)参照）。対象ツール自体がこのリポジトリ外でも使えるものである以上、スキルもマーケットプレイス・skills-siteの配布対象にする。`repo-meta/`直下には置かない。

## 責務の境界: セットアップは扱わない

使い方スキルは**使い方のみ**を扱い、インストール・初期セットアップには踏み込まない。

- 前提条件（PATH上に`aim`が必要、`OPENROUTER_API_KEY`が必要、等）はfrontmatterの`#`コメントと本文冒頭の「前提条件」節に明記する
- 前提条件が満たされていない場合、スキル自身がインストールを試みるのではなく、ツールのREADME.mdのセットアップ手順をユーザーに案内するよう指示する

## frontmatterのmeta

対象ツールへの依存を`meta:`に反映する。

```yaml
meta:
  requires_repo_tools: aim
  requires_install: uv tool install --editable tools/aim
  requires_env: OPENROUTER_API_KEY
```

詳細は[skill-meta-fields](../skill-meta-fields/SKILL.md)参照。

## Claude Code以外のツールへは自動的に広げない

同じツールに対応するスキルを他のAIツール（Cline/Codex/Copilot等）向けにも用意するかは別問題。このパターンはデフォルトでClaude Code向けであり、他ツールに機械的にポートしない理由は[claude-code-first-skills](../claude-code-first-skills/SKILL.md)を参照。

## 関連

- [tools-directory-layout](../tools-directory-layout/SKILL.md) — ツール自体のディレクトリ・CLI化規約
- [ai-tools-config](../ai-tools-config/SKILL.md) — スキルを`ai-tools.yaml`へ登録する手順
- [skill-meta-fields](../skill-meta-fields/SKILL.md) — `meta:`ブロックの各フィールドの意味
- [claude-code-first-skills](../claude-code-first-skills/SKILL.md) — 他AIツールへポートしない/する判断

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、このスキルを`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](../ai-tools-config/SKILL.md)参照。
