# Step 1(実験): 既存ログ・デバッグフラグ・設定スコープ・Windows既知問題の実地検証

> [00-overview.md](00-overview.md) の続き。このステップはファイルを書かない。実際にコマンドを実行し、ドキュメント記述がこの環境（Windows）で実際にどう見えるかを確認し、結果メモを残して [02-write-logs-and-settings.md](02-write-logs-and-settings.md) に引き渡す。

## やること

`~/.cline/data/` および VSCode拡張のglobalStorageに実在するログ・状態ファイルの所在と中身、`cline` CLIのデバッグ関連フラグ（`--verbose` / `--json` / `--data-dir` / sessionsサブコマンド等）の実際の挙動、グローバル設定とプロジェクト設定のスコープ関係を、このマシン・このプロジェクトで実際に動かして確認する。あわせて `integrations/CLINE.md` に記録済みのWindows既知問題3事例＋TTY制約が現在も再現するかを実地確認する。ドキュメントの記述をそのまま転記するのではなく、実際に見えたパス・出力例・相違点を検証結果メモとして残すことが、このステップの成果物になる。

## 検証観点・仮説

- `~/.cline/data/` 配下の実ファイル — `logs/`（`cline.log`、`hooks.jsonl`、`hub-daemon.log` が実在することはプラン作成時に確認済み）の各ファイルのフォーマット（プレーンテキストかJSON行か、タイムスタンプ形式、ログレベル表記）と実サイズ・ローテーションの有無（特に `hub-daemon.log` は約199MBと巨大）。`sessions/<id>/<id>.json` + `<id>.messages.json` の構造（1行1JSONか、ツール呼び出しの表現方法）。`settings/`（`global-settings.json` / `providers.json` / `cli-notices.json`）、`db/`、`cache/`、`locks/`、`workspaces/`、`globalState.json` が実際にどんな中身か
- VSCode拡張側の状態 — `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\` の `tasks/<id>/`、`checkpoints/`、`state/`、`settings/`、`taskHistory.json` の中身。CLI側（`~/.cline/data/`）と拡張側で状態・ログが分かれている実態の確認（同じタスクが両方に現れるか、ID体系が共通か）
- デバッグ関連フラグ — `cline --help` の実出力で `-v, --verbose` / `--json` / `--data-dir <path>` / `--id <session-id>` / sessions・config等のサブコマンドの実際の文言を確認（`.cline/skills/cline-cli-docs/output/help_result.yaml` が一次情報だが、実コマンドで裏取りする）。`-v` 付きの軽量な単発実行で出力が実際にどう増えるか。必要なサブコマンドは `cline <subcommand> --help` で個別確認（`cline-cli-docs`スキルの手順どおり）
- 設定スコープ — `~/.cline/data/settings/global-settings.json`（グローバル）とプロジェクト側の `.cline/` 配下の設定が実際にどう読み分け・マージされるか。`cline config` が `interactive mode requires a TTY` で非対話実行不可という `integrations/CLINE.md` の記載が現在も再現するか
- Windows既知問題の現状（`integrations/CLINE.md`の3事例＋TTY制約）— 診断コマンドのみで再現確認する:
  - hub-daemonのポート25463占有: `Get-Process cline` とポートListen確認で現在の状態を記録する（このプラン作成時にも `cline --help` が EADDRINUSE で失敗する事象を実測済み）。プロセスのkillは行わない
  - `@cline/cli-windows-x64` の依存欠落（`@cline/shared` / `jiti`）: `pnpm view @cline/cli-windows-x64 dependencies` と、現在インストールされているバージョンの実際の `node_modules` 状況で、パッケージングバグが現行版でも残っているかを確認する（plugin install自体は実行しない）
  - `cline plugin install` の `PATH` 大文字小文字問題: `node -e` での環境変数名確認までに留め、installは実行しない

## 検証の進め方（安全な実行方法・後片付け）

- 読み取り専用の確認が中心（ファイル存在確認、既存ログの閲覧、ヘルプ出力の取得）。設定変更は基本的に発生させない
- `cline` の単発実行を伴う確認は、`cline-pass/minimax-m3` 相当の軽量モデル・短いプロンプト・`--auto-approve false` を付けた最小限のものに留める（API課金の抑制と副作用防止）
- `secrets.json` / `providers.json` 等の秘密情報を含みうるファイルは、**値そのものはメモに転記せず**、キーの存在・構造のみを記録する
- hub-daemonのkill・plugin install・`cline auth` の実行など副作用のある操作はこのステップでは行わない
- もし確認のために一時ファイルを作成した場合は、このステップの最後に削除する

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[02-write-logs-and-settings.md](02-write-logs-and-settings.md) 側から要約だけを参照する
  - 実際に見えたファイルパス・フォーマット・サイズの一覧（CLI側／VSCode拡張側に分けて）
  - `cline-cli-docs` のヘルプYAML・公式ドキュメントの記述と一致した点／相違した点
  - `-v` / `--json` の実際の出力の違い（貼り付けは最小限に。冗長な生ログ全文は残さない）
  - Windows既知問題3事例＋TTY制約の再現有無（再現した／しなかった、現行バージョン）
  - Step9・10で使う実データ（ログファイルのパス）の一覧

## `.claude/rules` 更新ポイント

- なし
