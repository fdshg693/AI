---
name: "skills-site instructions"
description: "Instructions for files in skills-site/"
applyTo: "skills-site/**"
---

# スキル公開サイト

`skills-site` は、 `generated/catalog.json`(`tools\internal\plugin_meta\generate\generate_skill_catalog.py`によって生成) と `public/downloads/` を入力に、Astroで一覧・詳細ページを静的生成するサイトです。公開するのは登録済みスキルの `SKILL.md` 本文、frontmatter由来のメタデータ、スキルフォルダ単位のZIPだけです。

## ローカル開発

```powershell
pnpm --prefix skills-site install
pnpm --prefix skills-site run dev
```

ブラウザで表示されたローカルURLを開くと、一覧からスキル名で検索、またAIツール／プラグイン／ステータスで絞り込めます。詳細ページでは本文、メタデータ、ZIPに含まれるファイル一覧を確認できます。

## ビルドと検証

```powershell
pnpm --prefix skills-site run build
pnpm --prefix skills-site run validate
pnpm --prefix skills-site test
pnpm --prefix skills-site run preview
```

`build` はカタログとZIPを再生成したあと、`dist/` にAstroの静的出力を作ります。生成物は手編集せず、スキルの追加やfrontmatterの変更後に再生成してください。

`SITE_URL` を設定するとcanonical URLに、`SITE_BASE_PATH` を設定するとサブパス配信に対応します。

## ページ構成

- `/` — 全スキル一覧。スキル名の部分一致検索、AIツール、プラグイン、ステータスで絞り込めます。検索・絞り込みは React island（`src/components/react/SkillFilter.tsx`）で行い、外部解析SDKは含めません。「AIにスキルを提案してもらう」パネル（`src/components/AISuggest.astro` / `src/components/react/AISuggest.tsx`）から、自然文の質問に対してAIが関連スキルを提案する機能も利用できます。
- `/skills/<リポジトリ相対パス>` — `SKILL.md` のname・description・status、本文、リポジトリ相対パス、含有ファイル、ZIPダウンロードを表示します。

表示用のUIは `src/`、公開対象とfrontmatter・ZIPの正本は `scripts/` と `generated/catalog.json` に分離しています。将来検索やアクセス解析を追加する場合も、カタログ生成処理には公開データの責務だけを残します。

## AIによるスキル提案（サーバー側 OpenRouter）

- AIスキル提案は SWA managed Functions（`/api/suggest`）がサーバー保持の `OPENROUTER_API_KEY` で OpenRouter を呼び出す。クライアントに APIキーを入力させない（BYOK 廃止）。
- 提案用のスリム索引は `api/data/ai-index.json`（`path`/`name`/`description`/`tool`/`plugin`/`status.key`のみ）で、`catalog:build` が `generated/catalog.json` と同じ解決済みデータから同時に生成する。静的配信せず Functions バンドルに同梱する。
- 全文検索はビルド時 MiniSearch インデックス（`api/data/search-index.json`）を `/api/search` が参照する。テキスト検索はサーバー、ツール／プラグイン／ステータス絞り込みはクライアントと併用。
- `public/staticwebapp.config.json` の CSP `connect-src` は `'self'` のみ（OpenRouter 直叩きはしない）。
- 本番では Azure Portal（または `az staticwebapp appsettings set`）で Static Web App に `OPENROUTER_API_KEY` を設定する。ローカルでは `skills-site/.env` に `OPENROUTER_API_KEY` を設定するだけでよい（`api/src/lib/load-local-env.js` が Functions 起動時に `process.env.OPENROUTER_API_KEY` 未設定なら `../.env` を読み込むフォールバックを行うため、`api/local.settings.json` への二重設定は不要）。`local.settings.json` は `AzureWebJobsStorage` 等のホスト設定のみで、`api/local.settings.example.json` をコピーして使う。

## Azure Static Web Appsへの公開

Azureリソースは infra/main.bicep で作成します。`skills-site/.env.example` を `skills-site/.env`（gitignore済み）へコピーして値を設定すると、`skills-site/mise.toml` 経由で `AZURE_LOCATION` / `AZURE_RESOURCE_GROUP` / `AZURE_STATIC_SITE_NAME` / `GITHUB_REPOSITORY` が自動で読み込まれます（mise未activate、または `skills-site` 以外のカレントディレクトリでは読み込まれません）。同ファイルは `az` CLIの状態を `skills-site/.azure` に隔離する `AZURE_CONFIG_DIR` も設定するため、他プロジェクトやグローバルの `az login` 状態と混ざりません。詳細は infra/AGENTS.md を参照してください。

準備ができたら `skills-site` ディレクトリで次を実行してください。

```powershell
az login
az account set --subscription "<subscription-id>"
just azure-provision
just azure-set-github-secret
just azure-url
```

AZURE_LOCATION、AZURE_RESOURCE_GROUP、AZURE_STATIC_SITE_NAME の環境変数で既定値を変更できます。BicepはリソースグループとFree tierのStatic Web Appだけを作成し、ソースリポジトリとのAzure側連携は設定しません。

GitHub Actionsの .github/workflows/skill-site.yml は、Pull Requestではカタログ生成・ZIP検証・テスト・Astroビルド・API依存インストールまでを実行します。mainへのpushが成功した場合だけ、生成済みの `skills-site/dist` と `skills-site/api`（索引同梱）をAzure Static Web Appsへアップロードします。Azure側でフロントを再ビルドせず、APIは SWA が managed Functions としてビルドします。deployment tokenはGitHub Secret AZURE_STATIC_WEB_APPS_API_TOKEN からのみ読み込みます。

### 現在本番に出ているビルドの確認

- `build` スクリプト（`catalog:build` の後）は `scripts/write-build-info.mjs` を実行し、commit SHA・ブランチ・ビルド日時・（CI実行時のみ）workflow run URLを `public/build-info.json` として生成します。生成物はgitignore対象で手編集しません。
- このJSONはページフッターに short SHA とビルド日時として表示されるほか、`/build-info.json` として本番サイトから直接取得できます。今公開されているビルドがどのcommit・いつのものかは、サイトを見れば分かります。
- デプロイjobは成功後に `deploy-<UTC日時>-<short SHA>` 形式のgit tagを作成してpushします（例: `deploy-20260729T153000Z-abc1234`）。過去のデプロイ履歴はリポジトリのtag一覧から辿れ、ロールバックしたい場合は該当tagのcommitでworkflowを再実行（`workflow_dispatch`はカタログ検証のみのため、実際には該当commitへの再push、またはそのcommitをmainにcherry-pick/revertして通常のpushフローに乗せる）します。

### 障害時の確認

- verifyが失敗した場合は、公開対象の登録、frontmatter、ZIP、.env混入の検証エラーを修正してから再実行します。deployは実行されません。
- deployが失敗した場合は、GitHub repository Secretの名前と値、Static Web Appのdeployment token、just azure-urlの対象リソースを確認します。必要ならjust azure-set-github-secretでtokenを更新します。
- 公開対象やサイトの変更は、生成物を手編集せず、ソースと生成スクリプトを変更してからjust skills-site-checkで確認します。

サイト生成処理とAstroの静的出力はホスティングサービスから独立しています。将来Firebaseへ移行する場合は、BicepとAzure用workflowをFirebase用のリソース定義・デプロイworkflowへ置き換え、カタログスキーマ・ZIP仕様・UIはそのまま利用できます。
