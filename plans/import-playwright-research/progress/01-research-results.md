# Step 1 調査結果（詳細）

調査日: 2026-11-15。クローン側は `C:\C\playwright`。後続作業の正本は 02〜05 のプラン本文で、ここは根拠の記録。

## 1. 参照グラフ

`.claude/outputs/INSTALL.md` の「移動先で切れる参照」表に加え、`rg` でソース・README・ルールを走査した。分類:

| 種類                  | 例                                                                                                                                                              | 扱い                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 調査ノート            | `../../docs/*-notes.md`、`.claude/docs/*-notes.md`（スキル README・references、pwdo README、rules）                                                             | `docs/topics/browser-automation/` へ移し、README からだけ参照（下記 4）         |
| 完了プラン            | `../../plans/browser-task-delegation/*`・`delegation-guardrails/*`・`delegation-integration/*`・`browser-automation-scripting/*`（pwdo README・sharing README） | 要約 1 行に置換                                                                 |
| ROLE.md / OVERVIEW.md | `using-playwright-cli`・`authoring-playwright-agents`・`searching-playwright-docs` の SKILL.md・README、`rules/tools/pwq.md`                                    | 削除（ルーティングは SKILL.md 本文へ）                                          |
| ツール起動パス        | `.claude/tools/pwq/dist/cli.js`・`.claude/tools/pwdo/dist/cli.js`（references・README）                                                                         | コマンド名 `pwq`/`pwdo`                                                         |
| ルール間              | `.claude/rules/tools/pwq.md`・`pwdo.md`（references・README）                                                                                                   | `tools/browser/{pwq,pwdo}/AGENTS.md`                                            |
| 別プラグイン          | `site-recon.md` → `../../web-lookup/tav.md`、web-lookup `tav.md` → `../using-playwright-cli/references/site-recon.md`（クローン側のみ）                         | スキル名で参照                                                                  |
| upstream 生成物       | `../../using-playwright-cli/output/playwright-cli/references/test-generation.md`（scripted-automation.md）                                                      | 取り直し後も同じパスにあるので相対リンクのまま可                                |
| テストサイト          | `resources/`・`resources/serve.py`（README・references・ROLE.md・custom-pages.md）                                                                              | `tools/browser/test-sites/`。スキル本文からは「このリポジトリ内なら」の任意扱い |
| 正しい言及            | `using-playwright-cli/README.md` の「`playwright-cli install --skills` が `.claude/skills/` に配る」、`authoring-playwright-agents` の `.claude/agents/*.md`    | 残す（05 の検査で許可リスト化）                                                 |

### ソースコード中のハードコード

- `pwdo/src/passthrough.ts`: pwq の解決順 `PWDO_PWQ` → PATH の `pwq` → `PACKAGE_ROOT/../pwq/dist/cli.js`（隣のディレクトリ）。`tools/browser/pwq` と `tools/browser/pwdo` が兄弟なので隣解決はそのまま効く。ヒント文言 `cd .claude/tools/pwq && pnpm install && pnpm build` とコメントは書き換え。
- `pwdo/src/cli.ts:157` `契約の正は .claude/tools/pwdo/README.md`、`pwdo/src/report.ts:175` `.claude/skills/sharing-browser-with-user/SKILL.md`、`pwdo/src/guards.ts:4`（コメントの相対リンク）— 文言を書き換え（スキルはスキル名で）。
- `pwq/src/store.ts:32`・`pwdo/src/cli.ts:35`: ストア既定 `.playwright-cli/{pwq,pwdo}`（`process.cwd()` 相対）。
- `pwq/src/config.ts`・`pwdo/src/config.ts`: `.env` を「ツール直下 → 祖先ディレクトリ」と多段探索。models.json は `PACKAGE_ROOT/models.json`、無ければ `.example` にフォールバック。
- `.env.example`（両ツール）に別リポジトリのパス `C:\C\job_hunt\.env`・`.agents/tools/...` が書かれている → 全面書き直し。
- `playwright-app`: `package.json` の `serve:pages` が `bash ../resources/serve.sh`。`scripts/vertical_slice/cli_executor.py:44` のコメントが存在しない `.claude/skills/playwright-cli/SKILL.md`。ストーリー 14 本の `seed_url` はすべて `http://localhost:8080/...`。`load_dotenv()` は引数なし（CWD 探索）。
- `resources/serve.sh` は `NGINX_BIN=/usr/sbin/nginx`（Linux 前提）。`serve.py` は `Path(__file__)` 基準・ポート 8080 で、移設してもパスは壊れない。

