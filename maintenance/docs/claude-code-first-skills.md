---
type: Design Decision
title: Claude Code中心のスキル方針
description: Explains this repository's policy that SKILL.md content is written for Claude Code specifically (exploiting its frontmatter mechanisms like allowed-tools, disable-model-invocation, dynamic `!command` context injection, and this repo's own meta block); knowledge about other AI tools is also kept as Claude Code skills in skills/plugins/ai-tools-knowledge and reaches those tools through generated marketplaces or gitignored workspace copies, while tool-specific format samples and the differences from Claude Code live in agent-compat/. Use when deciding whether a skill belongs under skills/plugins/cc-knowledge, ai-tools-knowledge or another skills/plugins/ plugin, whether to port an existing Claude Code skill to another tool, or where a tool-specific SKILL.md/plugin format example should go.
tags: [claude-code, cline, codex, copilot, cursor, antigravity, repo-wide]
generated: { by: reference_agent/cline-glm-5.2, at: 2026-08-09T14:39:30Z }
status: stable
---

# Claude Code中心のスキル方針

このリポジトリのスキルの大部分はClaude Code向けに書かれており、他のAIコーディングツール（Cline/Codex/Copilot/Cursor/Antigravity/Kilo）について持つのは、原則としてその**ツール自体の使い方に関する知識スキルだけ**である。それも Claude Code スキルとして `skills/plugins/ai-tools-knowledge/` に 1 か所で置く。1個のタスク向けスキルを全ツールへ機械的にポートする方針ではない。

## 実態の比較

- `skills/plugins/*/skills/` — このリポジトリの大半のタスク特化スキルの本体（`writing-hooks`、`ai-tools-config`、`claude-mechanisms`、`proposing-flow`等）
- `skills/plugins/ai-tools-knowledge/skills/` — `<tool>-cli-docs`・`<tool>-docs`・`<tool>-sdk-docs`・`<tool>-skill-writer`/`plugin-writer`/`rule-writer`のような、**そのツール自体を使うための知識スキル**
- 他ツールへの届け方は 2 通りで、どちらもスキルのコピーをコミットしない。Codex・Copilot・Cursor は、このプラグインに同梱したそれぞれのマニフェスト（`.codex-plugin/plugin.json`、ルートの `plugin.json`、`.cursor-plugin/plugin.json`）を、生成したマーケットプレイスから指す。ワークスペース直下からしか読まない Cline・Kilo・Antigravity には、`registry/ai-tools.yaml` の `workspace_copies` に従って gitignore 済みのコピーを `just agent-compat-sync` で作る（[ai-tools-config](./ai-tools-config.md)）
- `agent-compat/` — スキルの実体は置かない。マルチ AI 対応の仕組み（`agent-tooling`）、ツール固有書式の最小サンプル（`formats/<tool>/`）、Claude Code との書き方の相違点（`docs/differences/`）

## なぜポートしないか

Claude CodeのSKILL.mdフロントマターには他ツールの機構では1:1に再現できない仕組みがある。

- `disable-model-invocation`（モデルによる自動起動を止め、明示呼び出し専用にする）
- `allowed-tools`（そのスキル実行中に使えるツールを絞る）
- `` !`command` `` 形式の動的コンテキスト注入（スキル読み込み時にコマンドを実行し結果を埋め込む）
- `meta:`ブロック（Claude Code自体の機能ではなく、このリポジトリ独自の運用。詳細は[skill-meta-fields](./skill-meta-fields.md)）

これらの仕組みを前提にしたスキルをそのまま他ツールへコピーしても、その挙動（明示呼び出し限定、ツール制限、事前注入）は再現されず、静かに壊れる。

## 横断が必要な内容は「生成」で扱う

このリポジトリでは、複数ツールに同じ内容を持たせたい場合もスキルを手でポートするのではなく、共通のソースから生成する。`.clinerules/agents-*.md`と`.github/instructions/*.instructions.md`は各プラグインの`AGENTS.md`から生成される（SKILL.mdの内容からではない。詳細は[ai-tools-config](./ai-tools-config.md)）。

## 判断の目安

「これをCline/Codex/Copilotにも追加して」と言われたら、まず次を切り分ける。

1. 対象が**そのツール自体の使い方**（CLIオプション、SDK、プラグインの書き方等）についてのガイドなら、`skills/plugins/ai-tools-knowledge/skills/` に `<tool>-*` の知識スキルとして追加する。そのツールで読ませて初めて意味がある実物（そのツール用の frontmatter を持つ SKILL.md、マニフェスト等）は `agent-compat/formats/<tool>/` のサンプルにし、知識スキルからはリンクする
2. 対象がClaude-Code特有の仕組みに依存したワークフロースキルなら、基本的にポートしない。どうしても必要なら、Claude Code専用の仕組みを取り除き、そのツール自身の流儀で書き直す

`ai-tools.yaml`の`skills_layout`（`subdir`/`direct`）はあくまで各ツールが実際に使うSKILL.md配置形式の違いを表すフィールドであり、Claude Code側のレイアウトをコピーしたものではない（[ai-tools-config](./ai-tools-config.md)参照）。

## 関連

- [ai-tools-config](./ai-tools-config.md) — `AGENTS.md`からのCline/Copilot向け生成、`skills_layout`の意味
- [tool-companion-skills](./tool-companion-skills.md) — 便利ツールへの使い方スキル併設もデフォルトはClaude Code向け
- [skill-improving-meta-skills](./skill-improving-meta-skills.md) — 各ツールが持つ「スキルを書くためのスキル」自体もツールごとに独立している

## このドキュメントの位置づけ

`maintenance/plugin/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、この内容を`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](./ai-tools-config.md)参照。
