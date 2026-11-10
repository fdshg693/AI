---
type: Plan Step
status: planning-research
---

# Step 6: マルチ AI 対応の分離、ツール別書式サンプルと相違点ドキュメント

> [00-overview.md](00-overview.md) の続き。04 が完了し、05 のバッチ 1〜4 が終わっていること。05 のバッチ 5（他ツールの知識スキルの移動）は、本ステップの配布方式（生成器）と同じコミットで行う。01 の観点 D（1 ディレクトリに複数ツールのマニフェストを同居できるか）の結果で配布方式を確定させる。

## やること

- このリポジトリの都合で行っているマルチ AI 対応の仕組みを `agent-compat/` に集める。対象: `agent-tooling/`（フック・コンテキスト注入）、各ツール向けマーケットプレイス・マニフェストの生成設定、AGENTS.md から各ツールのルールを作る設定。
- 他ツール向けの配布は「スキルの実体は 1 か所（`skills/`・`tools/_plugin/`）、各ツールのマニフェストは生成物」にする。ツールごとのスキルのコピーは持たない。
- ツール固有の書式でなければ意味がないものを `agent-compat/formats/<tool>/` に最小サンプルとして切り出す（skill／plugin／rule／memory の 4 種、必要なものだけ）。元の知識スキルからはサンプルへのリンクにする。
- Claude Code を基準にした「他ツールでの書き方の相違点」を `agent-compat/docs/differences/` に別軸でまとめる（ツール × 観点の表と、ツール別の注意点）。各ツールの `*-skill-writer`／`writing-skills` 系スキルはこれを参照する。

## 読むべきファイル

### 現在のマルチ AI 対応の仕組み

- `ai-tools.yaml`（tools ブロック全体、`skills_layout`、`marketplace`、`rules_from_agents_md`）
- `maintenance/docs/ai-tools-config.md`（旧 `docs/repo-wide/ai-tools-config.md`）、`claude-code-first-skills.md`、`hook-distribution.md`
- `agent-tooling/README.md`、`agent-tooling/AGENTS.md`、`agent-tooling/agent_tooling/adapters/README.md`
- `tools/agents-rules/README.md`、`tools/agents-rules/agents_rules/targets.py`
- `.agents/README.md`、`_agents/README.md`、`.cursor/rules/README.md`、`.github/agents/README.md`、`.github/skills/README.md`

### サンプル・相違点の元ネタ

- `copilot-plugins/meta/writing-skills`、`writing-plugins`、`writing-copilot-instructions`
- `.cline/skills/cline-skill-writer`、`cline-plugin-writer`、`cline-rule-writer`
- `.kilo/skills/kilo-skill-guide`、`kilo-plugin-writer`、`kilo-agent-writer`
- `cursor-plugins/meta/skills/cursor-skill-use`、`cursor-plugin-use`
- `codex-plugins/meta/skills/codex-skill-authoring`、`codex-hooks`
- `_agents/plugins/antigravity-meta/skills/antigravity-skills`、`antigravity-memory`
- （05 の後は、いずれも `skills/plugins/ai-tools-knowledge/` 配下の新パスで読む）
- `claude-plugins/meta/skills/writing-skill`（Claude Code 側の基準。05 の後は `skills/plugins/claude-code/`）

## 触るファイル

- 移動: `agent-tooling/` → `agent-compat/agent-tooling/`（`pyproject.toml` の members、`repo-hooks.yaml` の `catalog`、`lefthook.yml` の glob、`justfile` を追従）。深さが 1 段増えるので、`agent_tooling/hooks/build/build.py:810`（`package_root.parent.parent / "repo-tools.yaml"`。registry/ 移動も重なる）と、tests の `parents[2]`（`conftest.py`、`test_codex_parity.py`、`test_builder.py` の `REPO_ROOT`）を直す
- 移動: 他ツールの知識スキル 42 件 → `skills/plugins/ai-tools-knowledge/skills/`（対応表は [progress/02-mapping.md](progress/02-mapping.md)。05 のバッチ 5 と同じコミット）。名前の衝突を避けるため、copilot の `writing-plugins` → `copilot-writing-plugins`、`writing-skills` → `copilot-writing-skills` に改名する
- 移動: `cline-plugins/personal-info` → `agent-compat/formats/cline/personal-info`（`docs/integrations/justfile:60` の相対パス、`docs/integrations/cline.md`、`ai-tools.yaml:80` を追従）
- 移動（サンプル）: `codex-plugins/meta/skills/*/agents/openai.yaml`（5 件）→ `agent-compat/formats/codex/`。copilot 側に混入した `agents/openai.yaml`（github-copilot-observability-docs、writing-copilot-instructions）は削除する
- 変更: `agent-tooling/agent_tooling/hooks/REFERENCES.md`（他ツールスキルへのパス 30 か所）、`tools/agents-rules/agents_rules/targets.py:9`、`agent-tooling/.../adapters/codex/nested_agents_md.py:7,11`、`site/skills-site/tests/publication.test.mjs`、`.github/workflows/skill-site.yml` の `paths:`
- 変更: 知識スキル本文のうち、このリポジトリ固有の段落（codex-memory:82、codex-skill-authoring:26、cursor-plugin-use:75、cursor-memory の memory.md:98、cursor-skill-use の authoring.md:70）を削るか、maintenance 側へ移す
- 新規: `agent-compat/README.md`／`AGENTS.md`／`CLAUDE.md`、`agent-compat/formats/<tool>/**`、`agent-compat/docs/differences/index.md` と `<tool>.md`
- 新規または変更: 各ツール向けマニフェストの生成器（`maintenance/scripts/plugin_meta/generate/`）。01 の結果次第で、プラグインディレクトリへの `.codex-plugin`／`.cursor-plugin` マニフェスト生成か、`.agents/plugins/marketplace.json` 等からのパス参照か、を選ぶ
- 変更: `ai-tools.yaml`（各ツールの `plugins` を新しい実体パスへ。`workspace` 種別の `.cline`・`.kilo`・`.github` は、実体を `skills/` に置いたうえで、ワークスペース直下のフォルダを Junction か生成物にする）
- 変更: 知識スキルの本文（書式説明をサンプル・相違点ドキュメントへのリンクに置き換え。`meta.version` を上げる）
- 削除: 中身が空になった `.cline/skills/`、`.kilo/skills/` の実体（Junction か生成物へ置き換え）

