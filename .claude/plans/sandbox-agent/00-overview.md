# ISSUE駆動 Dockerサンドボックスエージェント 実装プラン — 概要

`tools/sandbox/README.md`（ラフプラン）と `tools/sandbox/CONSIDERATIONS.md`（検討メモ）を実装可能な単位に分解したプラン。

## 前提として確認したいこと（未回答・要確認）

計画時にユーザーへ4点確認を試みたが応答が得られなかったため、以下は**暫定の決定事項**として計画を進めている。実装着手前に本人へ確認すること。

| 項目                   | 暫定決定                                                                    | 代替案                           |
| ---------------------- | --------------------------------------------------------------------------- | -------------------------------- |
| 対象リポジトリ範囲     | このAIリポジトリ専用に固定（env設定不要）                                   | 汎用設計（複数private repo対応） |
| 実行単位               | 常駐ポーリングワーカー1プロセス + ISSUEごとに`docker run`で使い捨てコンテナ | 常駐コンテナ1つの中で完結        |
| 完了時のフィードバック | 成功時はPR作成のみ／失敗時のみISSUEにエラーコメント                         | 成功/失敗どちらもコメント返信    |

暫定決定の理由は各ステップの「決定事項」節に記載。

## 要件

- Docker上でClaude Code CLI（Claude Agent SDK経由）を動かし、GitHub ISSUEの `@sandbox` メンションをポーリングで検知して作業させる（README原文の方針）。
- GitHub Appにより最小権限（Contents読み書き・Issues読み書き・Pull requests書き込み）を付与し、ブランチ保護でmainへの直接pushを防ぐ（git pushにはContents:Write権限が必須なため、mainの保護はブランチ保護ルール側で担保する。[03-github-app-auth.md](03-github-app-auth.md)参照）。
- Claude Code自体はBypass Permissionで動かす。ただし「Bypass Permission = 安全境界ではない」ことを前提に、実際の境界はDockerコンテナ＋GitHub App最小権限＋Claude Code組み込みのネットワークサンドボックス（`sandbox.network.allowedDomains`）の三重にする（`tools/sandbox/CONSIDERATIONS.md`参照）。**ただし[01-research.md](01-research.md)で判明した通り、`bypassPermissions`下では未許可ドメインへのアクセスプロンプトが自動承認されてしまうため、project/user設定やSDKオプションでの`allowedDomains`指定だけでは防御にならない。`/etc/claude-code/managed-settings.json`をDockerイメージに焼き込み、`sandbox.network.allowManagedDomainsOnly: true` と `sandbox.allowUnsandboxedCommands: false` を併せて設定することで初めて実効性のある防御になる（詳細: [01-research.md](01-research.md)）。**
- 1 ISSUE = 1セッション（ステートレス）。`tools/claude-wrapper/todo_runner.py` の「新規セッションで完全リセットする」設計を踏襲する。
- **クラウド移行そのものは本プランのスコープ外**（ユーザー指示）。ただし将来Cloud Run Job / ECS Fargate等へ移行しやすいよう、設定は環境変数駆動・Docker Compose構成に閉じ、ホスト固有パスやWindows依存処理を持ち込まない（`tools/infra/ai-logs/` の既存方針を踏襲）。

## 実装ステップ

1. [01-research.md](01-research.md) — 外部知識の事前調査（GitHub App認証・ブランチ保護APIは調査済み、Claude Code組み込みサンドボックスの非対話時挙動が要検証）
2. [02-docker-image.md](02-docker-image.md) — Dockerイメージ・リソース制限・Claude Code組み込みネットワークサンドボックス設定
3. [03-github-app-auth.md](03-github-app-auth.md) — GitHub App作成・installation tokenの取得/更新・git認証注入
4. [04-orchestrator.md](04-orchestrator.md) — ポーリングワーカー・Claude Agent SDK実行・PR作成（Python）
5. [05-ops-and-docs.md](05-ops-and-docs.md) — ブランチ保護設定Runbook・`tools/sandbox/` ドキュメント整備・`.claude/rules` 新設

## 主要な決定事項

