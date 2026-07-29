# Step 6(執筆+実装+検証): otel-reference.md ＋ ローカルOTel収集基盤(Docker) ＋ クエリスクリプト

> [05-experiment-otel.md](05-experiment-otel.md) の続き。Step5の検証結果メモと、`temp/otel-stack-experiment/`配下で実際に動作確認済みの設定ファイルを前提に書く。ドキュメント執筆だけでなく、Docker Compose一式とクエリスクリプトの実装・実データでの検証まで行う（Step10の「実装+実験」ステップと同じ扱い）。

## やること

1. OpenTelemetryの環境変数・メトリクス・イベント名の全量リファレンスと設定手順をまとめた `otel-reference.md` を作成する。SKILL.mdの決定表から `otel-reference.md` へのリンクを実体化する。
2. Step5で`temp/otel-stack-experiment/`配下で動作確認済みのDocker Compose構成一式を、`otel-stack/`としてスキル配下に清書・コピーする（`bearertokenauth`を使わずループバック公開のみで完結する版）。
3. `scripts/query_otel_logs.py`を実装し、`otel-stack/`のスタックを実際に起動した状態で繰り返し実行し、期待どおりログが取得できるまで調整する（Step10と同様、初版実装で終わらせず実データで反復検証する）。

## 読むべきファイル・実行推奨Grep

**このステップ自身の検証結果を反映するため（優先度: 最高）**

- 読む: [05-experiment-otel.md](05-experiment-otel.md) の「検証結果の記録方法」に実装時に追記された内容 — 実際に確認できた最小構成、Docker収集基盤の動作結果、ドキュメントとの相違点
- 読む: Step5が`temp/otel-stack-experiment/`配下に残した、実際に動いたDocker Compose構成一式

**OTel内容を転記・統合するため（優先度: 高）**

- 読む: `.claude/skills/claude-logs-investigate/otel-reference.md` — 環境変数・メトリクス名（8種）・イベント名・標準属性・組織全体配布・Agent SDKとの関係（そのまま移設・統合する）
- 読む: `.claude/skills/claude-logs-investigate/SKILL.md` の「OpenTelemetryの仕込み」節 — 有効化の必須条件、最小構成例、子プロセスへの非伝播の注意

**Docker収集基盤・クエリスクリプトの実装パターンを踏襲するため（優先度: 高）**

- 読む: `tools/infra/ai-logs/README.md` — 恒常稼働インフラの設計意図・アーキテクチャ・既知の注意点（このローカル版との違いを`README.md`で説明する際の材料にする）
- 読む: `tools/infra/ai-logs/docker/docker-compose.yml` / `otel-collector-config.yaml` / `loki-config.yaml` / `grafana/provisioning/datasources/datasources.yaml` — ローカル版の設定内容のベースパターン（`bearertokenauth`関連の記述だけ外す）
- 読む: `tools/infra/ai-logs/scripts/fetch_logs.py` — クエリスクリプトのCLI設計（`--since`/`--limit`/`--service`引数、LogQLの組み立て方、出力整形）。ローカル版はSSH+`docker exec`を使わず`http://localhost:3100`への直接HTTPアクセスに置き換える

## 触るファイル

### 新規

- `.claude/skills/claude-code-debugging/otel-reference.md` — OTel環境変数・メトリクス名・イベント名の全量 + Step5で実際に動作確認した最小構成の有効化手順
- `.claude/skills/claude-code-debugging/otel-stack/docker-compose.yml` — ローカル専用のOTel Collector + Loki + Grafana構成（ループバック公開のみ、`bearertokenauth`なし）
- `.claude/skills/claude-code-debugging/otel-stack/otel-collector-config.yaml`
- `.claude/skills/claude-code-debugging/otel-stack/loki-config.yaml`
- `.claude/skills/claude-code-debugging/otel-stack/grafana/provisioning/datasources/datasources.yaml`
- `.claude/skills/claude-code-debugging/otel-stack/.env.example` — `GRAFANA_ADMIN_PASSWORD`等、ローカル版に必要な最小限の変数のみ
- `.claude/skills/claude-code-debugging/scripts/query_otel_logs.py` — `otel-stack/.env`を読み込み、Loki HTTP APIへ直接クエリしてログを取得するCLIスクリプト

### 変更

- `.claude/skills/claude-code-debugging/SKILL.md` — 決定表の`otel-reference.md`へのリンクを実体化し、`otel-stack/`起動手順・`query_otel_logs.py`の使い方への導線を追加

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                                                                                                                                                                             | 理由                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `otel-reference.md`は`claude-logs-investigate/otel-reference.md`とほぼ同一内容になるが、独立したファイルとしてこのスキル配下にも複製する                                                                                                                                                                                                                                         | [00-overview.md](00-overview.md)のDRY非優先方針。原典側の更新に自動追従する仕組み（同期スクリプト等）は今回のスコープ外とし、将来的な内容の乖離は許容する                                   |
| 有効化手順の節は、ドキュメントの一般論だけでなくStep5で実際に動作確認した最小構成（環境変数の組み合わせ・確認方法）をそのまま載せる                                                                                                                                                                                                                                              | 「動くはず」ではなく「実際に動いた」構成を載せることで、読んだ人がすぐ試せるようにするため                                                                                                  |
| Step5で確認できなかった項目（例: 組織全体配布のmanaged settings経由の挙動）は、ドキュメント由来の情報である旨を明記した上でそのまま転記する                                                                                                                                                                                                                                      | 個人環境では検証しきれない項目があるため。実地確認済みかどうかを読み手が区別できるようにする                                                                                                |
| `otel-stack/`は`tools/infra/ai-logs/`のコピーではなく独立した構成として維持し、SKILL.md・README.md双方で「別物である」ことを明記する                                                                                                                                                                                                                                             | 恒常稼働の個人ログアーカイブとデバッグ用の使い捨てテレメトリを混在させないため（[00-overview.md](00-overview.md)決定事項）                                                                  |
| `otel-stack/.env`実体はコミットしない（`.env.example`のみコミット）。既存の`*.env`グローバルgitignoreルールで自動的に除外されることを確認する                                                                                                                                                                                                                                    | 秘匿情報をリポジトリに残さないため。動作確認時にgit statusで実際に追跡対象外になっていることを確認する                                                                                      |
| `query_otel_logs.py`は`.env`の値（Grafanaパスワード等）を読み込む処理を持つが、実際のクエリ経路はLoki直叩きのため認証情報そのものは使わない設計になる可能性がある。その場合は「なぜ`.env`を読むのか（将来Grafana API経由に変える場合の拡張性、パスワード漏洩防止の一貫した置き場所）」をスクリプトのdocstring相当ではなくこのステップ内で判断し、`otel-reference.md`側に一言残す | Step5の実地検証で「Loki直叩きに認証が不要」と判明した場合、ユーザー指摘の「.envから読み込む」という要件と実装が完全には一致しなくなるため、判断の経緯を明記して後から疑問が出ないようにする |
| `scripts/query_otel_logs.py`は抽出・出力のみを行い、`aim` CLIへの要約連携は`extract_log.py`と同様に別プロセス（パイプ/ファイル渡し）に任せる                                                                                                                                                                                                                                     | `aim-cli`スキルとの責務分離方針をOTel用クエリスクリプトにも一貫させるため                                                                                                                   |

## `.claude/rules` 更新ポイント

- なし
