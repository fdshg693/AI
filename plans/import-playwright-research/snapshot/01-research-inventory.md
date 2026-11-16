---
type: Plan Step
status: ready
---

# Step 1: 持ち込む資産の棚卸しと置き場所の確定

> [00-overview.md](00-overview.md) の続き。コードは書かない。確定した事実は 02〜05 のプラン本文へ直接反映する。

## やること

クローン側（`C:\C\playwright`。`temp/playwright` は Junction）の取り込み対象について、参照グラフ・依存・既存との重複を洗い出し、[00-overview.md](00-overview.md) の「主要な決定事項」で保留にしている名前・置き場所を確定させる。

## 調査観点

- **参照グラフ**: 取り込み対象のファイルが指すリンク・パスの一覧。`.claude/outputs/INSTALL.md` の「移動先で切れる参照」表が出発点（`../../docs/*-notes.md`・`../../plans/...`・`.claude/rules/ROLE.md`・`.claude/tools/*/dist/cli.js`）。これに加えて `rg -n "\.claude/|resources/|\.\./" ` を `.claude/skills`・`.claude/tools/*/src`・`.claude/tools/*/README.md`・`resources/`・`playwright-app/`（`node_modules` 除く）にかけ、ソースコード中のハードコードされたパス（`pwq`/`pwdo` の既定キャッシュ先 `.playwright-cli/`、`playwright-app` の `../resources/serve.sh` など）も拾う。
- **スキル間の依存**: 4 スキル（`using-playwright-cli`・`sharing-browser-with-user`・`searching-playwright-docs`・`authoring-playwright-agents`）の SKILL.md・references が互いに・`pwq`/`pwdo` に・`web-lookup`（`site-recon.md` → `../../web-lookup/tav.md`）にどう依存するか。`pwq`/`pwdo` を「必須」として書いている箇所と「任意」の箇所を分ける（my-tools へ切り出す範囲を決めるため）。
- **プラグイン名**: 新プラグインの名前（候補 `browser`・`browser-automation`・`playwright`）。既存プラグイン名（`skills/plugins/*`）・`registry/ai-tools.yaml` の命名と衝突しないか。my-tools 側スキルの名前（候補 `browser-context-tools`）。
- **調査ノートの置き場所**: `.claude/docs/*-notes.md`（合計約 150 KB）を、スキル ZIP・スキル公開サイトに入れずに置ける場所。プラグイン直下の `docs/` がサイトの収集・`skill-catalog.json`・`agent-compat-sync` のコピー対象にならないか（`site/skills-site` の収集範囲、`maintenance/scripts/plugin_meta/` の走査範囲を確認）。ならない場所が無ければ、各ツール・各スキルの README から参照する `docs/topics/browser-automation/`（OKF frontmatter 付き）を候補にする。
- **ツールの規約差**: [tool-conventions](../../maintenance/docs/tool-conventions.md) が first-class CLI に求める `--version`・`version` メタデータ・README の書式と、`pwq`/`pwdo` の現状との差。`engines.node >= 26` と `mise.toml` の node 26.5.0 が合うこと。既存の TS ツール（`tools/llm/aim2`・`tools/linear-cli`）の `package.json`・`tsup.config.ts`・pnpm ワークスペース参加の仕方。
- **models.json の扱い**: `pwq`/`pwdo` の `models.json`（OpenRouter のモデル一覧）と `aim2` の `models.json` の書式が同じか（`glm-flash` の説明に「aim2 の既定と同じ」とある）。共通化はしないが、`registry/local-configs.yaml` への宣言の形を揃える。`.env.example`（`pwq`/`pwdo` とも未追跡）の中身。
- **searching-playwright-docs の取得方法**: ローカル `docs/src` を読む `sync_playwright_docs.py` を、GitHub から `docs/src/**/*.md` だけ取る形に替える方法（`gh api` の tarball か contents API）。`authoring-playwright-agents/download_playwright_agents.py` の取得方式を流用できるか。スナップショットの総量（約 3 MB / 180 ファイル）をコミットしてよいか、既存スキル（`codegraph-docs` 等）の `output/` の大きさと比べる。
- **playwright-app の依存**: Python（`openai`・`fastapi`・`uvicorn`・`pyyaml`・`python-dotenv`、`package = false`）を uv ワークスペースのメンバーにできるか（[uv-workspace](../../maintenance/docs/uv-workspace.md)）。`@playwright/test` を pnpm ワークスペースへ載せられるか。`Makefile` の各ターゲットを just に移す範囲（[justfile-conventions](../../maintenance/docs/justfile-conventions.md)）。`playwright-app/.claude/plan/`・`big_plans/`・`.claude/rules/playwright-app/*.md` のうち、規約として残すもの・設計資料として残すもの・捨てるもの。ルールが参照しているが存在しないスキル（`vertical-slice-ai-test`・`use-tavily`・`playwright-cli`）の扱い。
- **重複スキルの新旧**: `ai-sdk-docs`・`codegraph-docs`・`web-lookup`・`writing-skill` をクローン側と既存側で `diff -r`（`output/`・`.venv/`・`__pycache__/` を除く）し、クローン側にしか無い改善があるか。既知: `web-lookup` は既存側に `aws.md` があり既存側が新しい、`ai-sdk-docs/output/temp/` はクローン側のゴミ。

## 調査結果

（実行時に要約を書く。詳細は `progress/01-research-results.md`）

## 進め方

- 実行主体: 参照グラフと重複 diff は Explore サブエージェントに委任してよい（結果は一覧だけ返させる）。置き場所・名前の採否はメインが決め、02〜05 の本文へ反映する。
- TODO 化: 調査観点 1 項目 = 1 TODO。コミットはしない（プラン本文の更新のみ）。
