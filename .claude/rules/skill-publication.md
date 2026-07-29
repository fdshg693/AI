---
paths:
  - "skills-site/**"
  - ".github/workflows/skill-site.yml"
---

# スキル公開成果物の規約

- 公開対象のルートは `skills-site/scripts/source-registry.mjs` が `ai-tools.yaml`（リポジトリ直下）から自動的に導出する。新しいAIツールやプラグインのスキルを追加したら、`ai-tools.yaml` 側にプラグインを登録する（`source-registry.mjs` を直接編集しない）。
- スキャン対象は `ai-tools.yaml` に登録されたルート配下のみ。登録ルート外にある `SKILL.md`（例: `repo-meta/` のように意図的に`ai-tools.yaml`へ登録しないプラグイン）は存在してもエラーにならず、単に公開対象から漏れる。
- `ai-tools.yaml` に登録済み（＝マーケットプレイスには載る）だが、このサイトでは非公開にしたいプラグイン／スキルがある場合は `skills-site/site-overrides.yaml`（`skills-site/scripts/site-overrides.mjs` が読み込む）の `exclude.sources` / `exclude.skills` に追記する。逆に、`ai-tools.yaml` に無いものをこのファイルだけで公開対象に追加することはできない。
- スキルの安定したID・URLは `SKILL.md` の `name` ではなく、リポジトリ相対パスを使う。同名スキルがあっても別スキルとして扱う。
- `skills-site/generated/` と `skills-site/public/downloads/` の生成物は、ローカルビルドまたはCIで毎回再生成し、手編集しない。
- ZIPはスキルフォルダ配下のファイルを含めるが、ファイル名が `.env` のファイルは大文字小文字を区別せず除外する。シンボリックリンクとスキルルート外へ解決されるパスは含めない。
- 公開前にカタログとZIPの検証を実行し、未登録の `SKILL.md`、必須frontmatter不足、危険なパス、`.env` の同梱を見逃さない。
- カタログには`SKILL.md`の`meta:`ブロックの構造化情報（`requiresSkills`/`requiresHooks`/`requiresRepoTools`の解決結果を含む）も含まれる。リンク解決ロジックの決定事項は`.claude/plans/skills-site-meta-display/01-data-layer.md`を参照。

- 公開workflowは `skills-site/dist` と `skills-site/api`（SWA managed Functions）をデプロイする。リポジトリルートやサイトのソースをAzure Static Web Appsへ直接公開しない。
- Azureのdeployment tokenはGitHub Actions Secretからのみ読み込み、`.env`・Bicepの出力・リポジトリファイルへ保存しない。
- OpenRouter 等のサーバー秘密値（`OPENROUTER_API_KEY`）は SWA の Application settings にのみ置き、クライアントやリポジトリへ漏らさない。
- カタログ生成、テスト、公開成果物検証、Astroビルドのいずれかが失敗した場合はデプロイしない。
