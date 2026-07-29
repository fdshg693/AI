# Step 3: ローカル検索・使用量集計と定期実行

## やること

SQLiteへ保存したログをSSHなしで検索・集計できるCLIを追加し、既存のjustfileから実行できるようにする。Windowsタスクスケジューラから定期的に増分同期を起動できる登録・解除手順も整備する。

## 読むべきファイル・実行推奨Grep

**既存CLI・運用コマンドとの整合性を確認するため（優先度: 高）**

- 読む: `tools/infra/ai-logs/scripts/fetch_logs.py` — 現在の`logs` / `list-services`の出力形式と引数
- 読む: `tools/infra/ai-logs/justfile` — レシピの引数、shell設定、Terraform出力への依存
- 読む: `tools/infra/ai-logs/README.md` — 利用者向けコマンド一覧と初期構築手順

**使用量集計の正確性を確認するため（優先度: 高）**

- 読む: Step1の調査結果 — 実際に保存されるtoken、cost、event、model、sessionの属性
- Grep: `token|cost|usage|event_name|model|session_id` — 集計対象の表記揺れ・ツール差異
- 読む: `.claude/skills/claude-code-debugging/scripts/query_otel_logs.py` — 既存のログ検索・表示方法があれば再利用する

**Windows定期実行を確認するため（優先度: 中）**

- 読む: `tools/infra/ai-logs/scripts/client_env.py` — Windows向けPythonスクリプトの引数・エラー表示・パス処理
- 読む: Step1のWindows Task Scheduler調査結果 — 実行ユーザー、作業ディレクトリ、再試行条件

## 触るファイル

### 変更

- `tools/infra/ai-logs/scripts/fetch_logs.py` — ローカルDBからの期間・サービス・セッション別検索と、日次/ツール別/モデル別の使用量集計を追加
- `tools/infra/ai-logs/justfile` — 増分ダンプ、ローカルログ検索、使用量集計、タスク登録・解除のレシピを追加
- `tools/infra/ai-logs/README.md` — ローカルコマンドの使い方と定期実行設定を追記

### 新規

- `tools/infra/ai-logs/scripts/register_dump_task.ps1` — リポジトリの絶対パスを解決し、ログオン状態に依存しない同期タスクを登録
- `tools/infra/ai-logs/scripts/unregister_dump_task.ps1` — 本機能が登録したタスクだけを解除

## 決定事項・注意点／落とし穴

| 決定                                                                                   | 理由                                                                                            |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 最初のローカルUIはCLIとする                                                            | 新たなWebサーバーやGrafana構成を増やさず、SSHなしで使用量確認できる最小構成にするため           |
| 集計不能な属性は0として黙って扱わず、「未取得」として表示する                          | Claude Code / Codex CLIでイベントや属性の差があり、数値の過少集計を見逃さないため               |
| 定期実行はWindowsタスクスケジューラを標準とし、登録・解除スクリプトを冪等にする        | Windows環境でログオン後のシェルに依存せず、手動設定の漏れを減らすため                           |
| 同期処理には多重起動防止を入れる                                                       | タスクの再試行や手動実行が重なって、重複取得・SQLiteロック・不要なSSH接続が発生するのを防ぐため |
| 同期失敗はタスク履歴だけに埋めず、ローカルの同期状態と標準エラーで確認できるようにする | 「最後にいつ成功したか」をローカルから判断できる必要があるため                                  |

## `.claude/rules` 更新ポイント

- 更新なし。CLIやPowerShellの具体的な利用手順は`tools/infra/ai-logs/README.md`に記載し、一般規約はStep4で作成するルールへ集約する。
