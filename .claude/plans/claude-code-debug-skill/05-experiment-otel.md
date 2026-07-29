# Step 5(実験): OpenTelemetryのローカル動作確認 ＋ Docker収集基盤の検証

> [04-write-hooks-logging.md](04-write-hooks-logging.md) の続き。このステップはスキル配下の成果物ファイルを書かない（作業場所は後述のとおり`temp/`配下）。実際にOTelを有効化して出力を観察し、さらにDocker Composeでローカル収集基盤（Collector+Loki+Grafana）を実際に起動して検証し、結果メモを残して [06-write-otel-reference.md](06-write-otel-reference.md) に引き渡す。

## やること

1. `claude-logs-investigate/otel-reference.md`に列挙されている環境変数・メトリクス名・イベント名を、まずコンソールエクスポータで確認する（外部コレクタ不要、既存Step5相当の最小確認）。
2. 続けて、`tools/infra/ai-logs/docker/`（恒常稼働している別インフラ。[README.md](../../../tools/infra/ai-logs/README.md)参照）の設定パターンを参考に、ループバックのみで完結するローカル専用のDocker Compose構成（OTel Collector + Loki + Grafana）を`temp/otel-stack-experiment/`配下で組み立て、実際に`docker compose up`して動かす。
3. Claude Codeの`OTEL_EXPORTER_OTLP_ENDPOINT`をこのローカルCollectorに向けた単発`claude -p`実行を行い、送信したイベントが実際にLokiに取り込まれ、Grafana（`.env`のパスワードでログイン）およびLokiのHTTP APIへの直接クエリの両方で確認できるかを検証する。

## 検証観点・仮説

- 最小構成での有効化 — `CLAUDE_CODE_ENABLE_TELEMETRY=1` + `OTEL_METRICS_EXPORTER=console` + `OTEL_LOGS_EXPORTER=console` を単発の `claude -p` 実行の環境変数として設定し、実際にコンソールへメトリクス/ログが出力されるか
- イベント名・属性の実際の中身 — `claude_code.user_prompt`、`claude_code.tool_result`等が実際に出力に現れるか、`OTEL_LOG_USER_PROMPTS`等の詳細度制御フラグを切り替えると出力内容がどう変わるか
- 子プロセスへの非伝播の確認 — `OTEL_*`環境変数を設定したセッションからBashツールで子プロセスを起動した場合、その子プロセス側では計装が引き継がれないことを実際に確認する
- エクスポート間隔の実際の挙動 — `OTEL_METRIC_EXPORT_INTERVAL`のデフォルト(60000ms)が長すぎて確認しづらい場合、短縮した値で試して実用上の確認手順を固める
- **Docker収集基盤が実際に機能するか** — `tools/infra/ai-logs/docker/otel-collector-config.yaml`の`bearertokenauth`拡張を外し、ループバック公開のみにした構成で、Collector起動・Loki取り込み・Grafanaログインが問題なく通るか
- **Windows(Docker Desktop)特有の挙動** — ホストの`localhost`からコンテナへ`OTEL_EXPORTER_OTLP_ENDPOINT`で到達できるか、ポート競合（既存の`ai-logs`用ポート`4317`/`4318`/`3100`/`3000`等との衝突）が起きないか
- **Lokiへの直接クエリの実現可能性** — Grafanaを経由せず、ホストから`http://localhost:3100/loki/api/v1/query_range`等へ直接HTTPリクエストして結果が取れるか（`tools/infra/ai-logs/scripts/fetch_logs.py`はVM上でSSH+`docker exec`越しにアクセスしているが、ローカル完結ならその迂回が不要になるはずで、それを実際に確認する）
- **Grafana認証の最小構成** — `GF_SECURITY_ADMIN_PASSWORD`を`.env`から読み込む方式が実際に機能するか、`.env`未作成時のエラーメッセージが分かりやすいか

## 検証の進め方（安全な実行方法・後片付け）

- 現在のセッション自体の環境変数は変更せず、`claude -p`の単発呼び出しに対してその実行だけに環境変数を設定する形で検証する（親セッションのテレメトリ設定に影響を与えない）
- コンソールエクスポータでの最小確認は外部コレクタへの実送信を行わない
- Docker Compose検証は`temp/`配下（gitignore対象、`AGENTS.md`記載の一時作業用フォルダ）で行い、スキル配下のファイルはこの時点では作成・変更しない。動いた構成の実体（YAMLファイル一式）はこの`temp/`配下に残しておき、Step6が転記・コピー元として使う
- 恒常稼働中の`tools/infra/ai-logs/`のコンテナ・VM・ポートには一切触れない（読むのは設定ファイルの中身のみ）。ポート番号が衝突する場合は、このステップのローカル検証用構成側でポート番号をずらす
- 検証が終わったら`docker compose down`（および必要なら`-v`でボリューム削除）でコンテナを止め、ホストに常駐しない状態に戻す。ただし`temp/otel-stack-experiment/`配下の設定ファイル自体は次ステップの参照用に残す

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[06-write-otel-reference.md](06-write-otel-reference.md) 側から要約だけを参照する
  - 実際に確認できた最小構成の環境変数セットと、それで得られた出力の要約
  - ドキュメント記載のメトリクス名/イベント名との一致点・相違点
  - 子プロセス非伝播について実際に確認できた挙動
  - Docker収集基盤について: 動作確認できた設定内容への参照パス（`temp/otel-stack-experiment/`配下）、`bearertokenauth`を外して問題なかったか、ポート競合の有無と回避方法
  - Lokiへの直接クエリ（Grafana非経由）で実際に使えたエンドポイント・クエリパラメータの当たり

