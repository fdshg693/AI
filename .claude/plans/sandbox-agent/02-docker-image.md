# Step 2: Dockerイメージ・リソース制限・組み込みネットワークサンドボックス設定

[01-research.md](01-research.md) の続き。着手前に [01-research.md](01-research.md) の「未解決・要追加検証」2点（`sandboxing`ページの非対話時挙動、SDKでの`sandbox.*`設定方法）を確認してから実装すること。

## やること

Claude Code CLI・Claude Agent SDK（Python）・git・GitHub App認証に必要な依存を含んだDockerイメージを作る。コンテナ内に「project設定として`sandbox.network.allowedDomains`等を焼き込んだ`.claude/settings.json`」を配置し、[04-orchestrator.md](04-orchestrator.md)のSDK実行時に読み込ませる。リソース制限（CPU/メモリ）は`docker run`起動時オプションとして[04-orchestrator.md](04-orchestrator.md)側に持たせるため、このステップではDockerfile側では制限しない。

## 読むべきファイル・実行推奨Grep

**Claude Code CLIの非対話実行要件を確認するため（優先度: 高）**

- 読む: `tools/claude-wrapper/CLAUDE.md`（実体は`AGENTS.md`） — Claude Agent SDKのセットアップ手順（`pip install claude-agent-sdk`、`ANTHROPIC_API_KEY`の渡し方）の既存実績
- 読む: `.claude/skills/claude-agent-sdk/SKILL.md` — `ClaudeAgentOptions`の`setting_sources`・`permission_mode`の扱い

**ネットワークサンドボックス設定の書き方を確認するため（優先度: 高）**

- 読む: `.claude/skills/claude-settings/settings.md` 67-90行目 — `sandbox.network.allowedDomains`/`deniedDomains`のJSON形式
- 実行推奨: `python .claude/skills/claude-code-docs/download_claude_code_reference.py` → `python .claude/skills/claude-code-docs/extract_doc_section.py sandboxing` で最新の`sandboxing`ページを取得し、[01-research.md](01-research.md)の未解決事項を確認する

**既存インフラのDocker構成の書き方を揃えるため（優先度: 中）**

- 読む: `tools/infra/ai-logs/docker/docker-compose.yml` / `.env.example` — このリポジトリでの環境変数受け渡し・`.env.example`の書式の前例

## 触るファイル

### 新規

