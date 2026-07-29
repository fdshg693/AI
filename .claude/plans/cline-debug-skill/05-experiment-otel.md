# Step 5(実験): OpenTelemetryの有効化可否 ＋ 既存ローカル収集基盤への送信検証

> [04-write-hooks-logging.md](04-write-hooks-logging.md) の続き。このステップはスキル配下の成果物ファイルを書かない。実際にOTelを有効化して出力を観察し、送出できる場合は既存のローカル収集基盤への送信まで検証して、結果メモを残して [06-write-otel-reference.md](06-write-otel-reference.md) に引き渡す。

## やること

1. `cline-docs` スキルの手順で `enterprise-solutions/monitoring/opentelemetry.md` / `opentelemetry-events.md` / `opentelemetry_override.md`（環境変数）/ `telemetry.md` を抽出し、有効化に必要な環境変数・エンドポイント・イベント名の仮説を立てる。
2. 単発 `cline` 実行にその環境変数を設定し、まずローカルで完結する方法（コンソール出力・ローカルファイル等、ドキュメントが示す最小構成）で**個人環境（Cline Pass契約のCLI）で実際に有効化できるか**を確認する。公式ドキュメントが `enterprise-solutions/` 配下にあるため、そもそも有効化できるかが第一の検証観点。
3. 送出できる場合、`.claude/skills/claude-code-debugging/otel-stack/` を `docker compose up` で起動し（設定ファイルは一切変更しない）、ClineのOTLPエンドポイントをこのローカルCollector（`http://localhost:4317`）に向けて実行する。送信したイベントが実際にLokiに取り込まれ、LokiのHTTP API直接クエリ（`http://localhost:3100`）および既存の `scripts/query_otel_logs.py --service <Clineのservice名>` で取得できるかを検証する。

## 検証観点・仮説

- 有効化の可否 — ドキュメント記載の環境変数を単発 `cline` 実行に設定したとき、テレメトリが実際に初期化されて出力が始まるか。enterprise限定で個人環境では無視される／エラーになる可能性
- イベント名・属性の実際の中身 — `opentelemetry-events.md` 記載のイベントが実際に出力に現れるか。詳細度を制御するフラグ類の有無と効果
- service_nameの実値 — Lokiに取り込まれたときの `service_name` ラベルが実際に何になるか（後続のクエリの絞り込みキー。Claude Code版の `claude-code` とは別の値になるはず）
- 既存収集基盤への到達性 — ホストの `localhost` から `otel-stack` のCollectorへ到達できるか、ポート競合が起きないか（`tools/infra/ai-logs/` はVM上で稼働しておりローカルポートは使わない前提だが、`docker ps` で事前確認する）
- `query_otel_logs.py` のそのままの可用性 — 既存スクリプトの `--service` / `--since` / `--limit` が Clineのイベントにそのまま使えるか
- Cline Telemetry（`telemetry.md`、使用分析・イベントトラッキング）とOTelの違い — 両者の関係（別物か、OTelの一部か）をドキュメントと実挙動で切り分ける
- VSCode拡張側での有効化 — CLI単発実行での検証を主軸としつつ、拡張側で同じ環境変数が使えるかドキュメント上の記載有無を確認する（拡張の再起動を伴う実地検証は任意とし、できた範囲を記録する）

## 検証の進め方（安全な実行方法・後片付け）

- 現在のセッション自体の環境変数は変更せず、単発 `cline` 呼び出しに対してその実行だけに環境変数を設定する形で検証する
- CLI実行は軽量モデル（`cline-pass/minimax-m3`）・短い単発プロンプトに留める（API課金の抑制）
- `otel-stack/` の設定ファイル（docker-compose.yml・各種yaml・`.env`）は変更しない。起動・停止のみ行う。`.env` が未作成の場合は `.env.example` からコピーして作成するが、実値をメモに転記しない
- 恒常稼働中の `tools/infra/ai-logs/` のコンテナ・VM・ポートには一切触れない
- 検証が終わったら `docker compose down` でコンテナを止め、ホストに常駐しない状態に戻す

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[06-write-otel-reference.md](06-write-otel-reference.md) 側から要約だけを参照する
  - 有効化できたか否かの結論と、有効化できた場合の実際の環境変数セット
  - 実際に確認できたイベント名・属性（ドキュメントとの一致点・相違点）
  - `service_name` の実値と、Lokiへの直接クエリで実際に使えたエンドポイント・クエリパラメータ
  - `query_otel_logs.py` がそのまま使えたか、調整が必要だった点
  - 有効化できなかった場合: 判明した制約（enterprise限定等）と、その根拠となった実際の出力
  - VSCode拡張側での有効化について確認できた範囲

## `.claude/rules` 更新ポイント

- なし
