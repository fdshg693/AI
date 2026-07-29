# Claude Codeデバッグ包括スキル 実装プラン - 概要

## 要件

- `.claude/skills/claude-code-debugging/` に、Claude Code自体（CLIツール）のデバッグに関する主要な情報をほとんど同階層ファイル内に保持する、包括的なスキルを新規作成する。
- 非常に細かい一次情報（公式ドキュメント本文、CLIヘルプの正確な文言）だけは既存の `claude-code-docs` / `claude-cli-docs` スキルへの参照で済ませる。それ以外（既存ログの所在・読み方、デバッグフラグ・スラッシュコマンド、settings起因の切り分け、hookを使ったログの具体的な仕込み方、OpenTelemetry設定、テスト手法、抽出スクリプト）はこのスキル配下に直接書き切る。
- 既存の `claude-logs-investigate` ・ `claude-settings` は**作成時の参考資料としてのみ**使う。内容を要約したりそちらへ委譲したりせず、あえてDRY原則に反して新スキル側に重複して書き切る（ユーザー明示指示）。両スキル自体は変更・削除しない。
- 単なる参考ドキュメントに留めず、hookでのログ仕込み・サブエージェント/Claude CLIでのテスト・巨大ログの抽出＋`aim` CLIでの要約まで、実際に使える操作手順として書く。
- **各ドキュメント・スクリプトを執筆・実装する前に、対応する実地検証（実験）ステップを必ず独立して挟む。** hookの実際の発火結果、OTelの実際の出力、Claude CLI分離実行の実際の挙動、ログ抽出に本当に必要な機能は、書きながら/動かしながらでないと確定できない（ユーザー指摘）。実装ステップは実験ステップが残す「検証結果メモ」を前提に書き、実験の生ログ全文は実装ステップ側に持ち込まない。
- **OTel関連は単発のコンソールエクスポータ確認に留めない。** `otel-stack/`としてDocker Compose一式（OTel Collector + Loki + Grafana）をスキル配下に同梱し、いつでもテレメトリの向き先をローカルのこの基盤に切り替えて収集できるようにする。あわせて`scripts/query_otel_logs.py`を用意し、AIがGrafana等の認証情報を直接扱わなくても、同階層の`.env`をスクリプト自身が読み込む形でログを取得できるようにする（ユーザー指摘。ログの取得自体に労力をかけず解析に集中するため）。既存の恒常稼働インフラ`tools/infra/ai-logs/`とは目的が異なる別物として独立させる（詳細は決定事項表、および[05](05-experiment-otel.md)/[06](06-write-otel-reference.md)参照）。

## 実装ステップ

**既存ログ・デバッグフラグ・settings切り分け**

1. [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) — 既存ログ所在・デバッグフラグ・スラッシュコマンド・settingsスコープの実地検証
2. [02-write-logs-and-settings.md](02-write-logs-and-settings.md) — Step1の結果を踏まえて `logs-and-settings.md` + SKILL.md雛形を執筆

**hookを使ったログの仕込み方** 3. [03-experiment-hooks.md](03-experiment-hooks.md) — テスト用hookを実際に仕込み、発火・ログ出力・Windows特有の挙動を実地検証4. [04-write-hooks-logging.md](04-write-hooks-logging.md) — Step3の結果を踏まえて `hooks-logging.md` を執筆

**OpenTelemetry** 5. [05-experiment-otel.md](05-experiment-otel.md) — OTelを単発実行のコンソールエクスポータで、次いでDocker Compose製のローカル収集基盤（Collector+Loki+Grafana）で実際に有効化し、出力されるイベントが実際に集約・閲覧・クエリできるかを実地検証6. [06-write-otel-reference.md](06-write-otel-reference.md) — Step5の結果を踏まえて `otel-reference.md` を執筆し、あわせて `otel-stack/`（Docker Compose一式）と `scripts/query_otel_logs.py` を実装・実データで検証する

**テスト手法（サブエージェント／Claude CLI分離）** 7. [07-experiment-cli-isolation.md](07-experiment-cli-isolation.md) — `CLAUDE_CONFIG_DIR`分離・`--safe-mode`・`--debug-file`を実際に使い、分離テストの手順を実地検証8. [08-write-testing.md](08-write-testing.md) — Step7の結果を踏まえて `testing.md` を執筆