## 2. スキル間の依存と pwq/pwdo の必須・任意

- `using-playwright-cli/references/context-saving-explore.md`（pwq 31 箇所）・`delegating-browser-tasks.md`（pwq/pwdo 33 箇所）は全面的に pwq/pwdo 必須 → my-tools へ。
- `site-recon.md` は pwq を 6 箇所で「次の一手」として名指しするが、偵察自体は `curl` だけで完結 → 汎用側に残し、pwq は「入っていれば」に書き換え。
- `sharing-browser-with-user/references/scripted-automation.md` §5「委譲（pwdo）が認証壁に当たったとき」は pwdo 前提 → 節ごと my-tools スキルへ移し、元には 1 行の任意リンクだけ残す。
- `sharing-browser-with-user` は `using-playwright-cli` に依存（コマンド仕様の正）。逆方向は参照のみ。
- `searching-playwright-docs`・`authoring-playwright-agents` は他スキルに依存しない。

## 3. 名前

- 新プラグイン: `browser`（ユーザー確認済み。`skills/plugins/` と `registry/ai-tools.yaml` に衝突なし）。
- my-tools スキル: `browser-context-tools`（`tools/_plugin/my-tools/skills/` に衝突なし）。

## 4. 調査ノートの置き場所

- スキル公開サイトはスキルディレクトリ配下だけを走査（`site/skills-site/scripts/publication-core.mjs` の `walkFiles(skillDirectory)`）。プラグイン直下 `docs/` は ZIP・サイトには入らないが、Claude Code のプラグイン導入ではプラグインごとコピーされる。
- 前例: `docs/topics/claude_sandbox/`（workflow/sandbox の調査結果・既知の不具合を OKF で置いている）。
- → `docs/topics/browser-automation/` に 5 本（`browser-handoff`・`delegation`・`script-cli-roundtrip`・`scripted-automation`・`site-recon`）＋ `index.md`。OKF frontmatter（`type`・`title`・`description`・`tags`・`status`）を付ける。サブモジュールからはアンブレラルート相対のパス表記（相対リンクにしない）で参照する（repo-layout「パスはアンブレラのルート相対」）。

## 5. ツールの規約差（tool-conventions）

| 項目                    | 現状                                                                                                                   | 対応（ユーザー確認済み）                                                                               |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `.env`                  | 祖先ディレクトリまで多段探索（規則 3 違反）                                                                            | aim2 と同じ固定パス `.env`（ツール直下）だけを見る。プロセス環境変数優先・欠落時は探した絶対パスを出す |
| ストア既定              | `<cwd>/.playwright-cli/{pwq,pwdo}`                                                                                     | git ルート基準（規則 4。`.git` を親へ探す。git 外は cwd）。`--pwq-store` 等の明示値は従来どおり        |
| `--version`             | pwdo は `--version` で `VERSION` だけ出す。pwq は `--version` を playwright-cli に素通し、`--pwq-version` で `VERSION` | 両方 `--version` で `<command> <version>` 1 行。pwq の `--pwq-version` は残す                          |
| version                 | 両方 `0.1.0`（package.json）                                                                                           | そのまま                                                                                               |
| engines                 | `node >=26`、`@types/node ^26.5.1`                                                                                     | mise の node 26.5.0 と一致                                                                             |
| ツール内 lock/workspace | `pnpm-lock.yaml`・`pnpm-workspace.yaml`（`allowBuilds: esbuild: false`）                                               | 持ち込まない。ルートの `allowBuilds` は `esbuild: true`                                                |
| tsup                    | `node26`・esm・banner・`skipNodeModulesBundle`                                                                         | aim2 と同形。そのまま                                                                                  |

## 6. models.json・.env

- pwq と pwdo の `models.json.example` は同一。書式は aim2 と同じ（`default` + `models.{alias}.{enable,provider,id,description}`）。中身（モデル一覧）は違う。
- `registry/local-configs.yaml` には aim2 と同じ形で 2 本宣言。`.env` は deny_patterns に掛かり、未追跡ならエラーにならない（宣言は不要）。`.env.example` は追跡してよい。
- `sharing-browser-with-user/.env.example` はパス設定（`BROWSER_PROFILES_ROOT`・`BROWSER_PROFILES_META`）のみ。秘密情報なし。

