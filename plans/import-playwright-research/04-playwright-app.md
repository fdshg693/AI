---
type: Plan Step
status: implementing-done
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

- 新規 `workflow/playwright-app/` — `scripts/`・`tests/generated/`（中身は gitignore。クローン側でも追跡 0 件）・`playwright.config.ts`・`pyproject.toml`・`package.json`・`.env.example`・利用者向け文書
- 新規 `workflow/playwright-app/AGENTS.md`・`CLAUDE.md` — architecture・session-server・vertical-slice-runner・cost-summary の規約を集約
- 新規 `workflow/playwright-app/docs/roadmap/` — `big_plans/` 9 本（WHAT・順序。全 Step 実装済み）。`.claude/plan/` は持ち込まない
- 新規 `workflow/playwright-app/docs/session-server.md`・`docs/vertical-slice-runner.md` — 長いルール 2 本（14 KB・21 KB）。AGENTS.md からリンクする
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
- **`.claude/plan/` の扱い**: 完了済みの実装詳細プランは持ち込まない。`.claude/plan/main/`（HOW）・`custom_pages/`・`observability/`・`scenarios/` はすべて完了済み、`references/` は旧テンプレートなので捨てる。WHAT を持つ `big_plans/` だけ `docs/roadmap/` に残す。ルール・コード・ストーリー中の `.claude/plan/...` 参照は「`docs/roadmap/0N-*.md`」か削除に直す。
- **`SPEC.md` は存在しない**（architecture.md が「全体設計の正」とするがクローン内に無い）。参照を外し、AGENTS.md の「崩してはいけない前提」節を設計の正とする。`.claude/rules/roles.md`・`writing-rules` スキルへの参照も削る。
- **`.gitignore`** はクローン側の末尾が `.env.example` と連結して壊れている（`tests/generated/OPENAI_API_KEY=`）ので書き直す。`.playwright-cli/` も含める。
- **`.env`**: `load_dotenv()` が引数なし（CWD 探索）。tool-conventions 規則 3 に合わせ `Path(__file__)` 基準で `workflow/playwright-app/.env` 固定にする（`scripts/vertical_slice/main.py`・`scripts/server/main.py`）。
- **uv ワークスペース**: `package = false` のまま載る（仮想メンバーとして `uv lock` が通ることを実測）。`requires-python >=3.11` はそのまま。
- `cli_executor.py:44` の存在しない `.claude/skills/playwright-cli/SKILL.md` は `using-playwright-cli` スキルに直す。クローン側 `rules/playwright-app/plans.md` が定める旧プラン運用は捨てる（このリポジトリの `plans/` 運用に従う）。
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

## 実行中に判明した変更

- 2026-11-15（Step 1）: `.claude/plan/` は持ち込まず `big_plans/` だけ `docs/roadmap/` へ、`SPEC.md` 不在、`.gitignore` 破損、`.env` の固定パス化、`package = false` で載ることを反映。根拠は [progress/01-research-results.md](progress/01-research-results.md) の 1・8。
- 2026-11-16（Step 4 実施）: Windows で動かすためにコードを 2 点直した。(a) `playwright-cli`・`npx` を `shutil.which` の解決済みパスで起動（`.cmd` シムは素の名前では `subprocess` から起動できない）。(b) `subprocess.run` を `encoding="utf-8", errors="replace"` に（`text=True` だと cp932 で復号に失敗し stdout が `None` になって `CliExecutor.execute` が `TypeError`）。どちらも `cli_executor.py`・`runner.py`。
- 2026-11-16: `tests/generated/` は `.gitkeep` だけ追跡する（無いと `just cost` が `not found` で失敗するため）。
- 2026-11-16: クローン側の `scripts/temp/`（サーバー経由のスモークテスト。クローンでも gitignore）は持ち込まず、`docs/session-server.md` の言及を「持ち込んでいない」に書き換えた。`SPEC.md N章` は roadmap・NEXT では「元設計書（未収録）N章」とし、AGENTS.md の「崩してはいけない前提」を設計の正とした。
- 2026-11-16 確認: `uv sync`・`pnpm install` 成功、`just server` 起動（`/openapi.json` 応答）、`just cost`（0 件で正常終了）、クローンで生成済みの `.spec.ts` 1 本を一時的に置いて `just test` が通過（課金なし。ブラウザは `playwright install --only-shell chromium`）、`CliExecutor` で open・snapshot・`ALLOWED_DOMAINS` による遮断を確認。`slice` の実 AI 実行は未実施（課金のため）。
