# Step1 調査: 詳細結果メモ

> [../01-research-platform-constraints.md](../01-research-platform-constraints.md) の実行で得られた詳細。プラン本体の「調査結果」節には要約だけを置き、後続ステップ（04・07・08、00）の本文へは反映済み。原則このファイルを読み直す必要はない。

実施日: 2026-11-10。実験はすべて `temp/`（gitignore）配下のダミーで行い、リポジトリ本体には手を入れていない。

## 環境

git 2.47.1.windows.1 / Python 3.13.9 / node v26.5.0 / rg 15.2.0 / prettier 3.9.6 / pytest 9.2.0 / codegraph 1.6.0 / tinyglobby 0.2.17 / fast-glob 3.3.2 / uv 0.11.32 / pnpm 11.15.0 / lefthook 2.1.9 / Claude Code 2.1.319

## A. Git × Junction（実験: `temp/junction-exp/`、メモ `temp/junction-exp/NOTES.md`）

- A1: Git は Junction を**実ディレクトリとして辿る**。`git add -A` で参照先の中身が 100644 としてステージされる（120000 にはならない。`core.symlinks` の値に関係なし）。Git Bash の `ls -la` は `lrwxrwxrwx` と表示するので見た目に騙されない。
- A2: `.git/info/exclude` の `link` / `/link` / `/link/` はいずれも確実に無視される。
- A3 データ消失:

| 操作                                                                                  | Junction                       | 参照先                                        |
| ------------------------------------------------------------------------------------- | ------------------------------ | --------------------------------------------- |
| exclude あり + `clean -fd`                                                            | 残る                           | 無事                                          |
| exclude あり + `clean -fdX` / `-fdx` / `-ffdx`                                        | Junction のみ消える            | 無事                                          |
| exclude なし + `clean -fd`（中身すべて untracked）                                    | Junction のみ消える            | 無事                                          |
| **exclude なし・中身の一部が ignore + `clean -fd` / `-fdX`**                          | 残る                           | **中のファイルが個別に削除される**            |
| exclude あり + `checkout -- .` / `stash -u`                                           | 影響なし                       | 無事                                          |
| **exclude あり + 同じパスを実ディレクトリとして追跡する別コミットとの `switch` 往復** | 消える                         | **同名ファイルが無警告で上書き → 戻ると削除** |
| exclude あり + `stash -a` → `pop`                                                     | 実ディレクトリのコピーに化ける | 無事                                          |

switch の件は「ignore 対象は上書きしてよい」という Git の扱いによる。exclude なし、または `--no-overwrite-ignore` なら中断する。

- A4: サブモジュール内の `git rev-parse --path-format=absolute --git-path info/exclude` は `<super>/.git/modules/<name>/info/exclude` を返し、ファイルは既に存在する。そこに書けばサブモジュールも親も clean。
- A5: worktree には Junction もサブモジュールの中身も無い。worktree 内のサブモジュールは exclude が別ファイルになる（worktree は使わない方針なので参考情報）。
- 祖先を指す Junction: `git status` はパス長上限（Filename too long）まで潜る。

## B. Claude Code × Junction／サブフォルダ起動

### 実機確認（Claude Code 2.1.319、`claude -p`、`temp/cc-exp/`）

| ケース                                           | 結果                                                                                         |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| `.claude/skills/<name>` が Junction              | 発見され、起動もできた                                                                       |
| `.claude/skills` 全体が Junction                 | 発見された                                                                                   |
| アンブレラ配下のサブモジュールで起動             | 親の `.claude/skills` は**見えない**（repo root ＝サブモジュールで遡りが止まる）             |
| アンブレラ配下の普通のサブフォルダで起動（対照） | 親の `.claude/skills` が見える                                                               |
| サブモジュールで起動                             | 親（アンブレラ）の `CLAUDE.md` は**読み込まれる**                                            |
| アンブレラで起動                                 | サブモジュール内 `.claude/skills` の Junction スキルは起動時の一覧に出ない（二重にならない） |

### ドキュメント調査（code.claude.com/docs/en）

