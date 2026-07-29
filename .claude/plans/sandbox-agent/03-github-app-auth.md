# Step 3: GitHub App作成・installation token取得/更新・git認証注入

[02-docker-image.md](02-docker-image.md) の続き。GitHub App自体の作成（GitHub UI操作）は本ステップの手順として明文化するが、実際のApp登録操作はコードでは自動化しない（一度きりの手動セットアップ）。

## やること

1. GitHub App（Contents: Read、Issues: Read & Write、Pull requests: Read & Write の最小権限）を作成する手順をドキュメント化する。
2. installation access tokenを取得・キャッシュ・期限切れ前に再発行するPythonスクリプトを実装する。
3. 取得したトークンをgitのHTTPS認証（`git clone`/`git push`）に使えるように注入する仕組みを実装する。

## 読むべきファイル・実行推奨Grep

**調査結果の裏取りのため（優先度: 高）**

- 読む: [01-research.md](01-research.md) の「GitHub App installation access token」節 — エンドポイント・有効期限・git認証形式はここに確定済み

**JWT署名の実装方法を確認するため（優先度: 高、未調査）**

- Web調査推奨キーワード: `GitHub App JWT PyJWT RS256 生成方法` — GitHub Appの秘密鍵（PEM）を使ったJWT生成の具体的なPythonライブラリ・アルゴリズム（RS256）・有効期限（最大10分）をこのステップ着手時に確認する（[01-research.md](01-research.md)では取得エンドポイントまでは調査済みだがJWT生成自体は未調査）

**既存の環境変数注入パターンを確認するため（優先度: 中）**

- 読む: `tools/infra/ai-logs/scripts/client_env.py` — このリポジトリでの「秘密情報を環境変数経由で渡す」既存実装のスタイル

## 触るファイル

### 新規

- `tools/sandbox/github_app/get_installation_token.py` — JWT生成 → installation access token取得 → 有効期限とともに返す。呼び出し元（[04-orchestrator.md](04-orchestrator.md)のワーカー）が期限切れ前（例: 発行から50分後）に再取得する
- `tools/sandbox/github_app/git_credential_inject.py` — 取得したトークンを使い、コンテナ内のリポジトリのremote URLを`https://x-access-token:<TOKEN>@github.com/owner/repo.git`形式に書き換える（もしくはgit credential helperとして設定する）
- `tools/sandbox/docs/github-app-setup.md` — GitHub App作成手順（権限設定・秘密鍵ダウンロード・Installation ID確認・リポジトリへのインストール）を画面操作ベースで記載

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                            | 理由                                                                                                                                                                                                                                                                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| installation access tokenはコンテナ起動のたびに新規取得する（永続キャッシュしない）                                                                             | 1 ISSUE = 1使い捨てコンテナ運用のため、コンテナ内でのキャッシュに寿命管理の複雑さを持ち込む必要が無い                                                                                                                                                                                                                      |
| GitHub App秘密鍵（PEM）はコンテナに環境変数（Base64等）経由で注入し、イメージには焼き込まない                                                                   | イメージをレジストリにpushする将来（クラウド移行時）を見据え、秘密情報をイメージレイヤーに残さない                                                                                                                                                                                                                         |
| 権限は最小構成（Contents: Read、Issues: Read & Write、Pull requests: Write）とし、Contents: Writeは付与しない代わりにgit pushはブランチ保護でmain以外に制限する | README原文の最小権限方針。ただし**落とし穴**: git pushにはContents: Write権限が必須（[01-research.md](01-research.md)参照）。「push可能だがmainには弾かれる」設計にするため、実際にはContents: Writeを付与し、ブランチ保護側（[05-ops-and-docs.md](05-ops-and-docs.md)）でmainへの直接pushを止める構成に修正する必要がある |
| installation tokenの`repositories`パラメータで対象リポジトリを明示的に絞る                                                                                      | GitHub Appが複数リポジトリにインストールされる将来があっても、トークン単位で対象を固定リポジトリに限定できる（[00-overview.md](00-overview.md)の「対象リポジトリ範囲」が汎用化された場合の保険にもなる）                                                                                                                   |

## `.claude/rules` 更新ポイント

このステップ自体は更新しない。GitHub App運用の注意点は[05-ops-and-docs.md](05-ops-and-docs.md)でまとめて反映する。
