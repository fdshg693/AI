---
# 前提: 確認に gh CLI が使え、`gh auth login` 済みであること。未認証なら確認を止めてその旨を伝える。
# シークレットの値は取得しない・ログに出さない。設定の変更はユーザーが依頼したときだけ行う。
# ワークフローの挙動は maintenance/docs/gh-actions-lifecycle.md。Azure の Application setting は site/skills-site/AGENTS.md。
# ai-tools.yaml には登録しない。
name: configuring-github
description: Lists the GitHub repository settings this repository's workflows require, including Actions secrets, workflow permissions, and the Pages source. Use when an Actions run fails because a secret or GitHub setting is missing, when setting up Actions or Pages for this repository, or when a new workflow needs a secret or permission.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: gh CLI
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: このリポジトリのワークフローが依存する GitHub 設定（Actions シークレット、workflow 権限、Pages）
  version: 1.0.2
---

# このリポジトリに必要な GitHub 設定

GitHub のリポジトリ設定だけを扱う。ワークフローがいつ何をするかは [gh-actions-lifecycle](../../../docs/gh-actions-lifecycle.md)。本番 `/api/suggest` 用の `OPENROUTER_API_KEY` は Azure Static Web Apps の Application setting であり、ここには含めない（[skills-site/AGENTS.md](../../../../site/skills-site/AGENTS.md)）。

設定の変更は、ユーザーが依頼したときだけ行う。シークレットの値はコマンド出力にも会話にも出さない。

## 手順

1. **失敗や依頼がどの設定かを決める** — ログの `::error::`、または下の表のワークフロー名で絞る。ワークフローの中身を追う必要が無いときは [gh-actions-lifecycle](../../../docs/gh-actions-lifecycle.md) に戻る。
2. **今の設定を名前だけ読む** — リポジトリルートで次を実行する。`{owner}/{repo}` は `gh repo view --json nameWithOwner --jq .nameWithOwner` の値。

   ```text
   gh api repos/{owner}/{repo}/actions/secrets --jq ".secrets[].name"
   gh api repos/{owner}/{repo}/actions/permissions/workflow
   gh api repos/{owner}/{repo}/pages --jq "{build_type,html_url}"
   ```

   Pages が HTTP 404 のときは、Source が GitHub Actions になっていない。

3. **不足を伝える** — 必須シークレットの名前、workflow 権限、Pages の Source のうち、手順2と食い違うものだけを挙げる。値は聞かない。
4. **依頼されたときだけ設定する** — `AZURE_STATIC_WEB_APPS_API_TOKEN` は下の「deployment token」の手順で Azure からコピーする。それ以外のシークレットは、ユーザーが持っている値を標準入力から渡す。

   ```text
   gh secret set NAME
   ```

   `echo` や `--body` に値を書かない。workflow 権限と Pages は、下のコマンドをユーザーの依頼があるときだけ実行する。

## 必須の Actions シークレット

置き場所は **リポジトリの Actions シークレット**（Settings > Secrets and variables > Actions）。Environment シークレットには置かない。`check-secrets` と `verify` は `environment:` を持たないため、Environment にだけ置くと読めない。

`GITHUB_TOKEN` は Actions が渡す。リポジトリシークレットとしては作らない。

| 名前                              | 使うワークフロー                             | 用途                                                                                              |
| --------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | `skill-site.yml` の check-secrets と deploy  | 対象 Static Web App の deployment token。Azure が発行した値を GitHub にコピーする。手順は直後の節 |
| `OPENROUTER_API_KEY`              | `skill-site.yml` の verify                   | `catalog:build` の埋め込み計算。未設定だと verify が失敗する                                      |
| `ANTHROPIC_API_KEY`               | `claude-issue-triage.yml`                    | issue 作成時の Claude triage                                                                      |
| `OPENAI_API_KEY`                  | `codex-issue-triage.yml`、`gaw-issue-triage` | `@codex` と `/gaw`。gh-aw は `CODEX_API_KEY` があればそちらを使う                                 |
| `OPENAI_KEY`                      | `pr-agent.yml`                               | PR コメントの `/describe` と `/review`。`OPENAI_API_KEY` とは別名                                 |

