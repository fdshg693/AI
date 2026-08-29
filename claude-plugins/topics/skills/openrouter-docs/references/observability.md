# Observability

Source: `guides/features/input-output-logging`, `guides/features/broadcast`, `guides/features/router-metadata`

目的の異なる2つの主要機能がある。

|              | Input & Output Logging（Beta）       | Broadcast                                     |
| ------------ | ------------------------------------ | --------------------------------------------- |
| 保存先       | OpenRouter上（GCSに暗号化保存）      | 外部プラットフォーム（destination単位で設定） |
| 設定         | ワークスペース設定のトグル1つ        | destinationごとに認証情報を設定               |
| アクセス     | Logsページ（組織はadmin限定）        | 各外部ツール側                                |
| 用途         | デバッグ・応答比較・プロンプト最適化 | 本番監視・分析                                |
| プライバシー | 常にプライベート（学習等に不使用）   | destinationごとにPrivacy Mode設定可           |

## Broadcast

対応先はLangfuse, LangSmith, Datadog, Sentry, Grafana Cloud, New Relic, S3/S3互換, Snowflake, ClickHouse, PostHog, Braintrust, Comet Opik, Arize AX, W\&B Weave, OpenTelemetry Collector, Webhook, Ramp, Raindropなど（随時追加、最新リストは[Broadcast設定ページ](https://openrouter.ai/settings/observability)）。

- `trace_id`/`session_id`/`user`/`parent_span_id`等のメタデータでリクエストをグルーピングでき、`parent_span_id`で自前のOTel等トレースにネストさせることも可能
- destinationごとにAPIキーフィルタ・サンプリングレート・Privacy Modeも設定できる
- 管理はSDKの`openRouter.observability.{list,create,get,update,delete}()`（Management API Key必須）

なお「OpenRouterへのデータ利用許可（Privacy設定、全モデル1%割引）」はInput & Output Loggingとは別設定で、両者は独立に有効化できる。

## Router Metadata（リクエスト単位）

[Router Metadata](https://openrouter.ai/docs/guides/features/router-metadata)は、ワークスペース全体を継続監視するBroadcast/Loggingとは別軸で、単発リクエストのルーティング挙動をデバッグする機能。`X-OpenRouter-Metadata: enabled`ヘッダを付けるとレスポンスに`openrouter_metadata`（選ばれたprovider、フォールバック試行、ガードレール/コンテキスト圧縮/サーバーツール等のpipeline実行内容）が載る。

使い分け: 継続的な監視・分析はBroadcast/Logging、単発リクエストの「なぜこのproviderが選ばれたか」を追うにはRouter Metadata。

対応先リストや料率は変わりやすいので、断定的に答える前に上記Sourceパスを`extract_doc_section.py`で再取得して裏取りすること。
