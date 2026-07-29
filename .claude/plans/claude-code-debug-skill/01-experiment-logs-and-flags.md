# Step 1(実験): 既存ログ・デバッグフラグ・settingsスコープの実地検証

> [00-overview.md](00-overview.md) の続き。このステップはファイルを書かない。実際にコマンドを実行し、ドキュメント記述がこの環境（Windows）で実際にどう見えるかを確認し、結果メモを残して [02-write-logs-and-settings.md](02-write-logs-and-settings.md) に引き渡す。

## やること

`claude-logs-investigate` ・ `claude-settings` に書かれている「既存ログの所在」「デバッグフラグ・スラッシュコマンド」「settingsスコープの優先順位」を、実際にこのマシン・このプロジェクトで動かして確認する。ドキュメントの記述をそのまま転記するのではなく、実際に見えたパス・出力例・相違点を検証結果メモとして残すことが、このステップの成果物になる。

## 検証観点・仮説

- `~/.claude/`配下の実ファイル — Windowsでは`%USERPROFILE%\.claude`に解決されるはず。`projects/<project>/<session-id>.jsonl`が実在し、1行1JSONの構造になっているか。`shell-snapshots/`・`session-env/`・`history.jsonl`・`debug/`が実際にどんな中身か
- デバッグフラグ — `claude -d "hooks"`や`claude --debug-file <path>`を実行したときの実際の出力形式・粒度。カテゴリフィルタ（`"api,hooks"`等）が期待通り絞り込めるか
- MCP関連 — このプロジェクトにMCPサーバー設定があるか確認した上で、`claude --debug mcp`の出力（無ければ「MCP未接続時の出力」を確認する）
- セッション内スラッシュコマンド — `/context`、`/doctor`、`/hooks`、`/status`、`/permissions`を実行し、実際の出力形式・どの設定ソース（User/Project/Local/Managed）が有効と表示されるか
- settingsスコープ — このリポジトリに実在する `.claude/settings.json` ・ `.claude/settings.local.json` ・ `~/.claude/settings.json` の内容を確認し、`/status`等で実際にどのスコープの値が優先されているかを突き合わせる

## 検証の進め方（安全な実行方法・後片付け）

- 読み取り専用の確認が中心（ファイル存在確認、既存セッションのjsonl閲覧、スラッシュコマンド実行）であり、設定変更は基本的に発生しない
- `claude --debug-file <path>`のように新規プロセスを起動する場合は、非対話の軽量な確認（`-p`での短い一発実行等）に留め、長時間の対話セッションは起動しない
- もし確認のために一時的な設定ファイルを作成した場合は、このステップの最後に削除する

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[02-write-logs-and-settings.md](02-write-logs-and-settings.md) 側から要約だけを参照する
  - ドキュメント（`claude-logs-investigate`/`claude-settings`）の記述と一致した点／相違した点
  - 実際に見えたファイルパス・出力のサンプル（貼り付けは最小限に。冗長な生ログ全文は残さない）
  - Windows特有の実際の挙動（パス解決、`%USERPROFILE%`展開等）

## `.claude/rules` 更新ポイント

- なし

## 検証結果メモ（実施済み）

検証環境: Windows 11 / Claude Code v2.1.215 / `entrypoint=cli`（VSCode拡張経由のセッションも別途並走していた）。

### `~/.claude/` 配下の実ファイル

- `%USERPROFILE%\.claude` に解決される点はドキュメント通り。トップレベルには `claude-logs-investigate` に載っていない項目も多数実在した: `backups/` `cache/` `chrome/` `file-history/` `ide/` `plugins/` `teams/` `.credentials.json` `.last-cleanup` `.last-update-result.json` `mcp-needs-auth-cache.json` `stats-cache.json`（これらは今回のスキルのスコープ外なので`logs-and-settings.md`には転記しない）
- `projects/<project>/<session-id>.jsonl` は実在。`<project>`名の変換規則はドキュメントの説明通りだが、**ドライブレターが小文字化される**（`C:\CodeRoot\AI` → `c--CodeRoot-AI`。一方で過去に別ツール経由で作られたと見られる `C--CodeRoot-AI-*` という大文字始まりの兄弟ディレクトリも同居しており、生成元によって表記揺れがある）
- `history.jsonl` は実在し、`display`/`pastedContents`/`timestamp`/`project`/`sessionId` を持つ1行1JSON。ドキュメント記載のフィールドと一致
- `sessions/<pid>.json` は実在し、現在のセッション（`pid`=`$env:CLAUDE_PID`）と一致することを確認。ドキュメント記載の`pid`/`sessionId`/`cwd`/`startedAt`/`version`/`entrypoint`/`name`に加えて、実際には`procStart`/`peerProtocol`/`kind`/`nameSource`/`status`/`updatedAt`/`statusUpdatedAt`も入っていた（未記載分は今回追記する）
- `shell-snapshots/snapshot-bash-<timestamp>-<rand>.sh` は実在し、関数定義がbase64エンコードされた`eval "$(echo '...' | base64 -d)"`形式で埋め込まれている点はドキュメント通り
- `session-env/<session-id>/` は実在するが、確認した現在セッション分は空ディレクトリだった（用途はまだ特定できず）
- **`debug/` はドキュメントの「通常は空」という記載と相違**: `--debug-file`を明示指定していない通常起動でも、`debug/<uuid>.txt`が毎回自動生成されており、起動時の`[DEBUG]`ログ（MDM設定読み込み、CA証明書、skill/plugin読み込み等）が最初から書き出されていた。少なくともこの環境・バージョンでは常時デバッグログが出力されている

