---
type: Plan Step
status: ready
---

# Step 2: 全スキル・ツール・docs の分類表とパス参照の棚卸し

> [00-overview.md](00-overview.md) の続き。このステップではファイルを移動しない。成果物の対応表は 05・06 の入力になる。

## やること

リポジトリ内の全 SKILL.md・プラグイン・tools・docs を、移動先カテゴリに分類した対応表（旧パス → 新パス）を作る。あわせて、移動で壊れるパス参照（コード・設定・CI・ドキュメント・外部契約）を一覧にする。対応表は `progress/02-mapping.md` に置き、ユーザーの確認を取る。

## 調査観点・キーワード

### 分類（1 スキル 1 行）

- 対象: `cline-plugins/personal-info`（SKILL.md ではない Cline 用 AgentPlugin）、`claude-plugins/*/skills/*`、`meta-plugins/skills/*`、`codex-plugins/meta/skills/*`、`copilot-plugins/meta/*`、`cursor-plugins/meta/skills/*`、`_agents/plugins/antigravity-meta/skills/*`、`.cline/skills/*`、`.kilo/skills/*`、`.github/skills/`、`claude-plugins/*/agents`、`output-styles`。
- カテゴリ:
  - `generic`: tools にもこのリポジトリにも依存しない
  - `tool-companion`: `meta.requires_repo_tools` が `none` 以外、または本文が `tools/<name>` の CLI を前提にする
  - `repo-meta`: このリポジトリの構造・SSOT・生成物を前提にする（例: `claude-plugins/meta/skills/skill-maintenance` は `claude-plugins/meta/skills` を保守するので repo-meta 候補。`writing-skill` の bestpractices を `audit-skills` ワークフローが参照するなどの依存も記録する）
  - `ai-tool-knowledge`: Claude Code 以外の AI ツールの使い方の知識（Claude Code スキルとして読めるもの）
  - `format-sample`: ツール固有の書式でなければ意味がない部分（frontmatter キーの違い、`direct` レイアウト等）。スキルの中から切り出す部分を特定する
- 各行に記録する: 現パス、カテゴリ、移動先、`meta.requires_repo_tools`／`requires_skills`、他スキル・ツールから参照されているか、判断理由（1 行）。
- 判断が割れるもの（例: `aim-cli` と `aim-lib`、`writing-skill-web` は uv member、`okf-spec` は docs/ が依存）は「要確認」として残す。

### tools と docs

- `tools/*` を、配布 CLI／ラッパー／実験／リポジトリ内部（`tools/internal`、`tools/infra`）に分ける。`tools/README.md` の区分と突き合わせる。
- `docs/repo-wide`（repo-meta）、`docs/integrations`（利用者向けの導入手順）、`docs/topics`（汎用知識）の行き先を決める。
- `templates/` 相当（plans はテンプレートとしても配布されている）の扱い。

### パス参照の棚卸し

- `rg` で旧パス（`claude-plugins/`、`meta-plugins/`、`codex-plugins/`、`copilot-plugins/`、`cursor-plugins/`、`_agents/`、`.cline/skills`、`.kilo/skills`、`agent-tooling/`、`tools/internal`、`docs/repo-wide`、`ai-tools.yaml` ほか SSOT 名）を検索する。`node_modules`、`.venv`、`dist`、`output/`、`generated/`、`temp/` は除く。
- 種類別に分ける: コードのハードコード（例: `tools/skill-tools/skill_tools/config/__init__.py` の `DEFAULT_SELF_SKILL`）、SSOT yaml、生成器の入力、CI の `paths:`（`.github/workflows/skill-site.yml`）、lefthook の glob、justfile、Markdown リンク、SKILL.md 本文。
- 外部契約: marketplace の `source`、`skill-tools` の GitHub ソースが読むパス、他プロジェクトに配置済みの `.skill-tools` マニフェスト・ジャーナルが記録する source パス、skills-site の URL、README のインストール手順、`repo-workflows.yaml` の canonical ID、`skill-tools --fb` の保存先キー。
- リポジトリ外の参照: `~/.claude/settings.json`（`extraKnownMarketplaces` の `directory`、`statusLine` のスクリプトパス）、Windows タスクスケジューラの登録（`tools/scheule` 配下）、`uv tool install --editable` 済みのツール（editable のパスを持つ）。
- 追跡外ファイル: 移動対象フォルダ内の ignore 対象（`.env`、`.venv`、`logs/`、`fb/`、`state/`、sqlite 等）の一覧（`git status --ignored`）。05・07 で移設・退避する。
- 過去の移動用スクリプト `temp/rewrite_moved_paths.py` が再利用できるか確認する。

## 調査結果（後続ステップから参照する）

（未実施）

## 進め方

- **実行主体**: 分類の下書きはプラグイン単位でサブエージェントへ並列委任し、表の行だけを返させる（読み取り専用）。パス参照の棚卸しはメインが `rg` で行う。カテゴリの最終判断と「要確認」の解消はメインが行い、対応表をユーザーに確認してもらう。
- **TODO 化**: (1) 分類下書き、(2) パス参照の棚卸し、(3) 対応表のユーザー確認、の 3 TODO。確認後に 05・06 の「触るファイル」を対応表で更新したら完了。