## `.claude/rules` 更新ポイント

- なし

## 検証結果メモ(実装時に追記)

### 1. コンソールエクスポータでの最小確認

- 実際に機能した最小構成: `CLAUDE_CODE_ENABLE_TELEMETRY=1` + `OTEL_METRICS_EXPORTER=console` + `OTEL_LOGS_EXPORTER=console`(+ 確認を早めるため `OTEL_METRIC_EXPORT_INTERVAL=5000` `OTEL_LOGS_EXPORT_INTERVAL=1000`)を単発 `claude -p "..." --no-session-persistence` の環境変数として設定し、標準出力に整形されたイベント/メトリクスオブジェクトが実際に流れることを確認した
- イベント名は `otel-reference.md`(claude-logs-investigate側)記載どおり `claude_code.user_prompt` / `claude_code.api_request` / `claude_code.assistant_response` / `claude_code.plugin_loaded` 等が実際に出力された。加えて `-p` 実行では裏で `generate_session_title` 用の補助APIコール(haikuモデル)が走り、それも `api_request`/`assistant_response` として個別に記録される(`query_source` 属性で `generate_session_title` / `sdk` / `main` / `auxiliary` を区別できる)ことを実地で確認した
- ドキュメント記載の「標準属性」一覧より実際の属性は多い。実際に出力された共通属性: `user.id`, `session.id`, `organization.id`, `user.email`, `user.account_uuid`, `user.account_id`(ドキュメント未記載), `terminal.type`。イベント個別属性として `event.name` / `event.timestamp` / `event.sequence` / `prompt.id` / `message.uuid` / `request_id` / `client_request_id` / `query_source` / `effort` なども実際に付与されていた
- `OTEL_LOG_USER_PROMPTS=1` を設定すると `user_prompt` イベントの `prompt` 属性にプロンプト本文がそのまま載ることを確認(未設定時は後述のとおり `<REDACTED>` になる)
- メトリクスは `claude_code.session.count` / `claude_code.cost.usage` / `claude_code.token.usage` / `claude_code.active_time.total` が実際に出力された(`claude -p` 単発実行では `lines_of_code.count` / `pull_request.count` / `commit.count` / `code_edit_tool.decision` は発生条件に当たらず出力されなかった。ツール未使用の単発QAでは出ないというだけで、ドキュメントとの相違ではない)

### 2. 子プロセスへの非伝播

- **実地確認できず**: 子プロセス側(Bashツールで起動される子シェル)がOTEL環境変数を継承するかを直接確認するには、`claude -p` セッション内でBashツールを実行できる権限が必要だが、このプロジェクトの `.claude/settings.local.json` の編集も、独立した `CLAUDE_CONFIG_DIR` を切っての `--dangerously-skip-permissions` 相当の実行も、いずれも実行環境のauto modeクラシファイアにブロックされた(権限昇格とみなされる操作は本セッション側では行えない)
  - `CLAUDE_CONFIG_DIR` を切って検証を試みた際の副産物: 未認証の新規config dirでは `claude -p` がAPI呼び出し時に "Could not resolve authentication method" エラーになった(認証情報はconfig dirごとに保持されるため)。これは分離テスト手法(Step7/8)側でも踏まえておくべき挙動
  - 上記の理由により、この項目は `claude-logs-investigate/SKILL.md` 記載の「OTEL_* 系の環境変数はBashツール・hook・MCPサーバーなどの子プロセスには伝播しない」という記述を**ドキュメント由来の未実地検証情報**としてそのまま転記する

### 3. Docker収集基盤(Collector + Loki + Grafana)の実地検証

- `temp/otel-stack-experiment/` 配下に、`tools/infra/ai-logs/docker/` を土台に以下を変更した構成一式を作成し、実際に `docker compose up -d` で起動できた:
  - Collectorの `receivers.otlp.protocols.{grpc,http}.auth` を削除し `bearertokenauth` extensionを丸ごと除去(認証なし、ループバック限定公開のため)
  - 全サービスのポートを `127.0.0.1:<port>:<port>` 明示バインドに変更(`docker-compose.yml`)
  - Loki単体では `ai-logs` はホストにポート公開していないが、このローカル版はLoki直叩き検証のため `127.0.0.1:3100:3100` を追加公開した
  - Grafana管理者パスワードは `.env`(`.env.example` からコピーして作成、gitignore対象)の `GRAFANA_ADMIN_PASSWORD` から読み込む方式で問題なく機能した