**ログ抽出スクリプト** 9. [09-experiment-extraction-needs.md](09-experiment-extraction-needs.md) — Step1/3/7で得た実ログを手作業で読み、抽出スクリプトに本当に必要な機能を洗い出す（Step5のOTelデータは`otel-stack/`＋専用クエリスクリプト側の担当のため対象外）10. [10-implement-and-verify-extract-script.md](10-implement-and-verify-extract-script.md) — Step9の結果を踏まえて `scripts/extract_log.py` を実装し、実データ＋`aim` CLIへの受け渡しで反復検証する

**結線** 11. [11-finalize.md](11-finalize.md) — SKILL.mdの決定表・リンクを完成させ、README.md（メンテナ向け）を書き、全体の整合性を最終確認する

## 主要な決定事項

| 決定                                                                                                                                                                                                                                                                                                   | 理由                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 新スキルは `.claude/skills/claude-code-debugging/` に新規作成し、既存の `claude-logs-investigate` ・ `claude-settings` は変更しない                                                                                                                                                                    | ユーザー指示。両スキルは参考資料としてのみ使う。統合・非推奨化・相互参照によるDRY化は今回のスコープ外                                                                                              |
| 一次情報の細部だけ `claude-code-docs` / `claude-cli-docs` への参照を残し、それ以外は全て新スキル配下のファイルに転記・保持する（DRYより網羅性を優先）                                                                                                                                                  | ユーザー要件「非常に細かい詳細はclaude-code-docsに譲りつつ、主要な情報は同階層ファイルにほとんど保持する」を満たすため                                                                             |
| SKILL.md本体は「何をしたいか→どのファイルを見るか」の決定表とポインタのみに留め、詳細本文は同階層の複数ファイルに分割する                                                                                                                                                                              | `writing-skill`の bestpractices（SKILL.md本体500行以内）を守るため                                                                                                                                 |
| 各成果物（ドキュメント/スクリプト）の執筆・実装の前に、対応する実地検証ステップを独立させて挟み、実装ステップは検証ステップが残す「検証結果メモ」だけを前提に書く                                                                                                                                      | ユーザー指摘どおり、実際にhookを仕込む・OTelを動かす・CLIを分離実行する・ログを読む、という手を動かす過程で初めて見えてくる情報（Windows特有の挙動、抽出すべき粒度）があり、事前に確定できないため |
| 実地検証は副作用（設定変更・API呼び出し・課金）を伴うため、Haikuサブエージェントへの委任は行わず、実装者自身が実行して結果を解釈する                                                                                                                                                                   | README.mdが定義する「軽量なコードベース内調査」の委任基準（設計判断を伴わない、grepで済む）に該当しない。設定変更やCLI起動を伴い、結果の解釈にも判断が必要なため                                   |
| 実地検証で行う設定変更（テスト用hookの追加等）は `.claude/settings.local.json` または一時的な `CLAUDE_CONFIG_DIR` 配下に限定し、各検証ステップの最後で必ず元の状態に戻す                                                                                                                               | プロジェクトの本番設定・hookに検証用の変更を残さないため                                                                                                                                           |
| `CATALOG.md`は手動編集しない                                                                                                                                                                                                                                                                           | `lefthook.yml`のpre-commitフックが `**/skills/**` の変更を検知して `tools/internal/generate_skills_catalog_md.py` を自動実行するため、コミット時に自動反映される                                   |
| hookのcommandハンドラーで独自スクリプトが必要な箇所は、シェルスクリプト（bash/PowerShellの生スクリプト）ではなく必ずPythonスクリプトを使い、`command`に実行ファイル（`python`）・`args`にスクリプトパス以下を配列で渡す**exec form**で呼び出す（shell formでコマンド文字列にスクリプトを埋め込まない） | ユーザー明示指示。可読性が高く、シェルのクォート/エスケープに起因するトラブルが少ない。exec formならJSON入力はstdin経由で渡るためシェルのクォート問題がそもそも発生しない（Step3で実際に検証済み） |
| OTel検証は「単発`claude -p`実行+コンソールエクスポータ」の確認だけに留めず、Docker Composeでローカル専用のOTel Collector+Loki+Grafanaを実際に起動して検証し、その構成一式を`otel-stack/`としてスキル配下に同梱する。テレメトリの向き先はいつでもこのローカル基盤に切り替えられるようにする             | ユーザー指摘。確認のたびに使い捨てのコンソール出力を読むのではなく、繰り返し使えるクエリ可能な永続基盤を用意し、ログの取得自体に労力をかけず解析に集中できるようにするため                         |
| このローカル基盤は、既に運用中の `tools/infra/ai-logs/`（さくらのクラウドVM上で恒常稼働する、複数AIツール横断の個人ログアーカイブ。README.md参照）とは独立した別物として新設する。Collector/Lokiの設定内容は`tools/infra/ai-logs/docker/`を参考にするが、共有・依存はさせない                          | `ai-logs`は実利用ログを恒常的に貯め続ける個人アーカイブが目的であり、デバッグ用の実験的なテレメトリ（スキル動作確認のノイズ）を混ぜたくない。両者は目的が異なるため独立させる                      |
| ローカル基盤はDocker Desktop上でループバック（`127.0.0.1`）にのみポートを公開し、`ai-logs`がVM公開のために使っている`bearertokenauth`拡張は導入しない。認証はGrafanaの管理者パスワードのみに絞る                                                                                                       | ネットワーク外部に一切公開しないローカル完結の用途であり、VM公開を前提にした認証機構は過剰。ユーザー指摘の「認証は最小限に」にも合致する                                                           |
| Grafana管理者パスワード等の秘匿情報は`otel-stack/.env`（`otel-stack/.env.example`をコピーして作成。リポジトリ既存の`*.env` gitignoreルールで自動的に除外される）から読み込む。docker-composeと`scripts/query_otel_logs.py`の両方がこの`.env`を参照する                                                 | ユーザー指摘どおり。AI(Claude)自身が認証情報を直接読み書きしなくてもログ取得ができるようにするため                                                                                                 |
| `scripts/query_otel_logs.py`は`tools/infra/ai-logs/scripts/fetch_logs.py`のCLI設計（`--since`/`--limit`/`--service`、LogQLの組み立て方）を参考にしつつ、SSH+`docker exec`は使わずローカルのLoki HTTP API（`http://localhost:3100`）へ直接アクセスする                                                  | ローカル完結のため、`fetch_logs.py`のようなVMへのSSHトンネル越しの間接アクセスは不要。既存スクリプトの引数設計・出力整形は実績のあるパターンとして踏襲する                                         |
| このローカル基盤ではメトリクス・トレースは対象外とし、ログ(Loki)のみを扱う                                                                                                                                                                                                                             | `ai-logs`の既存スコープ判断（ログパイプラインのみ）を踏襲し、複雑さを増やさない。将来必要になれば`otel-collector-config.yaml`にエクスポータを追加するだけで拡張できる構成にしておく                |

