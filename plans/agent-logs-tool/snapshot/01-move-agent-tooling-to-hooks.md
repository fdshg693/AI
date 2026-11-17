---
type: Plan Step
status: planning-breakdown
---

# Step 1: agent-tooling を hooks/ 配下へ移す

> [00-overview.md](00-overview.md) の続き。他ステップと独立しているが、以降のステップが新パスを前提にするため最初に行う。

## やること

`agent-compat/agent-tooling/` を `agent-compat/hooks/agent-tooling/` へ `git mv` し、リポジトリ全体（アンブレラ・各サブモジュール）の参照を新パスに置き換える。挙動は変えない。生成物（`hooks/generated/`）を再生成し、テスト・検査・フックの再インストールが通る状態にする。

## 読むべきファイル・実行推奨Grep

**移動の影響範囲を確定するため（優先度: 高）**

- Grep: `rg -l "agent-compat/agent-tooling|agent-tooling" --hidden -g '!.git'` — 着手時点の参照元一覧（計画時点で約 60 ファイル・138 箇所）。`maintenance/scripts/reorg/tables/*.json` は過去の移動記録なので書き換えない
- 読む: `registry/repo-hooks.yaml` — `catalog:` のパス。skill-tools がここからカタログを引く
- 読む: `tools/skill-tools/skill_tools/hooks/catalog.py` と `tools/skill-tools/tests/test_hooks_catalog.py` — カタログパスをハードコードしていないか
- 読む: `agent-compat/agent-tooling/agent_tooling/hooks/build/build.py`・`tests/test_builder.py`・`tests/test_codex_parity.py` — リポジトリルートからの相対パスを前提にした箇所
- 読む: `agent-compat/agent-tooling/agent_tooling/notify/macos.py`・`notify/macos_helper/build.sh`・`adapters/*/notify.py` — 生成物・インストール先にソースパスが埋め込まれていないか

**ビルド・CI の入口を確認するため（優先度: 中）**

- 読む: `lefthook.yml`（L40-48）・`maintenance/lefthook/submodule.yml` — 再生成ジョブのパス
- 読む: `justfile`（L55 付近の hooks 系レシピ）・`pyproject.toml`（uv workspace members）
- 読む: `site/skills-site/scripts/build-catalog.mjs`・`site/skills-site/tests/publication.test.mjs` — agent-tooling パスの参照理由
- 読む: `.github/workflows/` — Grep で agent-tooling を含む workflow（各サブモジュールの `.github/` も）

**規約（優先度: 低）**

- 読む: `maintenance/docs/repo-layout.md`「サブモジュール」「Junction」節、`maintenance/docs/hook-distribution.md`

## 触るファイル

### 新規

- `agent-compat/hooks/README.md` — `hooks/` の中身（agent-tooling）への 1 段の案内

### 変更

- `agent-compat/agent-tooling/` → `agent-compat/hooks/agent-tooling/`（`git mv`。`__pycache__`・`*.egg-info` は移さず削除して再生成）
- agent-compat 内: `README.md`・`AGENTS.md`・`docs/differences/{kilo,cline}.md`・`formats/kilo/README.md`・移動先内部の README/AGENTS/justfile/tests/build.py/notify（`agent-compat/agent-tooling` の文字列は一括置換）
- 移動先内部で深さに依存する箇所（grep で見つからない）: `tests/conftest.py`（`parents[3]`→`[4]`）・`tests/test_codex_parity.py`（`parents[1] / "agent_tooling"` 起点に）・`tests/test_builder.py`（`REPO_ROOT`）。パッケージ外への相対リンクは `../` を 1 段足す: `AGENTS.md`・`agent_tooling/hooks/{AGENTS,REFERENCES}.md`（`rg -n '\]\((\.\./){2,}' -g '*.md'` で洗い出す）
- アンブレラ: `registry/repo-hooks.yaml`・`registry/ai-tools.yaml`・`registry/meta_field.yaml`・`pyproject.toml`・`uv.lock`・`justfile`・`lefthook.yml`・`maintenance/lefthook/submodule.yml`・`README.md`・`README_EN.md`・`AGENTS.md`・`.claude/.gitignore`・`.claude/hooks/AGENTS.md`・`maintenance/docs/*.md`（hook-distribution / repo-layout / justfile-conventions / index / claude-code-first-skills / repo-ssot-pattern / skill-tools-contract）・`maintenance/plugin/skills/{committing,exploring-this-repo}/SKILL.md`
- ルート直下の生成コピー（`ai-tools.yaml`・`repo-hooks.yaml` 等）— 手編集せず生成し直す
- tools: `_plugin/my-tools/skills/task-tracker/`（`skill_tools/hooks/catalog.py`・`tests/test_hooks_catalog.py`・`skill-tools/README.md` はパッケージ名の言及だけでパスを持たないので変更不要）
- skills: `plugins/cc-knowledge/skills/writing-hooks/SKILL.md`（frontmatter を触るなら `meta.version` を上げる）
- site: `skills-site/scripts/build-catalog.mjs`・`skills-site/tests/publication.test.mjs`

