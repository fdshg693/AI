# Step 3(実験): hooksを使ったログ仕込みの実地検証

> [02-write-logs-and-settings.md](02-write-logs-and-settings.md) の続き。このステップはドキュメント成果物を書かない。実際にテスト用hookを仕込んで発火させ、結果メモを残して [04-write-hooks-logging.md](04-write-hooks-logging.md) に引き渡す。

## やること

Clineのhooks機構（公式ドキュメントの hooks ページ、CLIの `--hooks-dir <path>` オプション、pluginが提供するhooks）を、実際に一時的なテスト用hookを仕込んで検証する。「ドキュメント通りに動くか」「Windows環境固有の詰まりポイントが実際に再現するか」「どんなテンプレートなら実用的か」を手を動かして確認し、`hooks-logging.md` に載せるテンプレートの元ネタにする。あわせて、既に実在する `~/.cline/data/logs/hooks.jsonl`（`session_shutdown` イベントが記録済みであることはプラン作成時に確認済み）の観察を通じて、hook発火がどうログに残るかの実例を把握する。

まず `cline-docs` スキルの手順（`scripts/extract_doc_section.py`）で hooks 関連ページ（`customization/hooks` 等）と、必要なら plugins ページを抽出し、hookの定義形式・イベント一覧・入出力契約の仮説を立ててから実地検証に入る。

## 検証観点・仮説

- hookの配置・定義方法 — `--hooks-dir <path>` にどんな形式のファイル（スクリプトの拡張子・実行形式・イベント名との対応付け規則）を置くとhookとして認識されるか。グローバル側（`~/.cline` 配下）に相当の既定hooksディレクトリがあるか
- 発火と入出力契約の実際 — 一時 `--hooks-dir`（`temp/` 配下）にテストhookを置き、軽量モデルの単発 `cline` 実行で実際に発火させる。hookへの入力（stdin JSONか、引数か、環境変数か）と、hookの出力・終了コードが本体の挙動（ブロック可否等）にどう影響するかを実地確認する
- ログへの記録 — hookの発火が `hooks.jsonl`（`--data-dir` を差し替えた場合はその先の対応ファイル）にどう記録されるか。既存の `session_shutdown` 記録（`ts` / `hookName` / `reason` / `sessionId` / `pid` / `source`）と同じ形式・同じファイルに混ざるか
- 利用可能なイベント種類 — ドキュメント記載のイベント一覧のうち、CLI単発実行で実際に発火させられるもの（session系・tool系・タスク系）と、TUI/拡張でないと発火しないものの切り分け
- Windows特有の挙動 — hookスクリプトの起動で `integrations/CLINE.md` の `PATH` 大文字小文字問題と同種のspawn失敗が起きないか。Pythonスクリプト・PowerShellスクリプトを直接hookとして指定した場合の成否
- plugin hooksとの関係 — `~/.cline/plugins/_installed/` の既存プラグイン（`cline-plugins/meta`）が提供するhookがある場合、テストhookの発火にどう混ざって見えるか。`--data-dir` 分離でpluginsのhookも無効化されるか

## 検証の進め方（安全な実行方法・後片付け）

- テストhookは必ず `temp/` 配下の一時 `--hooks-dir` に置く。グローバルの `~/.cline` 配下には一切hookを追加しない
- ログの追記先は `temp/` 配下の一時ファイルにし、リポジトリ内・`~/.cline` 内に検証用ログを残さない
- CLI実行は軽量モデル（`cline-pass/minimax-m3`）・短い単発プロンプトに留める。tool系イベントの発火にファイル操作が必要な場合のみ、最小限の `--auto-approve` を一時 `--data-dir` との組み合わせで検討し、本番プロジェクトのファイルは触らせない（`--cwd` を `temp/` 配下のダミーディレクトリに固定する）
- 検証が終わったら、一時 `--hooks-dir` と `--data-dir` を削除し、グローバル環境に影響が残っていないことを確認する

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[04-write-hooks-logging.md](04-write-hooks-logging.md) 側から要約だけを参照する
  - 実際に動いた最小構成のhook定義（テンプレート化できる形。配置形式・イベント名との対応付け）
  - hookへの実際の入出力（stdin/引数/環境変数のどれで何が渡ったか。貼り付けは最小限に）
  - 発火がログ（`hooks.jsonl` 等）にどう記録されたか
  - ドキュメント記載と異なった実際の挙動（あれば）
  - Windowsで実際につまずいた点・回避方法
  - 発火させられなかったイベントの一覧とその理由の推定

## `.claude/rules` 更新ポイント

- なし
