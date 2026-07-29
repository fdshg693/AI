# Step 6(執筆): otel-reference.md（既存収集基盤の再利用手順を含む）

> [05-experiment-otel.md](05-experiment-otel.md) の続き。Step5の検証結果メモを前提に書く。Claude Code版のStep6と異なり、Docker Compose一式やクエリスクリプトの新規実装は**行わない**（既存のものを再利用する方針。[00-overview.md](00-overview.md)決定事項）。

## やること

ClineのOpenTelemetryについて、有効化手順・環境変数・イベント名のリファレンスと、既存のローカル収集基盤（`.claude/skills/claude-code-debugging/otel-stack/` + `scripts/query_otel_logs.py`）への送信・クエリ手順をまとめた `otel-reference.md` を作成する。SKILL.mdの決定表から `otel-reference.md` へのリンクを実体化する。

## 読むべきファイル・実行推奨Grep

**このステップ自身の検証結果を反映するため（優先度: 最高）**

- 読む: [05-experiment-otel.md](05-experiment-otel.md) の「検証結果の記録方法」に実装時に追記された内容 — 有効化の可否、実際の環境変数セット、`service_name` の実値、クエリの実例

**OTel内容の一次情報を確認するため（優先度: 高）**

- 読む: Step5で `cline-docs` スキル経由で抽出した `enterprise-solutions/monitoring/` 配下の各ページのスナップショット（`output/temp/` 配下）— 環境変数・イベント名の公式記述

**収集基盤の再利用手順を正確に書くため（優先度: 高）**

- 読む: `.claude/skills/claude-code-debugging/otel-reference.md` — `otel-stack/` の起動手順・`.env` の作り方・`query_otel_logs.py` の使い方の記述（この部分は再利用手順としてほぼそのまま流用できる）
- 読む: `.claude/skills/claude-code-debugging/otel-stack/` 一式（`docker-compose.yml` / `.env.example`）— 起動手順を書くための実体参照。**読むだけで変更はしない**

## 触るファイル

### 新規

- `.cline/skills/cline-debugging/otel-reference.md` — ClineのOTel環境変数・イベント名・有効化手順（Step5で実際に確認できた範囲）+ 既存 `otel-stack/` への送信設定・起動・クエリの手順（`.claude/skills/claude-code-debugging/` へのリポジトリ相対パスで導線を書く）

### 変更

- `.cline/skills/cline-debugging/SKILL.md` — 決定表の `otel-reference.md` へのリンクを実体化

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                               | 理由                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `otel-stack/` 一式と `scripts/query_otel_logs.py` はコピーせず、`.claude/skills/claude-code-debugging/` へのパス参照で導線を書く                                                                                   | [00-overview.md](00-overview.md)決定事項どおり。同一ポートをbindする2系統は同時起動できず、二重保守も無意味なため                          |
| 有効化手順の節は、Step5で実際に動作確認した環境変数セット・確認方法をそのまま載せる。動作確認できなかった項目は「公式ドキュメント由来の未検証情報」と明記して区別する                                              | 「動くはず」ではなく「実際に動いた」構成を載せるため。enterprise配下のドキュメントであり、個人環境で使えない機能を使えるかのように書かない |
| Step5で有効化自体が確認できなかった場合は、`otel-reference.md` を「有効化の可否とその根拠」「公式ドキュメント由来の情報（未検証と明記）」「有効化できる環境が用意できた場合の収集基盤利用手順」の3節構成に縮小する | 実際に動かない手順を「動く」ものとして書かないため。条件分岐は[00-overview.md](00-overview.md)決定事項どおり                               |
| Claude CodeとClineのテレメトリが同一の収集基盤に混在しうること（`service_name` で絞り込む運用）を本文に明記する                                                                                                    | 同一Lokiに両方のイベントが入るため、絞り込みを怠ると解析時に混ざる。`query_otel_logs.py --service` の実際の使い分けを書く                  |
| `otel-stack/.env` の実値（Grafanaパスワード等）は一切書かず、`.env.example` からのコピー手順のみ記載する                                                                                                           | 秘匿情報をスキルファイルに残さないため                                                                                                     |

## `.claude/rules` 更新ポイント

- なし
