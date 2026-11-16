---
type: Plan Step
status: ready
---

# Step 2: `pwq`・`pwdo`・テストサイトを `tools/browser/` へ

> [00-overview.md](00-overview.md) の続き。[01](01-research-inventory.md) の結果（パス・規約差・models.json の扱い）を反映してから着手する。

## やること

tools サブモジュールに `browser/` カテゴリを作り、クローン側の `.claude/tools/pwq`・`.claude/tools/pwdo`・`resources/` を移す。コマンド名で起動できる配布 CLI にし、ワークスペース・レジストリ・ローカル設定・索引に登録する。

## 読むべきファイル

**置き場所と CLI の形を決めるため（最優先）**

- `maintenance/docs/tools-directory-layout.md` — カテゴリ追加の手順
- `maintenance/docs/tool-conventions.md` — `--version`・`version`・README の必須事項
- `tools/llm/aim2/`（`package.json`・`tsup.config.ts`・`README.md`・`AGENTS.md`）— 既存の TS ツールの形。models.json を持つ前例

**登録先の書式を確認するため**

- `registry/repo-tools.yaml` — エントリの形（`path`・`release` 等）
- `registry/local-configs.yaml` — `tools/llm/aim2/models.json` のエントリ
- `pnpm-workspace.yaml` — `tools/llm/aim2` の載せ方
- `tools/README.md` — 役割索引の書式

**移す元（クローン側）**

- `.claude/tools/pwq/README.md`・`pwdo/README.md` — 契約・実測。パスの書き換え箇所
- `.claude/tools/*/src/config.ts` — 既定のキャッシュ先・models.json・`.env` の探索パス
- `.claude/rules/tools/pwq.md`・`pwdo.md` — AGENTS.md に移す規約
- `resources/INDEX.md`・`serve.sh`・`serve.py`・`nginx/nginx.conf`、`.claude/rules/resources/custom-pages.md`

## 触るファイル

- 新規 `tools/browser/pwq/`・`tools/browser/pwdo/` — `src/`・`package.json`・`tsconfig.json`・`tsup.config.ts`・`README.md`・`models.json.example`・`.env.example`。`pnpm-lock.yaml`・`pnpm-workspace.yaml`（ツール内のもの）は持ち込まない（アンブレラのルートだけが持つ）
- 新規 `tools/browser/pwq/AGENTS.md`・`CLAUDE.md`、`tools/browser/pwdo/AGENTS.md`・`CLAUDE.md` — クローン側 `rules/tools/*.md` の規約（`paths:` frontmatter は外す）
- 新規 `tools/browser/pwdo/docs/delegation-notes.md` — pwdo の実測根拠（置き場所は 01 で確定）
- 新規 `tools/browser/test-sites/` — `resources/` 一式、`AGENTS.md`（`custom-pages.md` の規約）、`README.md`（`INDEX.md` を改名 or 併置）
- 変更 `tools/README.md` — `browser/` カテゴリの節
- 変更 `tools/.gitignore`（または各ツールの `.gitignore`）— `dist/`・`node_modules/`・`models.json`・`.env`・`.playwright-cli/`
- 変更 `.gitignore`（アンブレラ）— `.playwright-cli/`（`pwq`/`pwdo`/`playwright-cli` がここに認証情報を含みうるストアを作る。`site-recon.md` もリポジトリ直下で無視されている前提）
- 変更 `pnpm-workspace.yaml` — `tools/browser/pwq`・`tools/browser/pwdo` を追加、`pnpm-lock.yaml` 再生成
- 変更 `registry/repo-tools.yaml` — `pwq`・`pwdo` を追加（`release` の可否は 01 で決める）
- 変更 `registry/local-configs.yaml` — `tools/browser/pwq/models.json`・`tools/browser/pwdo/models.json`
- 変更 `maintenance/docs/tools-directory-layout.md` — カテゴリ一覧に `browser/`
- 変更 `justfile`（アンブレラ）— テストサイトの起動レシピ（例 `just test-sites`）。`serve.sh` が nginx 前提なので、Windows では `serve.py` を `uv run --no-project` で呼ぶ形を既定にする（標準ライブラリのみ。`--no-project` でワークスペース全体の sync を避ける）

## 決定事項

- **`pwq` の引数素通し・ref を生成させない・LLM を呼ぶコマンドの限定・横取りしない条件**（クローン側 `rules/tools/pwq.md`）は AGENTS.md に原文のまま移す。設計の不変条件なので要約で弱めない。
- **pwdo README 冒頭の「状態: Step5 まで完了…」のプランリンク**は、完了プランを持ち込まないので「設計の経緯は `docs/delegation-notes.md`」の 1 行に置き換える。契約本体（CLI 表面・返却スキーマ・終了状態 5 値）は変えない。
- **パスの書き換え**: README・ソース中の `.claude/tools/pwq/dist/cli.js` → `pwq`、`resources/` → `tools/browser/test-sites/`、`.claude/skills/using-playwright-cli/...` → 01 で決まるスキルの場所。キャッシュ先（`.playwright-cli/`）は cwd 相対のままでよいか 01 の結果で判断する。
- **models.json**: 実体は gitignore、`.example` だけをコミットする。クローン側の `models.json` は実体なのでコピーしない。
- 注意: `pwq`/`pwdo` は実行に `playwright-cli`（`@playwright/cli`）のグローバル導入と `OPENROUTER_API_KEY` が要る。README の前提に書き、ツール自身は依存として抱えない。
- 注意: `test-sites` の `custom_pages` はルート直下配信（`http://localhost:8080/<page>.html`）を playwright-app のストーリーが前提にしている。配信位置は変えない（04 と整合）。
- 注意: `nginx.conf`・`serve.py` にクローン側の絶対パスや `resources/` 前提が無いか確認してから移す。`custom-pages.md` の「サイト追加時に更新する 4 か所」のパスも移設先に直す。

## ルール更新ポイント

- `tools/browser/{pwq,pwdo,test-sites}/AGENTS.md` を新設（規約の正本をここにする）。
- `maintenance/docs/tools-directory-layout.md` にカテゴリを 1 行足す。
- `docs/integrations/cli-tools.md` に `pwq`/`pwdo` の入れ方を足すか、01 の結果（`release` の可否）で判断する。

## 進め方

- 実行主体: メインのエージェント。
- TODO 化: (1) pwq 移設とビルド確認、(2) pwdo 移設とビルド確認、(3) test-sites 移設と起動確認、(4) 登録・索引・規約文書。tools サブモジュールで 1〜2 コミット → アンブレラで `git add tools` と registry/workspace の変更を 1 コミット。
- 確認: `pnpm install` → 各ツールで `pnpm build`、`pwq --version`・`pwdo models`、`just test-sites` で `http://localhost:8080/tables/` が開け、`pwq snapshot` がダイジェストを返すこと。
