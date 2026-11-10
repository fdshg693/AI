---
type: Plan Step
status: planning-research
---

# Step 8: サブモジュール単体で開くための Claude Code 用 Junction・指示ファイル

> [00-overview.md](00-overview.md) の続き。07 でサブモジュール化が済んでいること。01 の観点 B（Claude Code × Junction／サブフォルダ起動）の結果に従う。

## やること

各サブモジュールのフォルダだけを Claude Code で開いたときに、そのフォルダでの作業に必要なスキル・ルール・関連ファイルが見えるようにする。

- 各サブモジュールの `.links.yaml` に、そこで使う Junction を宣言する。例:
  - `.claude/skills/<name>` → アンブレラの `maintenance/plugin/skills/<name>`（`committing`、`changing-skills-and-tools` など、そのサブモジュールで必要な repo-meta スキル）
  - `skills/` で作業するなら `writing-skill` 系は自分の中にあるので不要。`tools/` で作業するなら `skills/plugins/claude-code/skills/writing-skill` など
  - 強く結びついた兄弟・上位フォルダ（例: `tools/` から `registry/`、`site/` から `registry/` と `skills/`）を `_umbrella/<name>` のような明示的な名前で
- 各サブモジュールに `CLAUDE.md`（`@./AGENTS.md`）と `AGENTS.md` を置く。アンブレラ全体の規約のうち必要なものは、01 の結果に応じて `@` import か、Junction 経由のパスで読み込む。
- フックは、サブモジュールごとに `just hooks-install`（skill-tools）を実行して入れる。`.claude/settings.json` は gitignore 対象の生成物なのでコミットしない。`.claude/hooks` の Junction は使わない（`.env`・`logs/`・`state/` を共有してしまい、サブモジュールでの `hooks-install` がアンブレラ側の実体を書き換えるため）。サブモジュール用のフック設定ファイル（`.claude/skill-tools.hooks.yaml` 相当）とレシピだけをコミットする。
- アンブレラのプラグイン（`maintenance/plugin`）は、01 の観点 B の結果に応じて、`--plugin-dir`／`extraKnownMarketplaces`／`.claude/skills` Junction のいずれかで読み込む。
- 各サブモジュールを実際に単体で開き、確認項目を満たすか検証する。

## 読むべきファイル

### サブフォルダ起動時の挙動

- 01 の調査結果（観点 B）
- `.claude/settings.json`（フックが `${CLAUDE_PROJECT_DIR}/.claude/hooks/...` を指している）、`.claude/skill-tools.hooks.yaml`、ルート `justfile` の `hooks-install`
- `maintenance/docs/hook-distribution.md`（旧 `docs/repo-wide/hook-distribution.md`）
- `agent-compat/agent-tooling/agent_tooling/hooks/scenarios/nested_agents_md/`（ネスト AGENTS.md の注入はこちらが担当。Claude Rule とは独立した契約）

### 各サブモジュールで必要になるもの

- 02 の対応表の「参照されている」列（サブモジュールの外から何を参照しているか）
- 各サブモジュールの README と主要なスキル・ツールの `meta.requires_skills`

## 触るファイル

- 新規: 各サブモジュールの `.links.yaml`、`.claude/skill-tools.hooks.yaml`（フックを使う場合）
- 新規または変更: 各サブモジュールの `CLAUDE.md`、`AGENTS.md`（`tools/AGENTS.md`・`CLAUDE.md`、`site/skills-site/AGENTS.md` など既存のものは変更）
- 変更: アンブレラの `justfile`（`links-sync` を全サブモジュールに対して実行するレシピ）
- 変更: `maintenance/plugin/skills/exploring-this-repo`（サブモジュール単体で開いているときの地図の見え方）

## 決定事項・注意点／落とし穴

- Junction は Claude Code 用だけに限る（依頼の範囲）。他ツール向けの対応はしない。
- Junction で見せるのは「そのフォルダの作業に必要なもの」だけ。アンブレラ全体を Junction で見せると、単体で開く意味が無くなるうえ、祖先参照の禁止にも反する。
- アンブレラで開いたとき、サブモジュール内の `.claude/skills` Junction はスキルとして二重に見えないか確認する（Claude Code はネストした `.claude/skills` も読むことがある）。二重に見えるなら、04 の設計を見直す。
- サブモジュール単体 clone で Junction が壊れていても、Claude Code の起動自体は失敗しないことを確認する（壊れた Junction を読み込もうとしてエラーにならないか）。
- `CLAUDE.md` の `@` import がプロジェクト外を指すと承認プロンプトが出る場合は、Junction 経由のパスに切り替える。

### 確認項目（サブモジュールごと）

- 単体で開いたとき、必要なスキルが `/` 補完と自動起動の両方で見える
- `CLAUDE.md` の内容が読み込まれる（`/memory` で確認）
- フックが動く（設定した場合）
- `just links-check` がエラーなし。`git status` に Junction が出ない
- アンブレラで開いたとき、スキル・指示が二重にならない

## ルール更新ポイント

- 各サブモジュールの `AGENTS.md`（本ステップで新規）: 単体で開く前提（アンブレラ配下に clone されていること、`just links-sync` の実行）、そのフォルダの責務。
- `maintenance/docs/repo-layout.md`（本ステップ）: サブモジュールごとの Junction 一覧の考え方（宣言は各 `.links.yaml` が正本で、ドキュメントには重複して書かない）。

## 進め方

- **実行主体**: メインがサブモジュールごとに宣言を書き、`claude` を実際にそのフォルダで起動して確認項目を検証する（`claude -p` での非対話確認で足りる項目はそれで行う）。
- **TODO 化**: サブモジュールごとに 1 TODO（宣言 → sync → 確認項目）。
