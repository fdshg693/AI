---
type: Plan Step
status: ready
---

# Step 4: playwright-app を `workflow/playwright-app/` へ

> [00-overview.md](00-overview.md) の続き。[02](02-browser-tools.md) の完了（テストサイトの置き場所と起動レシピ）を待って着手する。[03](03-browser-skills.md) とは独立。

## やること

クローン側の `playwright-app/`（自然言語ストーリー → AI がブラウザを操作 → `.spec.ts` を生成する実験アプリ）を workflow サブモジュールへ移す。Python は uv ワークスペース、Node は pnpm ワークスペースに載せ替え、`Makefile` を just に移し、散らばっている規約（クローン側 `.claude/rules/playwright-app/*.md`・`playwright-app/.claude/`）を `AGENTS.md` と `docs/` にまとめる。

## 読むべきファイル

**置き場所と載せ方（最優先）**

- `workflow/README.md`・`workflow/AGENTS.md` — workflow に置くものの約束（registry に載せない、付属スキルなし）
- `maintenance/docs/uv-workspace.md` — メンバーの追加条件（`package = false` の扱い）
- `maintenance/docs/justfile-conventions.md` — 各ディレクトリの justfile とルートからの呼び出し
- `workflow/claude-wrapper/` — 既存の workflow メンバーの形（pyproject・AGENTS.md）
- `tools/llm/my-agents/justfile`・`site/skills-site/justfile` — ディレクトリごとの justfile の前例（workflow 配下には justfile が無い）

**移す元（クローン側）**

- `playwright-app/README.md`・`QUICKSTART.md`・`FEATURES.md`・`NEXT.md`・`MERMAID.md` — 利用者向け文書
- `playwright-app/Makefile`・`pyproject.toml`・`package.json`・`playwright.config.ts`・`.env.example`
- `playwright-app/scripts/`（`server/`・`vertical_slice/`・`stories/`・`internal/`）
- `.claude/rules/playwright-app/architecture.md`・`session-server.md`・`vertical-slice-runner.md`・`cost-summary.md`・`plans.md`
- `playwright-app/.claude/plan/`・`playwright-app/big_plans/`

## 触るファイル

- 新規 `workflow/playwright-app/` — `scripts/`・`tests/`（`generated/` は gitignore するか 01 で判断）・`playwright.config.ts`・`pyproject.toml`・`package.json`・`.env.example`・利用者向け文書
- 新規 `workflow/playwright-app/AGENTS.md`・`CLAUDE.md` — architecture・session-server・vertical-slice-runner・cost-summary の規約を集約
- 新規 `workflow/playwright-app/docs/` — `big_plans/`（設計ロードマップ。全 Step 実装済み）と、`.claude/plan/` から残すと決めた設計資料
- 新規 `workflow/playwright-app/justfile` — `Makefile` の `setup`・`env`・`install-browsers`・`server`・`slice`・`resume`・`test`・`cost`・`cost-html`・`clean`。`npx` は `pnpm exec` に替える
- 変更 `workflow/README.md` — 「中身」に playwright-app を追加
- 変更 `pyproject.toml`（アンブレラ）— `[tool.uv.workspace] members` に `workflow/playwright-app`、`uv.lock` 再生成
- 変更 `pnpm-workspace.yaml` — `workflow/playwright-app`、`pnpm-lock.yaml` 再生成
- 変更 `workflow/.gitignore` か `workflow/playwright-app/.gitignore` — `.env`・`.playwright/`・`test-results/`・`playwright-report/`・`node_modules/`・`__pycache__/`
- 変更 `registry/local-configs.yaml` — `workflow/playwright-app/.env` を宣言

## 決定事項

- **`uv.lock`・`package-lock.json` は持ち込まない**。ルート定義・lockfile はアンブレラだけに置く（[repo-layout「生成物の所有権」](../../maintenance/docs/repo-layout.md#生成物の所有権)）。
- **`Makefile` は just に置き換える**。`make serve-pages`（`bash ../resources/serve.sh`）は 02 で足したアンブレラのテストサイト起動レシピを呼ぶ形にし、サブモジュールから兄弟サブモジュールへの相対パス（`../../tools/browser/test-sites`）は書かない。サブモジュール単体で開いたときは動かないので、AGENTS.md に「テストサイトはアンブレラの `just test-sites`」と書く。
- **ワークスペースのメンバー名**は `vertical-slice` から `playwright-app` に改名する。`python -m scripts...` はトップレベルの `scripts` を cwd から解決するので、just レシピは必ず `workflow/playwright-app` を cwd にして呼ぶ。
- **課金に関わる操作の確認**（`slice`・`resume` は実 AI API を呼ぶので実行前にユーザーへ確認）は AGENTS.md に残す。
- **存在しないスキルへの参照**（`use-tavily`・`playwright-cli`・`vertical-slice-ai-test`）は、それぞれ `web-lookup`・`using-playwright-cli`（03）に置き換えるか削る。`vertical-slice-ai-test` は本文の手順を AGENTS.md に直接書く。
- **`.claude/plan/` の扱い**: 完了済みの実装詳細プランは持ち込まない。設計判断として残す価値があるもの（SPEC 相当）だけを `docs/` に移す。どれを残すかは 01 の結果で決める。クローン側 `rules/playwright-app/plans.md` が定める旧プラン運用は捨てる（このリポジトリの `plans/` 運用に従う）。
- 注意: `scripts/vertical_slice/cli_executor.py` は `playwright-cli` を子プロセスで呼ぶ。パス前提（cwd・`.playwright-cli/`）が移設先で変わらないか確認する。
- 注意: `requires-python = ">=3.11"` とルートの ruff `target-version = "py313"` の差。ワークスペースの Python と合うか確認する。
- 注意: ストーリー YAML の URL（`http://localhost:8080/...`）は 02 の配信位置と一致させたまま変えない。

## ルール更新ポイント

- `workflow/playwright-app/AGENTS.md` を新設し、クローン側のルール 4 本（`architecture`・`session-server`・`vertical-slice-runner`・`cost-summary`）を集約する。サブシステムごとの詳細が長い場合は `docs/` に分け、AGENTS.md からリンクする。
- `workflow/README.md` に 1 行足す。

## 進め方

- 実行主体: メインのエージェント。
- TODO 化: (1) コード・文書の移設、(2) ワークスペース・just への載せ替え、(3) 規約の集約、(4) 動作確認。workflow サブモジュールで 1〜2 コミット → アンブレラでポインタ・pyproject・pnpm-workspace・lockfile・local-configs を 1 コミット。
- 確認: `uv sync`・`pnpm install` が通る、`just --justfile workflow/playwright-app/justfile server` が起動する。生成済みテストは gitignore で存在しないので、`test` の確認はユーザーの了承を得て `slice` を 1 本通し（課金あり）、その生成物に `pnpm exec playwright test` をかける。了承が無ければ `test` は `--list` で設定が読めることの確認に留める。
