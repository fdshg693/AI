---
type: Plan Step
status: implementing-done
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
- アンブレラのプラグイン（`maintenance/plugin`）のスキルは、`.claude/skills/<name>` の Junction で読み込む（01-B で動作確認済み）。`--plugin-dir` は補助手段として README に書く。
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

- **Claude Code の読み込み範囲（01-B、実機 2.1.319 で確認）**:
  - `.claude/skills/<name>` の Junction も、`.claude/skills` 全体の Junction もスキルとして発見・起動できる。よってアンブレラのスキルは `.claude/skills/<name>` の Junction で見せる方式を採る。`--plugin-dir`／`CLAUDE_CODE_PLUGIN_DIRS` は毎回の起動引数や環境変数が要り、`extraKnownMarketplaces`＋`enabledPlugins` は各ユーザーの install が要るので、補助手段として README に書くだけにする。
  - サブモジュールで起動すると、親アンブレラの `.claude/skills`・`.claude/agents` は見えない（repo root ＝サブモジュールで遡りが止まる）。必要なものは必ず Junction で見せる。
  - サブモジュールで起動しても、親アンブレラの `CLAUDE.md`（とその `@./AGENTS.md`）は自動で読まれる。**サブモジュールの `CLAUDE.md` から `@../...` で親を import しない**（二重読み込みになる。外部 import の承認プロンプトも出る）。サブモジュールの `AGENTS.md` には、アンブレラ全体の規約と重複しない、そのフォルダ固有のことだけを書く。単体 clone では親の指示が無くなるが、許容範囲（依頼どおり）。
  - アンブレラで起動したとき、サブモジュール内 `.claude/skills` の Junction スキルは起動時には読まれず、二重にならない（ただしサブモジュール内のファイルを読むと遅延ロードされうる。確認項目で見る）。
  - 親の `.claude/settings.json` は読まれない。サブモジュールごとに `just hooks-install` で生成する方式（本節の上の方針）で正しい。`${CLAUDE_PROJECT_DIR}` は起動ディレクトリ（サブモジュール）を指す想定なので、確認項目でフックから出力して確かめる。
  - `.claude/rules/` の Junction・symlink も読まれる（symlink は公式に記載あり）。ただし参照先が作業ディレクトリ外だと外部 import 扱いで初回承認が要る。
- **ワークスペース（01-E）**: サブモジュールで開いても `uv run`／pnpm はアンブレラの workspace と `.venv` を自動で使う。サブモジュール直下に `pyproject.toml`・`pnpm-workspace.yaml` を置かない（07 の決定）。単体 clone ではパッケージ単位の `uv run` で動く前提を AGENTS.md に書く。
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
- **コミット**: サブモジュールごとに、確認項目が通った時点で (a) サブモジュール側に宣言（`.links.yaml`・`CLAUDE.md`／`AGENTS.md`・フック設定）の 1 コミット、続けて (b) アンブレラ側でポインタ更新の 1 コミット（2 段階コミット）。Junction と `.claude/settings.json` はコミットしない。ステップ完了時にプラン更新を 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（01 完了時）: 01-B の実機確認から、アンブレラのスキルは `.claude/skills/<name>` の Junction で見せる方式に確定した。サブモジュールの `CLAUDE.md` から親を `@` import しない（親の `CLAUDE.md` は自動で読まれる）ことを「決定事項」に加え、status を `planning-breakdown` に進めた。
- 2026-11-10（04 完了時）: `links` はアンブレラから再帰でチェックアウト済みサブモジュールの `.links.yaml` を読むので、「`links-sync` を全サブモジュールに対して実行するレシピ」は不要（`just links-sync` 1 回でよい）。`.links.yaml` はリポジトリのルート直下だけ。agent-tooling の走査は、起点そのもの（`.claude/rules`・`.claude/skills` 全体）が Junction なら読み、起点の中にある Junction は辿らない。`.claude/skills/<name>` の Junction でスキルを見せる場合、Claude Code 自体は読むが、agent-tooling の `recommend_skills` は `.claude/skills` を起点に走査するので `<name>` の Junction の中は見ない点に注意（必要なら 08 で起点の扱いを決める）。
- 2026-11-10（06 完了時）: `agent-compat/` には `AGENTS.md`・`CLAUDE.md`（`@./AGENTS.md`）・README を作成済み。08 では単体で開いたときの前提（アンブレラ必須、Junction）を追記する。他ツールの知識スキルを Cline・Kilo・Antigravity に見せるコピーは、`just agent-compat-sync` で作る（アンブレラのルートで実行）。
- 2026-11-10（07 完了時）: [progress/07-submodule-results.md](progress/07-submodule-results.md)。08 に効く事実:
  - 各サブモジュールのルートには `.gitignore`・`.gitattributes`・`LICENSE`・`lefthook.yml`（`extends: [../maintenance/lefthook/submodule.yml]` だけ）がある。`skills/`・`site/` の README は切り出し時に作った最小のもの。`tools/`・`agent-compat/` は既存の README・AGENTS.md・CLAUDE.md。
  - サブモジュール単体で開いたときにコミット手順を使うには、`maintenance/plugin/skills/committing` を `.claude/skills/committing` の Junction で見せる（ラッパーは `../maintenance/...` を前提にしている）。
  - サブモジュールは detached HEAD で checkout される。開いたら `git switch main`（`just sub-sync`）。
- 2026-11-10（08 完了時）: [progress/08-subfolder-results.md](progress/08-subfolder-results.md)。計画からの変更:
  - 「`links-sync` を全サブモジュールに対して実行するレシピ」は作らず、フック用に `just sub-agent-hooks-install`／`sub-agent-hooks-update` をアンブレラの justfile に足した（`git submodule foreach` で各サブモジュールを project にして skill-tools を実行）。
  - アンブレラで開いてサブモジュール内のファイルを読むと、サブモジュールの `.claude/skills` の Junction が `skills:committing` のようなディレクトリ別スキルとして遅延ロードされる（起動時には出ない）。中身は同じスキルで実害は小さいため、04 の設計は変えず repo-layout に書いた。