## 変更/新規ファイル一覧

（各ファイルを最終的にどのステップで書き上げるかは実装ステップ一覧を参照。実験ステップ自体はファイルを変更しない）

### 新規

- `.claude/skills/claude-code-debugging/SKILL.md`（Step2で雛形作成、Step11で結線完成）
- `.claude/skills/claude-code-debugging/logs-and-settings.md`（Step2）
- `.claude/skills/claude-code-debugging/hooks-logging.md`（Step4）
- `.claude/skills/claude-code-debugging/otel-reference.md`（Step6）
- `.claude/skills/claude-code-debugging/otel-stack/docker-compose.yml`（Step6）
- `.claude/skills/claude-code-debugging/otel-stack/otel-collector-config.yaml`（Step6）
- `.claude/skills/claude-code-debugging/otel-stack/loki-config.yaml`（Step6）
- `.claude/skills/claude-code-debugging/otel-stack/grafana/provisioning/datasources/datasources.yaml`（Step6）
- `.claude/skills/claude-code-debugging/otel-stack/.env.example`（Step6）
- `.claude/skills/claude-code-debugging/scripts/query_otel_logs.py`（Step6）
- `.claude/skills/claude-code-debugging/testing.md`（Step8）
- `.claude/skills/claude-code-debugging/scripts/extract_log.py`（Step10）
- `.claude/skills/claude-code-debugging/README.md`（Step11、メンテナ向け）

### 変更

- なし（`CATALOG.md`は自動生成のため対象外）

## `.claude/rules` 更新ポイント

- なし。新規スキル追加は既存の `.claude/skills` 運用規約（`writing-skill`スキルの bestpractices.md）の範囲内であり、新たなパス限定ルールを必要としない。
