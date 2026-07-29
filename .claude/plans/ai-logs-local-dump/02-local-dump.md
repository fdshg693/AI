# Step 2: Lokiからの増分ダンプとローカル保存

## やること

既存の`fetch_logs.py`を拡張し、Lokiから指定期間のログをページングしながら取得してSQLiteへ保存する。初回の明示的なバックフィルと、以後のチェックポイントベースの増分同期を同じ仕組みで扱う。

## 読むべきファイル・実行推奨Grep

**取得処理の拡張点を確認するため（優先度: 高）**

- 読む: `tools/infra/ai-logs/scripts/fetch_logs.py` — 既存の`run_on_vm`、query_range、サービス指定、エラー処理
- Grep: `query_range|limit|direction|start|end` — 取得境界とページング処理を追加すべき箇所
- 読む: Step1の調査結果 — Loki APIの境界条件とstructured metadataの扱い

**保存対象と集計項目を確認するため（優先度: 高）**

- 読む: `tools/infra/ai-logs/README.md` — Claude Code / Codex CLIのservice_name、event_name、session_id、modelの説明
- 読む: `.claude/skills/claude-code-debugging/otel-reference.md` — Claude Codeイベント・使用量属性の既存整理
- 読む: `.claude/skills/claude-logs-investigate/otel-reference.md` — 重複するログ属性定義があれば差分を確認

**テスト方針を確認するため（優先度: 中）**

- 読む: `tools/infra/ai-logs/scripts/verify_pipeline.sh` — 実データを発生させる既存のE2E確認方法
- 読む: `tools/infra/ai-logs/scripts/verify_client.sh` — Claude Code実データの送信確認
- Grep: `unittest|pytest|sqlite3` — リポジトリ内のPythonテスト・SQLite利用パターン

## 触るファイル

### 変更

- `tools/infra/ai-logs/scripts/fetch_logs.py` — 増分取得、SQLite初期化、チェックポイント更新、重複排除、同期エラー報告を追加

### 新規（実装時に必要と判断した場合）

- `tools/infra/ai-logs/scripts/test_fetch_logs.py` — 時刻境界、ページング、重複排除、途中失敗時のチェックポイントをテスト

## 決定事項・注意点／落とし穴

| 決定                                                                                           | 理由                                                                                     |
| ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 初回同期は期間を明示させ、無制限の全期間取得を既定にしない                                     | VM上のログ量と通信量が未知で、意図しない長時間同期を防ぐため                             |
| 同期状態はSQLite内に保存し、ログ保存と同一トランザクションで確定する                           | ログだけ保存されてチェックポイントだけ進む、またはその逆になる不整合を避けるため         |
| 前回境界に重複期間を設け、サービス・時刻・本文・ラベル等から安定した識別子を作って重複排除する | バッチ送信による遅延、同一タイムスタンプ、再実行による重複を吸収するため                 |
| ローカルには検索・集計に必要なラベル、本文、structured metadata、元タイムスタンプを保存する    | 現在の表示用整形だけを保存すると、後からevent_name・model・usageを再集計できなくなるため |
| 取得途中で失敗した場合はチェックポイントを進めない                                             | 次回実行で再取得でき、取りこぼしを安全側に倒せるため                                     |
| ローカルDBはログ本文を含む個人データとして扱い、暗号化・クラウド同期は本ステップの範囲外とする | まずはローカル利用に限定し、秘密情報を新たな外部サービスへ広げないため                   |

## `.claude/rules` 更新ポイント

- 更新なし。同期アルゴリズムの実装規約はStep4で作成する`ai-logs-local-dump.md`へ集約する。