### `AZURE_STATIC_WEB_APPS_API_TOKEN` は Azure の deployment token

値はこちらで決めない。`skills-site` の Static Web App が持つ deployment token（`az staticwebapp secrets list` の `properties.apiKey`）を、GitHub のリポジトリシークレットへコピーする。

Static Web App が既にあるとき、`site/skills-site` ディレクトリで次を実行する。Azure CLI の出力を `gh secret set` に渡し、トークンは画面にも会話にも出さない。

```text
just azure-set-github-secret
```

リソースが無いときは、その前に `site/skills-site` で `az login` と `just azure-provision` を行う。対象は `site/skills-site/.env` の `AZURE_RESOURCE_GROUP` と `AZURE_STATIC_SITE_NAME`（未設定時は `rg-ai-skill-catalog` / `ai-skill-catalog`）。`just azure-token` はトークンを表示するので、確認専用にし、出力を会話に貼らない。

発行とコピーの詳細は [skills-site/AGENTS.md](../../../../site/skills-site/AGENTS.md) と [skills-site/infra/AGENTS.md](../../../../site/skills-site/infra/AGENTS.md)。

次は lock ファイルに名前が出るが、フォールバックがあるのでリポジトリシークレットとしては作らない。

- `CODEX_API_KEY` — 無いときは `OPENAI_API_KEY`
- `GH_AW_GITHUB_TOKEN`、`GH_AW_GITHUB_MCP_SERVER_TOKEN`、`COPILOT_GITHUB_TOKEN` — 無いときは `GITHUB_TOKEN`

## 必須のリポジトリ設定

### Actions の workflow 権限

Settings > Actions > General > Workflow permissions。

- `default_workflow_permissions`: `read`
- `can_approve_pull_request_reviews`: `false`（Allow GitHub Actions to create and approve pull requests はオフ）

書き込みが要るジョブは、各ワークフローが `permissions` を自分で宣言している。`skill-site.yml` の deploy は `contents: write`（デプロイタグの push）、`tool-release.yml` は `contents: write`、`tools-site.yml` の deploy は `pages: write` と `id-token: write`。既定を `write` に上げない。

ユーザーが直すとき:

```text
gh api -X PUT repos/{owner}/{repo}/actions/permissions/workflow -f default_workflow_permissions=read -F can_approve_pull_request_reviews=false
```

Actions 自体は有効のままにする（`allowed_actions` は `all`）。

### GitHub Pages

`tools-site.yml` は `actions/deploy-pages` と environment `github-pages` で公開する。Settings > Pages > Build and deployment > Source は **GitHub Actions**。

サイトが無い（GET が 404）ときだけ作成する。

```text
gh api -X POST repos/{owner}/{repo}/pages -f build_type=workflow
```

既にあり `build_type` が `workflow` でないときだけ更新する。

```text
gh api -X PUT repos/{owner}/{repo}/pages -f build_type=workflow
```

`skill-site.yml` の deploy は environment 名 `production` を使う。必須レビュアーは付けない。付けると main へのデプロイが承認待ちで止まる。

## 変えないこと

- Fork の PR にシークレットを渡すために `pull_request_target` を足さない。Fork PR で `OPENROUTER_API_KEY` が読めず verify が落ちるのは意図した動作。
- issue / PR bot の `author_association` が `OWNER` または `COLLABORATOR` である制限を外さない。
- `OPENROUTER_API_KEY` の GitHub Actions シークレットを、Azure の Application setting の代わりにしない。デプロイトークンでは Application setting を注入できない。

## 関連

- [gh-actions-lifecycle](../../../docs/gh-actions-lifecycle.md) — ワークフローのトリガー、権限、失敗の意味
- [skills-site/AGENTS.md](../../../../site/skills-site/AGENTS.md) — デプロイトークンの発行と、Azure 側の `OPENROUTER_API_KEY`
- [CONTRIBUTING.md](../../../../CONTRIBUTING.md) — Fork PR で一部の CI が落ちる理由
