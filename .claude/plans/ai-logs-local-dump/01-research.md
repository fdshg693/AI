# Step 1: 外部仕様と実データの事前調査

## やること

実装前に、Lokiの取得API・保存データ・保持期間設定の仕様を一次情報で確認し、後続ステップが取りこぼしや重複を起こさない前提を確定する。このステップではコードを変更しない。

## 調査観点・キーワード

- `Grafana Loki HTTP API query_range` — ページング、`limit`、`direction`、時刻の境界、レスポンス形式
- `Grafana Loki structured metadata query API` — structured metadataが取得結果に含まれるか、失われる場合の代替取得方法
- `Grafana Loki retention TSDB compactor filesystem` — filesystem構成での保持期間設定、削除処理、必要なcompactor設定
- `Windows Task Scheduler PowerShell working directory` — ログオン前実行、失敗時の再試行、リポジトリ移動時の扱い
- `Claude Code OTel usage attributes` / `Codex CLI OTel logs` — 使用量集計に使えるイベント名・属性名と、現在の設定で保存される範囲

## 読むべきファイル・実行推奨Grep

**既存の取得・保存形式を確認するため（優先度: 高）**

- 読む: `tools/infra/ai-logs/scripts/fetch_logs.py` — 現在のSSH経由取得、Lokiレスポンスの解釈、時刻単位、サービス絞り込み
- 読む: `tools/infra/ai-logs/docker/loki-config.yaml` — schema、filesystemストレージ、現在の保持設定の有無
- 読む: `tools/infra/ai-logs/docker/otel-collector-config.yaml` — logsのみのパイプラインであること、Lokiへの変換経路
- Grep: `service_name|event_name|session_id|token|usage|cost|model` — 実装済みドキュメントと既存スキルにある集計可能な属性

**運用上の接続設定を確認するため（優先度: 中）**

- 読む: `tools/infra/ai-logs/justfile` — SSHキー、VM IP取得、既存のコマンド命名、PowerShell/Bashの実行境界
- 読む: `tools/infra/ai-logs/.env.example` — ローカル設定値と秘密情報の扱い
- 読む: `.gitignore` — ローカルDB・同期状態の除外方法

## 調査結果として残すもの

- 参照したGrafana / OpenAI / Anthropic等の一次情報URLと、採用するAPIパラメータ・保持設定の要約
- 実データで確認したLokiレスポンスの保持項目と、ローカルDBへ保存する項目
- 使用量集計の対象イベント・属性と、取得できない項目の明示
- Windowsタスクスケジューラの実行間隔、失敗時再試行、ロックの扱いに関する決定

## `.claude/rules` 更新ポイント

- 更新なし。調査結果は後続ステップの設計判断へ引き渡し、実装に反映した確定ルールはStep4で記録する。
