# サンドボックス環境でのAIコーディングツール利用

AIコーディングツールは便利だが、強力な権限を与えるのは非常に危険。
しかし、権限を制限するのはなかなかコストがかかり、プロジェクト・場面によって様々に変化する。
そこで、サンドボックス環境を立ち上げて、そのなかでAIコーディングツールを動かすことで、権限を制限しつつ、便利さを享受することができる。

## 概要

サンドボックス環境に作業に必要なGithubへのアクセス権限等を最小権限で渡す。
サンドボックス内のツールは自由に使えるようにすることで、権限による危険を回避しつつ、便利さを享受することができる。
必要なAPIキー等は環境変数経由でサンドボックスに注入する、そしてそれらのAPIキーの権限を絞る。

## ラフプラン

最終的にはクラウドで動作させるが、まずはDockerを使って実現する

- Docker を立ち上げる
  - 使えるリソースを制限する（様々なライブラリがインストールされてしまうことなどを防ぐ）
- Claude Codeがインストールされる
- Githubアプリにより、最小権限が付与される（私のプライベートレポジトリのISSUE操作・ソース読み取り・PUSH・PR作成（ブランチプロテクションルールによって、mainへのプッシュを防ぐ））
- ISSUEにて、@sandboxというメンションを検知する（ポーリング形式にすることで、外部からのアクセスを遮断する）ことで、ISSUEの内容を元に作業を行う
- Claude Code CLIにBypass Permission権限をつけて（サンドボックスなので安全）作業させる
- 終わったらセッションを停止。次のISSUEが来たら、また作業を行う

## 実装後の使い方

上記ラフプランに沿って実装済み（設計方針・ファイル構成・運用注意点は[AGENTS.md](AGENTS.md)参照）。

### 前提条件（初回のみ）

1. [docs/github-app-setup.md](docs/github-app-setup.md)に沿ってGitHub Appを作成し、
   対象リポジトリにインストールする（App ID・Installation ID・秘密鍵を控える）。
2. [docs/branch-protection.md](docs/branch-protection.md)に沿って`main`ブランチ保護を
   設定する（GitHub Appによる直接pushを防ぐため。人間オーナーの直接pushは引き続き可能）。
3. Dockerイメージをビルドする。

   ```bash
   docker build -t sandbox-agent:latest -f tools/sandbox/docker/Dockerfile tools/sandbox/docker
   ```

4. `tools/sandbox/orchestrator/.env.example`を`.env`にコピーし、GitHub App認証情報・
   `ANTHROPIC_API_KEY`・`SANDBOX_IMAGE`等を埋める（各変数の意味は`.env.example`内コメント参照）。

### 起動方法

```bash
cd tools/sandbox/orchestrator
uv sync
set -a && source .env && set +a   # .envを環境変数として読み込む（python-dotenv等は未使用）
uv run python poller.py
```

常駐プロセスとして`@sandbox`メンション付きのopen issueをポーリングする
（既定60秒間隔、`SANDBOX_POLL_INTERVAL_SECONDS`で変更可）。対象ISSUEを見つけると
使い捨てDockerコンテナを起動してClaude Agent SDKに作業させ、成功時はPRを作成、
失敗時はISSUEにエラーコメントを投稿する。

### 停止方法

`Ctrl+C`でポーリングループを終了する（実行中のコンテナがあれば、そのコンテナの
処理完了・タイムアウトを待ってから終了する）。次回起動時は未処理のISSUEから再開する
（状態は`orchestrator/data/state.db`にSQLiteで永続化されているため、再起動しても
1 ISSUE = 1回までの試行制限は維持される）。

### 誤って打ち切ったISSUEを再試行させたい場合

```bash
cd tools/sandbox/orchestrator
uv run python state.py --reset <issue_number>
```