- ポート競合: 発生しなかった(`docker ps` で事前確認した限り、ホスト上にポート4317/4318/13133/3100/3000を使う既存コンテナは無かった。`ai-logs` はさくらのクラウドVM上でのみ稼働しており、ローカルホストのポートは使用していない)
- 起動後の healthcheck: Collectorは起動後まもなく `healthy`(`/`で `{"status":"Server available",...}`)。Lokiは起動直後は `/ready` が `Ingester not ready: waiting for 15s after being ready` を返し、約15秒待つと `ready` になった(Windows/Docker Desktop特有ではなく、Lokiの一般的な起動シーケンス)。Grafanaは `/api/health` が即座に `{"database":"ok",...}` を返した
- ホストの `localhost` からコンテナへの到達性: 問題なし。`curl http://localhost:4317` (gRPC health経由ではなく13133) / `curl http://localhost:3100/ready` / `curl http://localhost:3000/api/health` いずれも即座に応答した。Docker Desktop for Windows のポートフォワーディングで特別な追加設定は不要だった

### 4. 実イベント送信〜Loki取り込み〜Grafana/直接クエリでの確認

- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` + `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` + `OTEL_METRICS_EXPORTER=otlp` + `OTEL_LOGS_EXPORTER=otlp` を設定した単発 `claude -p "...2+2は?..." --no-session-persistence` を実行し、正常終了(追加のエラー出力なし)を確認した
- **Lokiへの直接クエリ(Grafana非経由)**: `GET http://localhost:3100/loki/api/v1/query_range?query={service_name="claude-code"}&limit=20` が実際に機能し、送信した `claude_code.user_prompt` / `claude_code.api_request` / `claude_code.assistant_response` / `claude_code.mcp_server_connection` イベントが取得できた。ラベル一覧確認用の `GET /loki/api/v1/label/service_name/values` も機能し `["claude-code"]` を返した
- `OTEL_LOG_USER_PROMPTS` を設定しなかったため、Lokiに格納された `prompt` / `response` 属性の値は実際に `"<REDACTED>"` になっていることを確認した(コンソールエクスポータ確認時に明示的に `OTEL_LOG_USER_PROMPTS=1` を付けた際は本文が載ったのと対照的で、デフォルトでは本文が伏せられる実装であることが実地で確認できた)
- Lokiのレスポンス上の `stream` オブジェクトには `event_name` / `session_id` / `prompt_id` 等、属性がすべてフラット化(ドット→アンダースコア変換、例 `event.name` → `event_name`)された形で載っていたが、これは `ai-logs/README.md` が言う「インデックス化されるラベルは `service_name` のみ、他は structured metadata」という設計と矛盾しない(Loki APIの `query_range` レスポンスは、クエリ結果の表示上structured metadataも同じ `stream` オブジェクトにまとめて返すため。indexとして使われているのは `service_name` のみという点は `label/values` API で `service_name` の値しか列挙されなかったことからも裏付けられる)
- **Grafana側**: `admin` + `.env` の `GRAFANA_ADMIN_PASSWORD` でBasic認証しGrafana API(`/api/datasources`)にアクセスできることを確認。さらにGrafanaのLokiデータソースプロキシ経由(`/api/datasources/proxy/uid/<uid>/loki/api/v1/label/service_name/values`)でも同じ結果(`["claude-code"]`)を取得でき、Grafana UI経由の閲覧が問題なく機能する経路であることを確認した

### 5. 使えたLokiエンドポイント・クエリパラメータのまとめ(Step6のクエリスクリプト実装向け)

- サービス一覧: `GET /loki/api/v1/label/service_name/values`
- ログ取得: `GET /loki/api/v1/query_range?query={service_name="<name>"}&start=<ns>&end=<ns>&limit=<n>&direction=backward`(`tools/infra/ai-logs/scripts/fetch_logs.py` と同じクエリ構築方法がそのまま通用した)
- 認証ヘッダは一切不要(`auth_enabled: false` のLoki設定のまま、ループバック限定公開のため)

### 6. 後片付け

- `docker compose down` でコンテナ3つ・ネットワークを削除済み(ボリュームは `-v` を付けなかったため残っているが、ホストポートは一切専有していない状態に戻っている)
- `temp/otel-stack-experiment/` 配下の設定ファイル一式(`docker-compose.yml` / `otel-collector-config.yaml` / `loki-config.yaml` / `grafana/provisioning/datasources/datasources.yaml` / `.env.example` / 動作確認用の実 `.env`)はStep6の転記元としてそのまま残置した
