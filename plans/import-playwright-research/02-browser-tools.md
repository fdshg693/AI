---
type: Plan Step
status: implementing-done
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
- 新規 `docs/topics/browser-automation/`（アンブレラ）— 調査ノート 5 本（`delegation`・`site-recon`・`script-cli-roundtrip`・`scripted-automation`・`browser-handoff`）と `index.md`。OKF frontmatter を付ける。変更 `docs/index.md`・`docs/log.md`。03 のスキル README もここを参照するので、ノートは全部この Step で移す
- 変更 `tools/browser/{pwq,pwdo}/src/` — `config.ts`（`.env` を固定パスに）、`store.ts`・`cli.ts`（ストア既定を git ルート基準に、`--version`）、`passthrough.ts`・`report.ts`・`guards.ts`（`.claude/...` の文言）
- 新規 `tools/browser/test-sites/` — `resources/` 一式、`AGENTS.md`（`custom-pages.md` の規約）、`README.md`（`INDEX.md` を改名 or 併置）
- 変更 `tools/README.md` — `browser/` カテゴリの節
- 変更 `tools/.gitignore`（または各ツールの `.gitignore`）— `dist/`・`node_modules/`・`models.json`・`.env`・`.playwright-cli/`
- 変更 `.gitignore`（アンブレラ）— `.playwright-cli/`（`pwq`/`pwdo`/`playwright-cli` がここに認証情報を含みうるストアを作る。`site-recon.md` もリポジトリ直下で無視されている前提）
- 変更 `pnpm-workspace.yaml` — `tools/browser/pwq`・`tools/browser/pwdo` を追加、`pnpm-lock.yaml` 再生成
- 変更 `registry/repo-tools.yaml` — `pwq`・`pwdo` を追加（`install: "cd tools/browser/pwq && pnpm add -g ."` の形。`release` は付けない＝tools-site に載せない。実験段階の 0.1.0 のため）。pwdo は `requires_tools` に `pwq`
- 変更 `registry/local-configs.yaml` — `tools/browser/pwq/models.json`・`tools/browser/pwdo/models.json`
- 変更 `maintenance/docs/tools-directory-layout.md` — カテゴリ一覧に `browser/`
- 変更 `justfile`（アンブレラ）— テストサイトの起動レシピ（例 `just test-sites`）。`serve.sh` が nginx 前提なので、Windows では `serve.py` を `uv run --no-project` で呼ぶ形を既定にする（標準ライブラリのみ。`--no-project` でワークスペース全体の sync を避ける）

## 決定事項

- **`pwq` の引数素通し・ref を生成させない・LLM を呼ぶコマンドの限定・横取りしない条件**（クローン側 `rules/tools/pwq.md`）は AGENTS.md に原文のまま移す。設計の不変条件なので要約で弱めない。
- **pwdo README 冒頭の「状態: Step5 まで完了…」のプランリンク**は、完了プランを持ち込まないので「設計の経緯は `docs/delegation-notes.md`」の 1 行に置き換える。契約本体（CLI 表面・返却スキーマ・終了状態 5 値）は変えない。
- **パスの書き換え**: README・ソース中の `.claude/tools/pwq/dist/cli.js` → `pwq`、`resources/` → `tools/browser/test-sites/`、`.claude/skills/using-playwright-cli/...` → スキル名（`using-playwright-cli`・`sharing-browser-with-user`。プラグイン `browser`）、`.claude/docs/*-notes.md` → `docs/topics/browser-automation/*.md`（アンブレラルート相対のパス表記。サブモジュールからは相対リンクにしない）、完了プランへのリンク → 1 行の要約。
- **設定（tool-conventions に合わせる。ユーザー確認済み）**: `.env` は祖先遡上をやめ、ツール直下の固定パス 1 か所だけ（aim2 の `src/config.ts` と同じ形。プロセス環境変数優先、欠落時は探した絶対パスを出す）。`.env.example` は別リポジトリのパス（`C:\C\job_hunt`・`.agents/tools/...`）を含むので書き直す。
- **ストア既定**（`.playwright-cli/pwq`・`.playwright-cli/pwdo`）は cwd ではなく git ルート基準（`.git` を親へ探す。git 外は cwd）。明示指定（`--pwq-store` 等）はそのまま。
- **`--version`**: 両ツールとも `<command> <version>` の 1 行。pwq は `--version` を playwright-cli に素通ししていたのをやめる（`--pwq-version` は残す）。README の素通しの説明も直す。
- **pwdo の pwq 解決**は `PWDO_PWQ` → PATH → 隣の `../pwq/dist/cli.js`。兄弟配置なので隣解決はそのまま効く。ヒント文言だけ `cd tools/browser/pwq && pnpm build` に直す。
- **models.json**: 実体は gitignore、`.example` だけをコミットする。クローン側の `models.json` は実体なのでコピーしない。
- 注意: `pwq`/`pwdo` は実行に `playwright-cli`（`@playwright/cli`）のグローバル導入と `OPENROUTER_API_KEY` が要る。README の前提に書き、ツール自身は依存として抱えない。
- 注意: `test-sites` の `custom_pages` はルート直下配信（`http://localhost:8080/<page>.html`）を playwright-app のストーリーが前提にしている。配信位置は変えない（04 と整合）。
- 注意: `nginx.conf`・`serve.py` にクローン側の絶対パスや `resources/` 前提が無いか確認してから移す。`custom-pages.md` の「サイト追加時に更新する 4 か所」のパスも移設先に直す。

