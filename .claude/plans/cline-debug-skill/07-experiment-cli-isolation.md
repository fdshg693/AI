# Step 7(実験): Cline CLIによる分離テストの実地検証

> [06-write-otel-reference.md](06-write-otel-reference.md) の続き。このステップはドキュメント成果物を書かない。実際にCline CLIを分離実行して結果メモを残し、[08-write-testing.md](08-write-testing.md) に引き渡す。

## やること

`cline-cli-use` スキルの単発実行の基本形と、CLIヘルプにある `--data-dir <path>` / `--auto-approve` / `--json` / `--worktree` を組み合わせ、「普段使いのグローバル設定・セッション・プラグインから切り離されたテスト環境」を実際に作れるか検証する。あわせて、SDK経由の実行（`tools/cline-wrapper` の `@cline/sdk` `Agent`）で同種の検証を行った場合との違いを比較する。

## 検証観点・仮説

- `--data-dir` 分離の実効性 — `temp/` 配下の一時ディレクトリを `--data-dir` に指定して単発実行し、グローバルの `~/.cline/data/settings/`（global-settings.json / providers.json）・セッション履歴・`~/.cline/plugins/` のプラグイン・hooksが実際に読まれないことを確認する。どこまでが `--data-dir` で分離され、どこからは分離されないか（プロジェクト側の `.cline/` 配下の設定・スキルはカレントディレクトリ基準のため別問題のはず）
- 認証の取り回し — `--data-dir` を差し替えると認証情報（`secrets.json` 等）も見えなくなり、API呼び出しが失敗するか（Claude Code版Step7で同種の問題が実測されている）。失敗する場合の回避策（環境変数でのAPIキー指定等）を実地確認する。`--key` / `cline auth --apikey` は秘密情報を履歴・ログに残しやすいため使わない（`cline-cli-use` の方針どおり）
- `--auto-approve false` での読み取り専用化 — 書き込みを指示するプロンプトを投げても、実際にはファイルが作成・変更されないことを `temp/` 配下のダミーディレクトリで実地確認する（既定が `true` である点に注意）
- `--json` 出力の実際の構造 — 単発実行を `--json` 付きで行い、出力JSONの構造（メッセージ列・ツール呼び出しの表現・終了ステータス）を記録する。Step9・10で使う実データとして確保する
- `--worktree` の実際の挙動 — git worktreeに隔離して実行する機能が、リポジトリの作業ツリーを汚さないテストに使えるか。ヘルプの記載と実挙動の対応
- hub-daemonの影響 — バックグラウンドhubが常駐している環境で、`--data-dir` 分離実行がhubとどう関係するか（新たなポート競合が起きないか。`windows-known-issues.md` の EADDRINUSE 事例との関連）
- SDK経由との違い — `tools/cline-wrapper`（`@cline/sdk` の `Agent`）で同様の軽量タスクを実行した場合、グローバル設定を共有するのか、CLIの `--data-dir` 相当の分離が可能か（`CLINE_API_KEY` 等の環境変数の扱いの違い含む）

## 検証の進め方（安全な実行方法・後片付け）

- `--data-dir` には必ず `temp/` 配下の一時ディレクトリを指定し、既存の `~/.cline` には触れない
- 書き込み系の検証は `temp/` 配下のダミーディレクトリを `--cwd` に指定して行い、本番プロジェクトのファイルは一切変更させない
- API課金を伴うため、確認は軽量モデル（`cline-pass/minimax-m3`）の短い単発タスクに留め、大掛かりなコーディングタスクは実行しない
- `--worktree` の検証はコミットに影響しない範囲で行い、作成したworktreeはこのステップの最後に削除する
- 検証で作成した一時 `--data-dir` ディレクトリは、Step9・10で使う実データ（`--json` 出力等）を除いてこのステップの最後に整理する

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[08-write-testing.md](08-write-testing.md) 側から要約だけを参照する
  - 実際に確認できた分離実行の具体的なコマンド（`--data-dir` ・ `--auto-approve false` ・ `--json` ・ `--worktree` の組み合わせ）
  - `--data-dir` で分離されるもの／されないものの実測一覧、および認証エラーの有無と回避策
  - `--json` 出力の構造の要点と、Step9・10で使う実データの保存先パス
  - SDK経由とCLI分離の違いとして実際に確認できた点
  - hub-daemon絡みで観測した挙動（あれば）

## `.claude/rules` 更新ポイント

- なし