## 決定事項・注意点／落とし穴

- **知識とサンプルの線引き**: 「Codex の hooks はどう設定するか」は知識（`skills/` に残す）。「Codex 用 SKILL.md の frontmatter はこう書く」という、そのツールで読ませて初めて意味がある実物はサンプル（`agent-compat/formats/` へ）。迷ったら知識側に残す。
- **ワークスペース直下の設定フォルダ**: Cline・Kilo・Copilot は `.cline/skills`・`.kilo/skills`・`.github/skills` をワークスペース直下から読む。実体を移すと、そのツールでアンブレラを開いたときにスキルが見えなくなる。04 の `.links.yaml`（アンブレラ用）で Junction を張るか、生成器でコピーを作るかを 01 の結果で決める。依頼は「Junction は Claude Code 限定」なので、**コピー生成に決定**（01 完了時）。Junction にすると exclude が必須になり、元の実ディレクトリを追跡していた古いコミットとの `switch` で参照先が上書き・削除される（01-A）ので、ここでは使わない。生成先は 04 の除外の仕組みに登録し、スキャナの二重計上を防ぐ。
- **マニフェストの同居（01-D）**: 1 つのプラグインディレクトリに `.claude-plugin/plugin.json`・`.codex-plugin/`・`.cursor-plugin/`・ルートの `plugin.json`（Copilot）を並べられる。ただしルートの `plugin.json` は Cursor も Agent Plugins 標準として読み、標準はスキルを `skills/` 直下に置く前提。現 `copilot-plugins/meta/plugin.json` はスキル名の配列でスキルを plugin 直下に置いているので、同居させるならスキルを `skills/` 配下へ揃える。
- **フックの配布元の移動**: `.claude/hooks/` などのインストール済みコピーはソースパスを含む可能性がある。移動後に `just hooks-install` で入れ直し、`just hooks-installed` で確認する。
- 相違点ドキュメントは OKF（`okf-spec`）の概念ドキュメント形式で書き、`maintenance/docs` と同じ索引の作法に揃える。
- `skills-site` は他ツールのスキルも「そのツール向け」として表示している。移動後の表示区分（ツールでなくトピックとして表示するか）を `site/skills-site/AGENTS.md` の方針に沿って決める。

## ルール更新ポイント

- `maintenance/docs/claude-code-first-skills.md`（本ステップ）: 「他ツール向けフォルダにはメタスキルだけ」→「知識スキルも Claude Code スキルとして `skills/` に置き、書式の差は `agent-compat` にまとめる」へ改稿。
- `maintenance/docs/ai-tools-config.md`（本ステップ）: `plugins` の `path` が実体を指すこと、マニフェストが生成物であること。
- `agent-compat/AGENTS.md`（本ステップで新規）: このフォルダの責務（マルチ AI 対応の仕組み・サンプル・相違点のみ。スキルの実体は置かない）。

## 進め方

- **実行主体**: 構成と生成器はメイン。ツール別のサンプル作成と相違点の下書きは、ツールごとにサブエージェントへ並列委任する（元スキルと公式ドキュメントの写しを読ませ、Claude Code との差だけを返させる）。採否・統合はメイン。
- **TODO 化**: (1) `agent-tooling` の移動、(2) 配布方式の実装（生成器）、(3) ツール別サンプル、(4) 相違点ドキュメント、(5) 知識スキル本文の差し替え、の 5 TODO。
- **コミット**: (1)〜(5) をそれぞれ 1 コミット。ただし (2) は 05 のバッチ 5（知識スキルの移動）と同じ 1 コミットにする（分けると間の状態で Cline 等がスキルを見失う）。(3)(4) をサブエージェントに並列で書かせた場合も、コミットはメインが採否を決めたあとに 1 回。ステップ完了時にプラン更新を 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（01 完了時）: ワークスペース直下の他ツール用フォルダはコピー生成に決定し、マニフェスト同居の条件（Copilot の `plugin.json` はスキルを `skills/` 配下へ揃える）を「決定事項」に加えた。
- 2026-11-10（02 完了時）: 「触るファイル」に、02 の対応表の具体的な移動と改名を追加した。追加したのは、agent-tooling の深さ +1 で直す箇所、`cline-plugins/personal-info` の行き先、`openai.yaml` の扱い、REFERENCES.md などの参照元。