## ルール更新ポイント

- `tools/browser/{pwq,pwdo,test-sites}/AGENTS.md` を新設（規約の正本をここにする）。
- `maintenance/docs/tools-directory-layout.md` にカテゴリを 1 行足す。
- `docs/integrations/cli-tools.md` は変えない（`release` しないため。入れ方は各 README）。
- `maintenance/docs/tools-directory-layout.md` に「規約を持つツールは AGENTS.md に本文を書いてよい」例外を 1 行（00 のルール更新ポイント）。

## 進め方

- 実行主体: メインのエージェント。
- TODO 化: (1) pwq 移設とビルド確認、(2) pwdo 移設とビルド確認、(3) test-sites 移設と起動確認、(4) 登録・索引・規約文書。tools サブモジュールで 1〜2 コミット → アンブレラで `git add tools` と registry/workspace の変更を 1 コミット。
- 確認: `pnpm install` → 各ツールで `pnpm build`、`pwq --version`・`pwdo --version` が `<command> 0.1.0`、`pwdo models`、`just test-sites` で `http://localhost:8080/tables/` が開け、`pwq snapshot` がダイジェストを返し、ストアが git ルートの `.playwright-cli/pwq/` にでき git status に出ないこと。

## 実行中に判明した変更

- 2026-11-15（Step 1）: ノートの置き場所を `docs/topics/browser-automation/` に確定しこの Step で移す、設定・ストア・`--version` の規約合わせ、`release` なしを「触るファイル」「決定事項」「ルール更新ポイント」に反映。根拠は [progress/01-research-results.md](progress/01-research-results.md) の 1・5・6。
- 2026-11-15（Step 2 実施）: 実施結果と、プランから外れた点。
  - `tools/browser/{pwq,pwdo,test-sites}` を作成。改行は tools の `.gitattributes`（`eol=lf`）に合わせて LF に揃えた（クローン側は CRLF 混在）。
  - `config.ts` に `readPackageVersion`・`findGitRoot`/`baseDir` を足した。`--version` は引数のどこにあっても `<command> <version>` を返す（pwq は playwright-cli の版数を `-v` で素通し）。
  - `.gitignore` はツールごとに置いた（`node_modules/`・`dist/`・`.env`・`models.json`・`.playwright-cli/`）。アンブレラの `.gitignore` には `.playwright-cli/`・`test-results/`・`playwright-report/` を足した。
  - `INDEX.md` は `README.md` に改名した（AGENTS.md のチェーンに合わせる）。`custom_pages/pages/index.html` の `resources/INDEX.md` 表記も直した。
  - ノートはタイプ `Research Notes`・`tags: [tools]`。元の `step`・`verified-on`・`verified-with` は残した。スキル内ファイルへのリンクは、Step 3 でスキルを移すまで切れないように、スキル名での文字参照にした（03 で必要ならリンクに戻す）。
  - `pnpm install` で `@types/node` の重複が 26.5.1 にまとまり、site 系パッケージの peer 解決も変わった（lock の差分）。
  - 確認済み: typecheck・build、`pwq --version`/`pwdo --version`、`pwdo models`、`just test-sites` で `/tables/` が 200、`docs/` から実行した `pwq snapshot` のストアが `<アンブレラ>/.playwright-cli/pwq/` にでき無視されている、`test_registered_cli_versions`・`skill-repo-tools-check`・`generate` が通る。`local-configs-check` の「example が未追跡」はコミット前のため。
  - 注意: `pwq open … | tail` のようにパイプへ出すと、`open` が起こしたデーモンがパイプを掴んで終わらなかった（ファイルへリダイレクトすれば終わる。デーモンがパイプを継承するためと推定。素の `playwright-cli` をパイプで試してはいない）。
  - コミットは未実施（tools サブモジュール → アンブレラの 2 段階）。