- skills: symlink したスキルフォルダは読まれ、同一ターゲットは 1 回だけロード（skills.md "Symlinked folders"）。Junction は記載なし。Windows の Junction スキルが登録されない旨の issue 報告あり（未検証。上の実機では問題なし）。
- rules: `.claude/rules/` の symlink を明示サポート。ターゲットが作業ディレクトリ外なら外部 import 扱いで初回承認が必要（memory.md）。
- agents / skills: 作業ディレクトリから repo root まで遡って `.claude/agents/`・`.claude/skills` を読む（sub-agents.md, skills.md "monorepos"）。
- CLAUDE.md: 作業ディレクトリと全祖先を起動時に読む。子ディレクトリは該当ファイルを読んだときに遅延ロード。`@` import は外部パス可、最大 4 ホップ、作業ディレクトリ外は初回承認ダイアログ（memory.md）。
- 親の `.claude/settings.json` は読まれない。共有設定は起動ディレクトリから（settings.md、large-codebases.md）。
- `extraKnownMarketplaces` は `directory` 型でローカルパス可だが、`enabledPlugins` だけではインストールされず、各ユーザーの install が要る。`--plugin-dir` は 1 セッション限り。`CLAUDE_CODE_PLUGIN_DIRS` 環境変数でも可（project/local 設定からは設定不可）。
- `--add-dir` は skills と agents を読む。CLAUDE.md・rules は `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` 併用時のみ。`permissions.additionalDirectories` はファイルアクセスのみ。
- `${CLAUDE_PROJECT_DIR}` は「セッションを開始したプロジェクトルート」。サブモジュールで起動すればサブモジュール側を指すと推定。
- 設定優先順位: managed > `--settings` > local > project > user。配列と hook は層をまたいでマージ。

## C. スキャナ × Junction

| ツール                                                      | 兄弟 Junction を辿るか                          | 祖先 Junction                            | 補足                                                                                 |
| ----------------------------------------------------------- | ----------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------ |
| Python `Path.rglob` / `glob("**")` / `glob.glob(recursive)` | 辿る                                            | 63 段の reparse 上限で止まる（重複計上） |                                                                                      |
| Python `os.walk(followlinks=False)`                         | **辿る**                                        | 同上                                     | 引数が効かない                                                                       |
| Python `Path.walk()`（既定）                                | 辿らない                                        | 安全                                     |                                                                                      |
| 判定                                                        | —                                               | —                                        | `is_junction()` / `os.path.isjunction` は True、`is_symlink` / `islink` は **False** |
| rg（既定）                                                  | 辿らない                                        | 安全                                     | `-L` は辿り、ループを検知                                                            |
| prettier / ruff                                             | 辿らない                                        | 安全                                     |                                                                                      |
| pytest                                                      | 辿る                                            | **止まらない**                           |                                                                                      |
| Node `fs.readdirSync({recursive})`                          | 辿る                                            | 上限で止まる                             | Dirent は `isSymbolicLink()` が true                                                 |
| Node `fs.globSync`                                          | 辿らない                                        | 安全                                     |                                                                                      |
| tinyglobby（Astro）                                         | 辿る（既定）                                    | 1 段重複・ループ検知                     |                                                                                      |
| fast-glob                                                   | 辿る（既定）                                    | 上限で止まる                             | `followSymbolicLinks:false` で回避                                                   |
| codegraph                                                   | git 管理内では exclude を尊重                   | ループ検知                               |                                                                                      |
| textgraph / lefthook                                        | git の一覧に従う                                | —                                        | exclude があれば安全                                                                 |
| VS Code 検索                                                | 辿る見込み（`search.followSymlinks` 既定 true） | —                                        | ドキュメントからの推定                                                               |

### このリポジトリの走査箇所

| file:line                                                                                                                                                                                                                                                                 | 方法                                                | Junction                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------- |
| `tools/internal/skill/util/skill_frontmatter.py:47` `find_skill_md_files`（呼び出し元 `set_skill_versions.py:24`、`set_skill_tags.py:25`、`set_skill_descriptions.py:31`、`skill_meta_field_fill.py:194,206`、`check_skill_repo_tools.py:37`、`skill_tool_graph.py:166`） | `os.walk`                                           | **辿る**。set 系は同じ実体へ二重書き込みの恐れ                                    |
| `tools/internal/plugin_meta/generate/generate_skill_catalog.py:47`、`generate_skills_catalog_md.py:21,40`、`generate_copilot_marketplace.py:35`                                                                                                                           | `iterdir` 1 段 + `is_dir()`                         | 1 段だけ拾う                                                                      |
| `site/skills-site/scripts/publication-core.mjs:101,113`                                                                                                                                                                                                                   | `readdir` + `isSymbolicLink()`                      | 辿らない                                                                          |
| `site/skills-site/scripts/patch-csp-header.mjs:13`                                                                                                                                                                                                                        | `readdirSync` + `statSync`                          | 辿る（対象は dist）                                                               |
| `tools/skill-tools/skill_tools/source/__init__.py:131-162`                                                                                                                                                                                                                | `git ls-files --cached --others --exclude-standard` | exclude があれば安全。`_resolve` の `is_relative_to(root)` は兄弟 Junction を通す |
| 同 `:174`、`:220`                                                                                                                                                                                                                                                         | `os.walk(followlinks=False)` + `is_symlink()`       | **辿る**                                                                          |
| `tools/skill-tools/skill_tools/install/installer.py:44,51,85-90,359,403`、`manifest.py:256,279,295-299`                                                                                                                                                                   | `is_symlink()` 防御 + `os.walk`                     | **すり抜ける**（コピー・削除で中に入る恐れ）                                      |
| `agent-tooling/.../adapters/claude/common/skill_frontmatter.py:49`、`recommend_skills.py:135`（生成物 `hooks/generated/claude/{recommend_skills,skill_usage_tracker}.py`）                                                                                                | `rglob("SKILL.md")`                                 | **辿る**                                                                          |
| `agent-tooling/.../sources/claude_rules.py:50`、`checks/agent_context.py:212`、`hooks/scenarios/scoped_rules/discovery.py:39`（生成物 `*/scoped_rules.py:600`）                                                                                                           | `rglob("*.md")`                                     | **辿る**                                                                          |
| `agent-tooling/.../core/sessions.py:131`（`agent_sessions.py`）                                                                                                                                                                                                           | `os.path.islink`                                    | Junction を検知できない                                                           |

