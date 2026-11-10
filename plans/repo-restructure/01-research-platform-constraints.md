---
type: Plan Step
status: ready
---

# Step 1: Junction・サブモジュール・各ツールの挙動の事前調査

> [00-overview.md](00-overview.md) の続き。このステップではコードを書かない。確定した前提は 04・06・07・08 のプラン本文へ直接反映する。

## やること

Windows の Junction と Git サブモジュールを組み合わせたときに、Git・Claude Code・このリポジトリのスキャナ類・CI・パッケージマネージャがどう振る舞うかを調べ、設計の前提を確定させる。可能な項目は `temp/` の使い捨てリポジトリで実験して確かめる。

## 調査観点・キーワード

### A. Git × Junction（最優先。04 の設計を左右する）

- Git for Windows は Junction（`IO_REPARSE_TAG_MOUNT_POINT`）を、実ディレクトリとして辿るか、symlink として扱うか、無視するか。`git status`・`git add -A` の結果を実験で確かめる。
- `.git/info/exclude` に書いた Junction パスが確実に無視されるか。
- `git clean -fdx`／`-X`・`git checkout` を実行したとき、Junction の参照先の中身が消えないか（データ消失リスク）。exclude に登録した Junction は `git clean -x/-X` の削除対象になるので、特に確かめる。
- サブモジュールの中で exclude ファイルの位置（`git rev-parse --git-path info/exclude`）。
- git worktree を作ったときに、Junction とサブモジュールがどう見えるか。

### B. Claude Code × Junction／サブフォルダ起動

- `.claude/skills/<name>` が Junction のとき、スキルとして発見されるか。`.claude/skills` 全体を Junction にした場合はどうか。
- `.claude/rules/*.md`・`.claude/agents/` も Junction 経由で読まれるか。
- `CLAUDE.md` の `@../...`（プロジェクト外を指す import）は読み込まれるか。承認プロンプトが出るか。アンブレラから開いたときにネストした CLAUDE.md が親を二重読込しないか。
- 現状、`meta-plugins` は `claude --plugin-dir ./meta-plugins` で読み込んでいる（marketplace には載っていない）。これを前提に、`--plugin-dir`・`.claude/settings.json` の `extraKnownMarketplaces`／`enabledPlugins` で、サブフォルダ起動時にアンブレラのプラグイン（`maintenance/plugin`）を読ませられるか。Junction より適切ならそちらを採る。
- フック設定の `${CLAUDE_PROJECT_DIR}` はサブフォルダ起動時にサブフォルダを指す。`.claude/settings.json` は gitignore 対象で、`just hooks-install` が生成する。サブモジュールごとに `hooks-install` を実行する方式で足りるかを調べる（`.claude/hooks` の Junction は、`.env`・`logs/`・`state/` の共有とアンブレラ側の実体書き換えを招くので採らない）。
- 参照: `claude-plugins/meta/skills/claude-code-docs`、`claude-code-memory`、`writing-plugins` スキル（公式ドキュメントの写し）。

### C. スキャナ × Junction（二重計上・無限ループ）

- Python 3.13 の `Path.rglob`・`os.walk(followlinks=False)`・`Path.is_junction()` は Junction を辿るか。
- `rg`、prettier、ruff、pytest（コレクション）、lefthook の glob、codegraph、textgraph、Astro の glob、VS Code の検索は Junction を辿るか。
- このリポジトリの `**/SKILL.md` 走査箇所（`tools/internal/plugin_meta`、`site/skills-site/scripts`、`tools/skill-tools`、`agent-tooling`）を列挙し、それぞれの走査方法を記録する。

### D. サブモジュール × 配布・CI

- Claude Code の `/plugin marketplace add fdshg693/AI` はサブモジュールを取得するか。取得しないなら、marketplace.json の `source` を `github`／`git-subdir` 形式（サブモジュール側リポジトリを直接指す）にできるか。
- Codex（`.agents/plugins/marketplace.json`）、Copilot（`.github/plugin/marketplace.json`、plugin.json の `skills` パス指定）、Cursor（`.cursor-plugin`）で同じ問い。1 つのプラグインディレクトリに複数ツールのマニフェストを同居させられるか。
- `skill-tools` の GitHub ソース（raw 取得）がサブモジュール内のファイルをどう解決するか（`tools/skill-tools/skill_tools/` の source 実装を読む）。
- GitHub Actions: `actions/checkout` の `submodules: recursive`、private サブモジュールのトークン、`paths:` フィルタがサブモジュールのポインタ更新でしか発火しない点。
- Azure Static Web Apps デプロイ・`tool-release.yml` のタグ付けへの影響。
- **go/no-go 判定**: 外部利用者が `fdshg693/AI` の marketplace からサブモジュール内のプラグインをインストールできない場合（`git-subdir` などでも代替できない場合）、`skills/` と `tools/_plugin` はサブモジュールにしない。代替構成は「意味的再編（05・06）はそのまま行い、サブモジュール化は `agent-compat/`・`site/` などの配布に関わらない単位に限る」。判定結果を 00 の目標構成と 07 へ反映する。

### E. ワークスペース・フック

- uv workspace の members がサブモジュール内にあっても `uv sync` が通るか。サブモジュールのフォルダだけを開いて `uv run` したときにアンブレラの `pyproject.toml` を見つけるか。
- pnpm workspace で同じ問い。
- lefthook はサブモジュール内のコミットで発火しない。サブモジュールごとに `lefthook.yml` を置くか、アンブレラの設定を `extends` するか。

## 調査結果（後続ステップから参照する）

（未実施）

## 進め方

- **実行主体**: A・C の実験（`temp/` での使い捨てリポジトリ）と D の公式ドキュメント調査は、観点ごとにサブエージェントへ委任し、要約と出典だけを返させる。採否はメインが判断する。B は `claude-code-guide` サブエージェントに問い合わせ、重要な点は実機で確かめる。
- **TODO 化**: 観点 A〜E をそれぞれ 1 TODO。結果を本節へ要約し、04・06・07・08 の本文を更新したら完了。
