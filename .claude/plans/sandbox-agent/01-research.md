# Step 1: 外部知識の事前調査

[00-overview.md](00-overview.md) の続き。GitHub App認証・ブランチ保護API・Claude Code組み込みサンドボックスの非対話時挙動・SDKでの`sandbox.*`設定方法、いずれも本ステップで調査済み。特にサンドボックスの調査結果は[00-overview.md](00-overview.md)の要件・決定事項に修正が必要なレベルの内容だったため、本ステップ完了時に合わせて反映済み。

## やること

後続ステップ（Docker/GitHub App/オーケストレーター実装）が前提とする外部API仕様・Claude Code仕様を確定させる。このステップではコードは書かない。

## 調査結果（後続ステップから参照する）

### GitHub App installation access token（[03-github-app-auth.md](03-github-app-auth.md)向け）

- JWTでアプリ自身として認証した上で `POST /app/installations/{installation_id}/access_tokens`（`Authorization: Bearer <JWT>`）を叩くとinstallation access tokenが発行される。
- **有効期限は1時間**。`permissions`/`repositories`パラメータで、アプリに付与された権限・リポジトリ範囲よりさらに絞り込んだトークンを発行できる（未指定ならアプリの全権限を継承）。
- gitのHTTPS認証には `https://x-access-token:<TOKEN>@github.com/owner/repo.git` の形式でパスワード欄にトークンを渡す。git操作には「Contents」権限が必須。
- 参照: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

### ブランチ保護（[05-ops-and-docs.md](05-ops-and-docs.md)向け）

- `PUT /repos/{owner}/{repo}/branches/{branch}/protection` で保護ルールを設定する。
- `required_pull_request_reviews` を設定するだけで、mainブランチへの直接pushはGitHub Appのinstallation token含め技術的に阻止される（PR経由のマージのみ可能になる）。個人リポジトリでレビュワー不在の場合は `required_approving_review_count: 0` として「PR必須・承認数0」にできる。
- `enforce_admins` を`true`にすると管理者（人間オーナー）自身の直接pushも阻止される。今回はサンドボックスエージェント（GitHub App）のpushだけを止めたいので、`enforce_admins: false` を初期値とする（人間の直接pushは引き続き許可）。
- 参照: https://docs.github.com/en/rest/branches/branch-protection

### Claude Code組み込みサンドボックス（`sandbox.*`）（[02-docker-image.md](02-docker-image.md)向け）— 調査完了・重要な仕様判明

- `sandbox.network.allowedDomains`/`deniedDomains` はOSレベルでBashサブプロセス（`curl`/`wget`等）にも強制適用される公式機能。`Deny(WebFetch)`のようなツール権限ルールとは別レイヤーで、両者は併用が前提（出典: `.claude/skills/claude-code-docs/output/llms-full.txt` 106行目）。
- macOS/Linux/WSL2で有効。DockerコンテナはLinuxのため利用可能（出典: 同ファイル、`/docs/en/sandboxing` ページ抽出）。
- **解決: 非対話（bypassPermissions）時の未許可ドメイン挙動は「自動承認」であり、拒否でもハングでもない。** ネットワークは「未許可ドメインへの初回アクセス時にプロンプトが出て、承認すると以後そのセッションでは許可される」という設計だが、Changelogに明記の通り `auto` モードと `bypass-permissions` モードは**このプロンプトを自動承認する**（出典: `llms-full.txt` 6088行目「Improved auto mode and bypass-permissions mode to auto-approve sandbox network access prompts」、4782行目はこの自動承認処理がSDK/デスクトップ/IDE拡張で意図せず対話プロンプトとして出てしまっていた不具合の修正ログ）。
  - **意味すること**: `permission_mode="bypassPermissions"` で動かす本エージェントでは、project設定・user設定・SDKオプションのどれで `sandbox.network.allowedDomains` を書いても、未許可ドメインへのアクセスは拒否されず自動的に許可されてしまう。つまり**通常の設定経路では「第一防御」として機能しない**。
  - **解決策**: `sandbox.network.allowManagedDomainsOnly: true` を設定すると、未許可ドメインへのアクセスは「プロンプト→自動承認」ではなく「無条件で自動ブロック」になる（出典: `llms-full.txt` 29525行目、71315行目、6861行目「non-allowed domains are now blocked automatically with no bypass」）。**ただしこのキーは「managed settings」スコープでのみ有効**であり、project/user設定やSDKオプション（`ClaudeAgentOptions(sandbox=...)`）経由で設定しても無視される（出典: `llms-full.txt` 52718行目「Has no effect when set via SDK options」）。
  - managed settingsはエンタープライズ限定ではなく、**Linux上では `/etc/claude-code/managed-settings.json` という単なるファイルパス**であり、Dockerfileで焼き込める（出典: `llms-full.txt` 16603-16610行目。公式Dev Container向けドキュメントに `RUN mkdir -p /etc/claude-code` → `COPY managed-settings.json /etc/claude-code/managed-settings.json` の例あり）。使い捨てコンテナ・単一リポジトリ運用の本プロジェクトでは、これで十分（「リポジトリ書き込み権限があれば変更できてしまう」制約はあるが、脅威モデル上は自分自身からの改ざんを防ぐ想定ではないため許容範囲）。