- `tools/sandbox/docker/Dockerfile` — Python 3.12（Debian bookworm系）+ git + `bubblewrap`/`socat` + `claude-agent-sdk`をインストールするベースイメージ。非rootユーザーで実行する
- `tools/sandbox/docker/claude-settings/managed-settings.json` — `/etc/claude-code/managed-settings.json`としてイメージに焼き込むロックダウン設定（`sandbox.enabled`/`failIfUnavailable`/`allowUnsandboxedCommands: false`/`network.allowManagedDomainsOnly`/`network.allowedDomains`/`enableWeakerNestedSandbox`）
- `tools/sandbox/docker/claude-settings/settings.json` — 非セキュリティの利便性設定（`sandbox.filesystem.allowWrite`等）のみ。`/opt/sandbox-agent/claude-settings/settings.json`としてイメージに焼き込み、[04-orchestrator.md](04-orchestrator.md)の`run_agent.py`が読み込んで`ClaudeAgentOptions(sandbox=...)`に渡す想定（`setting_sources=[]`運用のため、Claude Codeの通常のproject設定読み込み経路では読まれない）
- `tools/sandbox/docker/.env.example` — コンテナに注入する環境変数の一覧（値は空。`ANTHROPIC_API_KEY`、GitHub App関連は[03-github-app-auth.md](03-github-app-auth.md)側の変数を参照するプレースホルダのみ）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                              | 理由                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ネットワーク許可ドメインは `api.anthropic.com`・`github.com`・`api.github.com`・`*.githubusercontent.com`・使用予定のパッケージレジストリ（`registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`）に限定する | CONSIDERATIONS.mdの結論通り、完全遮断は不可（`api.anthropic.com`必須）。ISSUE作業中にClaudeが必要とする範囲を最小限に絞る                                                                                                                                                                                                                                                                                                                                                                            |
| Dockerコンテナ自体の外部ネットワークは開放のままにし、ドメイン制御はClaude Code組み込みサンドボックスに一本化する                                                                                                 | [00-overview.md](00-overview.md)の決定事項参照。プロキシコンテナを別途構築する追加インフラコストを避ける                                                                                                                                                                                                                                                                                                                                                                                             |
| リソース制限（`--cpus`, `--memory`）はDockerfileではなく`docker run`起動オプション側（[04-orchestrator.md](04-orchestrator.md)）に持たせる                                                                        | イメージをビルドし直さずに制限値をチューニングできるようにするため                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ベースイメージは`python:3.12-slim-bookworm`（Debian）を採用。Ubuntu系は使わない                                                                                                                                   | Ubuntu 24.04+の既定AppArmorポリシーはbubblewrapのユーザー名前空間作成を制限しており、追加のホスト設定なしではサンドボックスが起動できない可能性があるため（公式`sandboxing`ページの該当セクションより）                                                                                                                                                                                                                                                                                              |
| Node.js・`@anthropic-ai/claude-code`のインストールは行わない                                                                                                                                                      | `claude-agent-sdk`（Python）はホストOS向けのネイティブClaude Codeバイナリを同梱するため別途インストール不要（出典: 公式`secure-deployment`ページ「Runtime dependencies」）。当初案の「Node.js必須」は誤りだったため撤回する                                                                                                                                                                                                                                                                          |
| `managed-settings.json`に`sandbox.enableWeakerNestedSandbox: true`を追加する                                                                                                                                      | bubblewrapは非特権コンテナ内では新しい`/proc`をマウントできず、追加のホスト権限（`--privileged`等）無しでは起動に失敗する可能性がある。このキーは「外側のコンテナが既に隔離境界を提供している」場合のための設定であり、本プロジェクトの構成（Dockerコンテナ＝外側の隔離境界＋Claude Codeサンドボックス＝内側の追加防御）に合致する（出典: 公式`sandboxing`ページのトラブルシューティング「Bubblewrap fails to start inside a container」節）。二重に隔離境界を持つ設計上のトレードオフとして採用する |
| コンテナは非rootユーザー（`sandbox-agent`）で実行する                                                                                                                                                             | `--dangerously-skip-permissions`相当のBypass Permission運用は、サンドボックスが認識されない状態でrootやsudo実行すると拒否される仕様のため（公式devcontainer構成も同様に非rootユーザーで実行）                                                                                                                                                                                                                                                                                                        |
| セキュリティ上のロックダウン（`allowManagedDomainsOnly`等）を含む設定は`managed-settings.json`にのみ書き、`settings.json`（project向け）には非セキュリティ項目のみを書く                                          | [01-research.md](01-research.md)の結論通り、`allowManagedDomainsOnly`等のbooleanキーはmanaged settingsスコープ経由でしか効かない。project設定に同じ内容を書いても無視されるため誤解を避ける                                                                                                                                                                                                                                                                                                          |
| 追加のseccompフィルタ（`@anthropic-ai/sandbox-runtime`、Unixドメインソケットのブロック強化）は今回は入れない                                                                                                      | インストールにnpm/Node.jsが必要になり、上記の「Node.js不要」判断と矛盾するため。必要になった場合は別途Node.jsを追加する判断とセットで再検討する                                                                                                                                                                                                                                                                                                                                                      |

## `.claude/rules` 更新ポイント

このステップ自体は更新しない。Dockerイメージ・ネットワーク設定の知見はまだ運用実績が無いため、[05-ops-and-docs.md](05-ops-and-docs.md)でまとめて`.claude/rules/sandbox-agent.md`に反映する。