| 決定                                                                                                                                                                                                                           | 理由                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 起動方式はClaude Agent SDK（Python, `query()`）。CLI直叩きは採用しない                                                                                                                                                         | `tools/claude-wrapper/todo_runner.py` で検証済みの「新規セッション・resume/continue不使用」パターンをそのまま再利用でき、GitHub API呼び出し・状態管理とのオーケストレーションもPython側に統一できるため                                                                                                                                                                                                                                                                                      |
| Bypass Permissionは `ClaudeAgentOptions(permission_mode="bypassPermissions")` で明示付与する。settingsの`defaultMode`は使わない                                                                                                | CONSIDERATIONS.md記載の通り、`defaultMode`をsettingsに書くと無意識の常時バイパス化を招く。SDKでの明示付与が事故りにくい                                                                                                                                                                                                                                                                                                                                                                      |
| ネットワーク制御はDockerの外部ネットワーク自体は開放し、Claude Code組み込みの`sandbox.network.allowedDomains`（OSレベルでBashサブプロセスにも強制適用される公式機能）を第一防御とする。別途squid等のプロキシコンテナは作らない | 追加インフラ無しで、プロンプトインジェクション経由の`curl`/`wget`悪用（実際の主要な攻撃面）を公式機能で塞げる。[01-research.md](01-research.md)で判明の通り、`bypassPermissions`下では通常設定の`allowedDomains`は未許可ドメインアクセスを自動承認してしまうため無効。`/etc/claude-code/managed-settings.json`（Dockerfileで焼き込み可能なファイルパス）に`allowManagedDomainsOnly: true`と`allowUnsandboxedCommands: false`を設定することで、追加インフラ無しのまま実効性のある防御にできる |
| GitHub認証はGitHub App（installation access token）。単純PATは採用しない                                                                                                                                                       | README原文の方針。トークンは1時間で失効するため、[03-github-app-auth.md](03-github-app-auth.md)で更新ロジックを実装する                                                                                                                                                                                                                                                                                                                                                                      |
| 実行単位は常駐ワーカー1プロセス + ISSUEごとに`docker run`で使い捨てコンテナ                                                                                                                                                    | 1 ISSUE = 1コンテナで隔離を最大化しつつ、todo_runner.pyのステートレス設計思想と一致する（暫定決定、未確認）                                                                                                                                                                                                                                                                                                                                                                                  |
| 作業ディレクトリ分離は「コンテナ内でリポジトリを都度`git clone`し直す」方式とし、`git worktree`は使わない                                                                                                                      | 使い捨てコンテナ前提のためworktreeによる使い回しの恩恵が薄く、clean cloneの方が状態汚染のリスクが低い                                                                                                                                                                                                                                                                                                                                                                                        |
| クラウド移行の具体策（クラウド事業者選定・Secrets Manager統合等）は本プランでは実装しない                                                                                                                                      | ユーザー指示によりスコープ外。移行しやすさは「Docker Compose構成に閉じる」「設定は環境変数経由」という制約の遵守で担保する                                                                                                                                                                                                                                                                                                                                                                   |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `tools/sandbox/AGENTS.md` / `tools/sandbox/CLAUDE.md`
- `tools/sandbox/docker/Dockerfile`
- `tools/sandbox/docker/claude-settings/managed-settings.json`（`/etc/claude-code/managed-settings.json`としてイメージに焼き込む。`allowManagedDomainsOnly`/`allowUnsandboxedCommands`等のロックダウン専用。詳細: [01-research.md](01-research.md)）
- `tools/sandbox/docker/claude-settings/settings.json`（project設定。非セキュリティ項目のみ）
- `tools/sandbox/docker/.env.example`
- `tools/sandbox/github_app/get_installation_token.py`
- `tools/sandbox/github_app/git_credential_inject.py`
- `tools/sandbox/orchestrator/poller.py`
- `tools/sandbox/orchestrator/run_agent.py`
- `tools/sandbox/orchestrator/github_client.py`
- `tools/sandbox/orchestrator/pyproject.toml`
- `tools/sandbox/docs/branch-protection.md`
- `.claude/rules/sandbox-agent.md`

### 変更

- `tools/sandbox/README.md` — 実装後の使い方・前提条件を追記
- `README.md`（リポジトリ直下） — `tools/` 配下一覧に `sandbox/` を追記するか、[05-ops-and-docs.md](05-ops-and-docs.md) 実施時に判断

## `.claude/rules` 更新ポイント

- `.claude/rules/sandbox-agent.md`（新規、[05-ops-and-docs.md](05-ops-and-docs.md)で作成）: `tools/sandbox/**` 配下のBypass Permission運用・ネットワークサンドボックス設定の注意点