### デバッグフラグ・スラッシュコマンド

- `claude --debug-file <path>` は動作確認済み。非対話1回実行（`claude -p "..." --model claude-haiku-4-5-20251001 --debug-file ./debug-test.log`）で、通常起動時の`debug/`と同じ形式の`[DEBUG]`ログがそのままファイルに書き出された
- **カテゴリフィルタ`-d "hooks"`は、ドキュメントが示唆する「hooksカテゴリのみに絞り込む」という挙動には見えなかった**: `-d "hooks"`指定でも起動処理・CA証明書・MCP接続・API送受信など無関係な`[DEBUG]`行が全172行中ほぼすべて出力され、`grep -i hook`でヒットしたのは3行（`Registered 0 hooks from 0 plugins`等）のみだった。フィルタが実際に何を絞り込んでいるのか（送信先/verbosityレベルであってカテゴリではない可能性）は今回の検証だけでは断定できず、`logs-and-settings.md`には「ドキュメント通りに絞り込まれるとは限らない」と明記するに留める
- `claude --help`で`-d, --debug [filter]` / `--debug-file <path>` / `--safe-mode` / `--disable-slash-commands`の存在を確認（文言は`claude-cli-docs`側の管轄のため転記は最小限）
- MCP: このプロジェクトに`.mcp.json`は存在せず、`~/.claude.json`にも`mcpServers`キーは無い。実際に`--debug-file`の出力に登場したMCPサーバーは`claude.ai Google Drive/Calendar/Gmail`という**アカウント紐付けのリモートMCP統合**であり、プロジェクトローカルのMCP設定ではなかった
- セッション内スラッシュコマンド（`/context` `/doctor` `/hooks` `/status` `/permissions`）はインタラクティブUIでの実行が前提のため、この実行環境（ツール呼び出し経由）からは直接実行不可。代わりに、現在有効なsettings実体を直接読み比べることで同等の裏取りを行った（次項）

### settingsスコープ

- 実在ファイル: Project `.claude\settings.json`（`enabledPlugins`のみ）、Local `.claude\settings.local.json`（`outputStyle: "default"`のみ）、User `%USERPROFILE%\.claude\settings.json`（`permissions.defaultMode: "auto"`, `model: "sonnet"`, `effortLevel: "high"`等、多数）。Managed設定ファイル（`C:\Program Files\ClaudeCode\managed-settings.json`）は未配置（debugログ上も「symlink or missing file」表示）
- `defaultMode: "auto"`が実際にUser設定側にのみ書かれており、Project/Localには存在しない ─ ドキュメントの「autoはProject/Local設定からは無視される」という制約と矛盾しない実例として確認できた
- **環境変数`CLAUDE_CODE_ENABLE_TELEMETRY=1`が既にこのセッションのプロセス環境に設定済み**であることを確認（`CLAUDECODE=1` / `CLAUDE_CODE_CHILD_SESSION=1` / `CLAUDE_CODE_ENTRYPOINT=cli` も同時に設定されていた）。OTel検証（Step5）を行う際、既にテレメトリ有効化フラグが立っている前提で影響範囲を確認する必要がある
- `~/.claude.json`はドキュメント通りOAuth・キャッシュ・プロジェクト別状態を含む巨大な構造だったが、**キーの大文字小文字違いが複数存在し、PowerShellの`ConvertFrom-Json`が素で失敗する**（`-AsHashtable`必須）。Windows特有の実務上の注意点として記録に値する

### Windows特有の挙動まとめ

- `~/.claude`→`%USERPROFILE%\.claude`解決は問題なし
- プロジェクトディレクトリ名の非英数字置換で**ドライブレターの大小文字が不安定**（生成元により`c--`/`C--`が混在）
- `~/.claude.json`をPowerShellで読む場合は大文字小文字違いキー衝突に注意（`-AsHashtable`が必要）
- Bashツールの実体は`C:\Program Files\Git\bin\bash.exe`（debugログで確認）