- **もう1つの穴: `dangerouslyDisableSandbox` エスケープハッチ**。サンドボックス内で失敗したコマンドをClaudeが「サンドボックス外で再試行」する機能があり、これも通常は許可プロンプトを要求するが、`llms-full.txt` 61211行目に明記の通り「`permissionMode` が `bypassPermissions` かつ `allowUnsandboxedCommands` が有効なら、モデルは承認プロンプト無しで自律的にサンドボックス外実行を要求でき、事実上サイレントにサンドボックスを脱出できる」。デフォルトは `allowUnsandboxedCommands: true` なので、明示的に `false` にする必要がある（出典: 同ファイル71170行目）。このキーはmanaged-settings専用ではなく `ClaudeAgentOptions(sandbox={"allowUnsandboxedCommands": False})` でも有効だが、boolean系managedキーは「managed値が常に勝ち、ローカル設定は無視される」性質があるため（出典: 71372行目）、二重防御としてmanaged-settings.json側にも書く。
- **結論（[02-docker-image.md](02-docker-image.md)への申し送り）**: `/etc/claude-code/managed-settings.json` をDockerイメージに焼き込み、最低限以下を設定する。
  - `sandbox.enabled: true`
  - `sandbox.network.allowedDomains`: 許可ドメインリスト（GitHub API、npm/pip registry等、実際に必要なものを列挙）
  - `sandbox.network.allowManagedDomainsOnly: true`
  - `sandbox.allowUnsandboxedCommands: false`
  - `sandbox.failIfUnavailable: true`（bubblewrap等の依存不足時にサイレントに無防備実行へフォールバックするのを防ぐ。Dockerfileでbubblewrap/socatを確実にインストールすることとセット）
  - project設定（`.claude/settings.json` を`setting_sources`経由 or SDKの`ClaudeAgentOptions(sandbox=...)`）には、上記以外の非セキュリティ項目（`filesystem.allowWrite`等の利便性設定）のみを書く。

### Claude Agent SDKでの`sandbox.*`設定方法（[02-docker-image.md](02-docker-image.md) / [04-orchestrator.md](04-orchestrator.md)向け）— 調査完了

- `ClaudeAgentOptions` には `sandbox: SandboxSettings` という専用フィールドが存在する（出典: `llms-full.txt` 52663-52691行目のPython例）。`SandboxSettings`/`SandboxNetworkConfig` はTypedDictで、`enabled`・`network.allowedDomains`・`allowUnsandboxedCommands`・`failIfUnavailable`等をコードから直接渡せる。`setting_sources` でproject設定を読み込ませる方式は不要（併用も可能だが必須ではない）。
- ただし前節の通り `allowManagedDomainsOnly` は「SDKオプション経由では効果なし」と明記されているため、**セキュリティ上のロックダウンはmanaged-settings.json、それ以外の利便性設定はSDKオプション、と使い分ける**のが正しい設計。
- `setting_sources`（`todo_runner.py` は `[]` を採用）は managed settings の読み込みに一切影響しない。managed settingsは「read regardless of this option」（出典: `llms-full.txt` 42446行目）なので、`run_agent.py` 側で `setting_sources=[]` を踏襲してよい。

### `claude --bare` / 非対話実行フラグ（[02-docker-image.md](02-docker-image.md)向け、SDK採用のため優先度低）

- `--bare` はkeychain/OAuthを読まず `ANTHROPIC_API_KEY`（または`apiKeyHelper`）に限定できる（出典: `tools/sandbox/CONSIDERATIONS.md` 45-46行目）。SDK採用により直接は使わない見込みだが、コンテナ内で`claude` CLIを疎通確認する際の動作確認コマンドとして有用。

## 書き方のポイント（このステップ自体の運用メモ）

- GitHub App認証・ブランチ保護APIはWebFetchで一次情報を取得済みなので後続ステップはそのまま引用してよい。
- サンドボックス関連の調査結果は[00-overview.md](00-overview.md)の要件・決定事項の記述を上書きするレベルの内容だったため、本ステップ完了と同時に00-overview.mdも更新済み。後続ステップは本ファイルの「結論」節を前提にしてよく、調査時の試行錯誤（プロンプト自動承認 vs エスケープハッチという2つの別経路がある点等）を再度掘り下げる必要はない。
