# AIログのローカルダンプ機能 実装プラン — 概要

## 要件

- VM上のLokiに蓄積されたClaude Code / Codex CLIのログを、ローカルへ定期的に増分ダンプできるようにする。
- ダンプ済みのログを、閲覧時のSSH接続なしでローカルから検索・集計できるようにする。
- VM側のログ保持期間を制御し、ローカルへ同期済みの古いログをVMから削除できるようにする。
- 同期失敗・重複取得・途中再実行に耐え、ログや認証情報をGitへ混入させない。

## 実装ステップ

1. [01-research.md](01-research.md) — Loki HTTP API、structured metadata、保持期間設定、Windows定期実行の事前確認
2. [02-local-dump.md](02-local-dump.md) — Lokiからの増分取得、ローカルSQLite保存、再実行・重複排除
3. [03-local-query-and-scheduling.md](03-local-query-and-scheduling.md) — ローカル検索・使用量集計、justレシピ、Windowsタスクスケジューラ連携
4. [04-retention-docs-and-verification.md](04-retention-docs-and-verification.md) — Loki保持期間、運用ドキュメント、障害時の復旧確認

## 主要な決定事項

| 決定                                                                                   | 理由                                                                                                                                  |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 同期経路は当面、既存のSSH経由でLoki APIを取得する                                      | Lokiの3100番ポートを外部公開せず、現在のセキュリティ境界を維持できる。閲覧・集計はローカルで完結するため、利用時のSSH接続は不要になる |
| ローカルの保存先はSQLiteとし、生成DBは`tools/infra/ai-logs/local-data/`に置く          | Python標準ライブラリで扱え、増分同期・重複排除・時刻/サービス別集計を追加依存なしで実装できる。生成データはGit管理外にする            |
| 取得は前回チェックポイントより少し前から再取得し、レコード単位で重複排除する           | Lokiへの遅延到着や同一ナノ秒のログによる取りこぼしを防ぐため                                                                          |
| 「使用量」は保存済みログの属性から集計する。OTelメトリクス収集の追加は別スコープとする | 現在のCollectorはlogsパイプラインのみで、Codexのメトリクスは保存していないため                                                        |
| VM側の保持期間はローカル同期の運用実績を確認してから有効化する                         | 初回同期未完了や長期停止時に、ローカルへ退避できていないログを削除しないため                                                          |

## 変更/新規ファイル一覧

### 新規

- `.claude/plans/ai-logs-local-dump/` — 本実装プラン
- `tools/infra/ai-logs/scripts/register_dump_task.ps1` — Windowsタスクスケジューラへの登録補助
- `tools/infra/ai-logs/scripts/unregister_dump_task.ps1` — 登録したタスクの解除補助
- `.claude/rules/ai-logs-local-dump.md` — Claude Codeが本基盤を変更する際の同期・データ保護ルール

### 変更

- `tools/infra/ai-logs/scripts/fetch_logs.py` — 増分ダンプ、ローカル保存、ローカル検索・集計を追加
- `tools/infra/ai-logs/justfile` — ダンプ・ローカル閲覧・タスク登録のレシピを追加
- `tools/infra/ai-logs/docker/loki-config.yaml` — 調査結果に基づく保持期間設定を追加
- `tools/infra/ai-logs/README.md` — ローカルダンプの設定、初回同期、定期実行、保持期間、復旧手順を追記
- `.gitignore` — `tools/infra/ai-logs/local-data/`を除外

## `.claude/rules` 更新ポイント

- `.claude/rules/ai-logs-local-dump.md`をStep4で新規作成する。対象パスは次のとおりとする。

```text
tools/infra/ai-logs/**
```

- 内容は、生成DB・同期状態・ログ本文をコミットしないこと、Lokiの外部公開を安易に行わないこと、保持期間変更前に同期状態を確認することに限定する。