## D. サブモジュール × 配布・CI

- Claude Code の plugin `source`: 相対パス（`./` 必須、`..` 不可）、`github`（repo/ref/sha）、`url`（git URL、ref/sha）、`git-subdir`（url/path/ref/sha、sparse checkout）、`npm`、`archive`、`command`。marketplace の clone は v2.1.295 以降「プラグインファイルを含むサブモジュールだけ」取得（marketplace-reference "Git submodules in the marketplace repository"）。update 時のサブモジュール同期漏れ（#33164）、EDR が `--recurse-submodules` を止める（#27251）報告あり。`owner/repo` 形式は SSH を試みるので https URL で書く（host-marketplace）。
- Codex: `local`／`url`／`git-subdir`（https://developers.openai.com/codex/plugins/build）。解決できないエントリはそれだけ飛ばす。
- Copilot CLI: 相対パス／`github`（repo/ref/sha/path）／`url`。`.claude-plugin/marketplace.json` も読む（https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference）。
- Cursor: `.cursor-plugin/marketplace.json` の `source` はパスのみ。他リポジトリ参照は不可（https://cursor.com/docs/reference/plugins）。現状ルートに Cursor 用 marketplace は無い。
- マニフェスト同居: 各ツールは別ファイルを見るので並べられる。ただしルートの `plugin.json` は Cursor が Agent Plugins 標準として読み、標準は `skills/` 直下を前提とする。現 `copilot-plugins/meta/plugin.json` はスキル名配列でスキルを plugin 直下に置いており、同居させるなら `skills/` 配下へ揃える必要がある（06 の範囲）。
- skill-tools `GitHubSource`（`tools/skill-tools/skill_tools/source/__init__.py`）: REST API の `commits/{ref}` → `git/trees/{sha}?recursive=1` → `git/blobs/{sha}`。Trees API はサブモジュールを `type: commit` で返し、`_load_tree` は blob 以外を黙って捨てるので、**サブモジュール配下が丸ごと見えなくなり、エラーにもならない**。
- GitHub Actions: `skill-site.yml`（paths `claude-plugins/**/skills/**` 等、Azure SWA デプロイ）、`tools-site.yml`（Pages）、`tool-release.yml`（paths なし、タグ `<name>-v<version>` を `gh release create --target ${{ github.sha }}`）、triage 系・`pr-agent.yml`・`agentics-maintenance.yml`。public なのでトークン不要。`paths:` はアンブレラ側ではサブモジュールのパス（gitlink）しか変わらないため、中身のパターンは発火しない見込み（未実験）。公開インストール手順 `git+https://github.com/fdshg693/ai#subdirectory=tools/skill-tools` はサブモジュール化後に動くか未確認。

## E. ワークスペース・フック（実験: `temp/ws-exp/`）

- uv: members がサブモジュール内でもルートの `uv lock`／`uv sync` は通る。サブモジュール内からの `uv run` はアンブレラの `.venv` を使う。サブモジュール直下に `pyproject.toml` を置くと（workspace 定義の有無にかかわらず）別の `.venv`／`uv.lock` が無警告で作られ二重管理になる。未初期化サブモジュールではメンバーが黙って無視され、lock から落ちる恐れ。単体 clone ではパッケージ単位で独立して動く。`uv tool install --editable <sub>/<pkg>` は動く。
- pnpm: ルートの install は通り、サブモジュール内からもアンブレラの workspace を見つける。サブモジュール内に `pnpm-workspace.yaml` を置くとそちらが優先され二重管理。サブモジュール側にも `node_modules/` の `.gitignore` が要る。
- lefthook: アンブレラのフックはサブモジュールのコミットで発火しない。サブモジュール内の `lefthook install` は `.git/modules/<name>/hooks` に正しく入る。`extends: [../x.yml]` は統合され、参照先が無いと黙って無視される。現 `lefthook.yml` はルート相対パス（`tools/**`、`just --justfile tools/internal/justfile`）に強く依存。
- 出典: https://docs.astral.sh/uv/concepts/projects/workspaces/ 、https://pnpm.io/workspaces 、https://lefthook.dev/configuration/extends