## 7. searching-playwright-docs の取得

- 現行 `sync_playwright_docs.py` は `find_repo_root` で親を遡って `docs/src` を探し、ローカルコピー。
- `download_playwright_agents.py` は `gh api repos/.../contents/<path>?ref=main` を 1 ファイルずつ（Accept raw）。180 ファイルでは呼び出しが多すぎる。
- → `git clone --depth 1 --filter=blob:none --sparse` + `git sparse-checkout set docs/src` を一時ディレクトリに行い、MD だけコピーする形を採る（呼び出し 1 回、外部依存は `git` のみ）。鮮度 7 日のスキップは維持。
- 総量: `output/docs` 3.0 MB、`index.md` 20 KB、`_meta.json` 40 KB。既存 topics スキルでは数 MB 級のスナップショットは本体を gitignore し索引だけ追跡（例: litellm 2.8 MB → 追跡 2 ファイル、ai-sdk 6 MB → 2 ファイル）。→ `output/docs/` は gitignore、`index.md`・`_meta.json` だけ追跡。`using-playwright-cli`（96 KB）・`authoring-playwright-agents`（119 KB）は codegraph-docs（152 KB 全追跡）と同様に全追跡。

## 8. playwright-app

- Python: `[project] name = "vertical-slice"`、`requires-python >=3.11`、依存 `openai`・`python-dotenv`・`pyyaml`・`fastapi`・`uvicorn`、`[tool.uv] package = false`。
- 実測: 仮想ワークスペースに `package = false` のメンバーを入れると `uv lock` で `source = { virtual = "app" }` として解決され、`uv run` で依存が使えた（uv 0.11.32）。既存メンバーに `package = false` の前例は無いが問題なし。
- Node: `@playwright/test ^1.61.1` のみ。`playwright.config.ts` は `testDir: './tests'`。
- `tests/generated/*.spec.ts` 等はクローン側でも gitignore（追跡 0 件）。`.playwright/` は空ディレクトリ。
- `.claude/plan/main/`（HOW）と `big_plans/`（WHAT）は 9 本ずつ 1 対 1 で中身は別。全 Step 実装済み。`.claude/plan/` 配下は他に `custom_pages/`・`observability/`・`scenarios/`（いずれも完了）と `references/`（旧テンプレート）。
- 存在しない参照: `SPEC.md`（architecture.md が「全体設計の正」とするがクローン内のどこにも無い）、スキル `vertical-slice-ai-test`・`playwright-cli`・`writing-rules`、`.claude/rules/roles.md`。`playwright-app/.claude/rules/using-playwright-cli/` は空ディレクトリ。
- ルール 5 本の大きさ: architecture 3.4 KB、cost-summary 3.1 KB、plans 1.6 KB、session-server 14 KB、vertical-slice-runner 21 KB。
- `.gitignore` の末尾が改行なしで `.env.example` の中身と連結されている（`tests/generated/OPENAI_API_KEY=`）— 移設時に直す。

## 9. 重複スキルの差分

`diff -r -x output -x .venv -x __pycache__` で比較。

| スキル             | 結果                                                                                                                                                                                                                                                                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai-sdk-docs`      | 既存が新しい（`requires_repo_tools: aim`・version 1.0.1、README のリンク先 `cc-knowledge`、ruff 整形）。取り込みなし                                                                                                                                                                                                                                    |
| `codegraph-docs`   | 既存が新しい（`gh` を `dependencies` へ、version 1.0.4、`--filter` の説明が正確）。取り込みなし                                                                                                                                                                                                                                                         |
| `writing-skill`    | 既存が新しい（version 2.0.1、`name` とコマンド名の説明が現行仕様）。取り込みなし                                                                                                                                                                                                                                                                        |
| `web-lookup`       | 全体は既存が新しい（`aws` 系統、version 1.3.0）。ただし `tav.md` にクローン側だけの記述が 2 点: (a) `map`/`crawl`/`research` を CLI に出していない理由（実測: `map` は 15 クレジットで新規 1 枚・死 URL 5 件。sitemap の部分集合）と site-recon.md への誘導、(b)「`localhost`・社内・非公開・認証壁の向こうの URL は外部サービスに渡さない」 → 取り込む |
| `web-lookup/temp/` | クローン側の実行ゴミ。無視                                                                                                                                                                                                                                                                                                                              |