## 決定事項・注意点／落とし穴

| 決定・注意 | 理由 |
| ---------- | ---- |
| パッケージ名・コマンド名・`catalog.json` の形式は変えない | 変えるのはパスだけにして、移動の差分をレビューしやすくする |
| 編集可能インストール（`uv tool install --editable agent-compat/agent-tooling`）は移動で壊れる。完了後に新パスで入れ直し、README の手順も更新 | editable はソースパスを保持する |
| `catalog.json`・生成フックにソースパスが埋め込まれていれば `generate` で再生成し、`just hooks-update`・`just sub-agent-hooks-update` を実行 | `.claude/hooks/` 等のインストール先は直接編集しない（AGENTS.md） |
| `~/.claude/settings.json`・`~/.codex/hooks.json`・`~/.config/kilo/plugin/` のグローバル登録に旧パスが残っていないか確認する | グローバル導入（`hooks update --global`）分はリポジトリ外 |
| サブモジュールのコミット順は agent-compat → tools・skills・site → アンブレラ（ポインタ＋参照更新）。途中状態で他エージェントが作業すると壊れて見えるので、1 セッションで通しで終える | 2 段階コミット。同時作業が頻繁にある |
| push の順もコミット順と同じ（agent-compat を先に main へ） | アンブレラ CI の `uv lock --check`・GitHub source の skill-tools・skills-site のリンクが新パスの gitlink を前提にする |
| 生成物ヘッダ（`build.py` の `GENERATED_MARK`・`generatedBy`）は正しい新パス `agent-compat/hooks/agent-tooling/agent_tooling/hooks/build/build.py` にする。全生成物の差分が出て、配布先は `hooks update`（グローバルは `--global`）が必要 | 旧ヘッダは `agent_tooling/` が抜けた誤ったパスだった |
| `pyproject.toml` を変えたら `uv lock` と `uv sync`（ルート `.venv` の editable finder が旧パスを持つ） | CI の `uv lock --check` と揃える |
| Junction（`.links.yaml`）は agent-tooling を指すエントリが無く変更不要 | レビューで確認済み |
| `maintenance/scripts/reorg/tables/` は書き換えない | 過去の移動の記録 |
| 移動後に `codegraph sync` | 索引が旧パスを指したままになる |

## ルール更新ポイント

- `agent-compat/AGENTS.md`「このフォルダの責務」: `agent-tooling/` を `hooks/agent-tooling/` に。`hooks/`（フック・コンテキスト注入）と、Step4 で足す `logs/`（ログ検索・集計）の役割を 1 行ずつ
- `maintenance/docs/repo-layout.md`: 置き場所表の「マルチ AI 対応の仕組み」行とサブモジュール表の agent-compat 行
- `maintenance/docs/hook-distribution.md`: 正本パスの全置換（description frontmatter を含む）
- AGENTS.md（ルート）の Behaviour にあるフック正本パス

## 進め方

- **実行主体**: メインエージェント。参照元の機械的置換の洗い出しだけは Explore サブエージェントに委任してよい（置換の採否はメインが判断）。
- **TODO化**: (1) agent-compat 内の移動と内部参照・テスト、(2) tools/skills/site の参照更新、(3) アンブレラの参照・生成物・フック再インストール、の 3 項目。それぞれ `just --justfile agent-compat/hooks/agent-tooling/justfile test`・`generate-check`、アンブレラの pre-commit が通ることを完了条件にする。
