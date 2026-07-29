# Clineデバッグ包括スキル 実装プラン - 概要

## 要件

- `.cline/skills/cline-debugging/` に、Cline自体（VSCode拡張およびCline CLI）のデバッグに関する主要な情報をほとんど同階層ファイル内に保持する、包括的なスキルを新規作成する。
- 非常に細かい一次情報（公式ドキュメント本文、CLIヘルプの正確な文言）だけは既存の `cline-docs` / `cline-cli-docs` スキルへの参照で済ませる。それ以外（既存ログの所在・読み方、デバッグ用フラグ・出力制御、設定起因の切り分け、hooksを使ったログの具体的な仕込み方、OpenTelemetry設定、分離テスト手法、抽出スクリプト、Windows既知問題）はこのスキル配下に直接書き切る。
- 既存の `cline-docs` / `cline-cli-docs` / `cline-cli-use` / `cline-sdk-docs` および `integrations/CLINE.md` は**作成時の参考資料としてのみ**使う。既存スキル・既存ドキュメント自体は変更・削除しない。`.claude/skills/claude-code-debugging/`（Claude Code版の先行スキル）はプラン構成・ファイル分割のテンプレートとして参照するが、内容を機械的に転記しない（Clineの実機検証結果だけを根拠に書く。Claude Codeの仕様からの類推でClineの挙動を書かない）。
- 単なる参考ドキュメントに留めず、hooksでのログ仕込み・Cline CLI分離実行・巨大ログの抽出＋`aim` CLIでの要約まで、実際に使える操作手順として書く。
- **各ドキュメント・スクリプトを執筆・実装する前に、対応する実地検証（実験）ステップを必ず独立して挟む。** hooksの実際の発火結果、OTelが個人環境で実際に有効化できるか、CLI分離実行の実際の挙動、ログ抽出に本当に必要な機能は、書きながら/動かしながらでないと確定できない。実装ステップは実験ステップが残す「検証結果メモ」を前提に書き、実験の生ログ全文は実装ステップ側に持ち込まない。
- **OTelのローカル収集基盤は新設しない。** Claude Code版スキルが既に同梱している `.claude/skills/claude-code-debugging/otel-stack/`（ローカル専用 Collector+Loki+Grafana、ループバック公開のみ）と `scripts/query_otel_logs.py` をそのまま再利用し、Clineのテレメトリの向き先をいつでもこの基盤に切り替えられるようにする（詳細は決定事項表、および[05](05-experiment-otel.md)/[06](06-write-otel-reference.md)参照）。
- Windows既知問題（`integrations/CLINE.md`に実績のある3事例＋TTY制約）は、単なる転記で終わらせず、現在の再現状態を実地確認したうえで `windows-known-issues.md` として独立ファイルにまとめる。

## 実装ステップ

**既存ログ・デバッグフラグ・設定スコープ・Windows既知問題**

1. [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) — 既存ログ所在（`~/.cline/data/`・VSCode拡張globalStorage）・デバッグ関連フラグ・設定スコープ・Windows既知問題の現状の実地検証
2. [02-write-logs-and-settings.md](02-write-logs-and-settings.md) — Step1の結果を踏まえて `logs-and-settings.md` + `windows-known-issues.md` + SKILL.md雛形を執筆

**hooksを使ったログの仕込み方** 3. [03-experiment-hooks.md](03-experiment-hooks.md) — テスト用hookを実際に仕込み、発火・入出力契約・ログ記録・Windows特有の挙動を実地検証4. [04-write-hooks-logging.md](04-write-hooks-logging.md) — Step3の結果を踏まえて `hooks-logging.md` を執筆

**OpenTelemetry** 5. [05-experiment-otel.md](05-experiment-otel.md) — ClineのOTelを単発実行で実際に有効化できるか検証し、できる場合は既存のローカル収集基盤（`.claude/skills/claude-code-debugging/otel-stack/`）へ実際に送信して、集約・クエリできるかを実地検証6. [06-write-otel-reference.md](06-write-otel-reference.md) — Step5の結果を踏まえて `otel-reference.md` を執筆（既存基盤の再利用手順を含む）

**テスト手法（Cline CLI分離／SDK）** 7. [07-experiment-cli-isolation.md](07-experiment-cli-isolation.md) — `--data-dir`分離・`--auto-approve false`・`--json`・`--worktree`を実際に使い、分離テストの手順を実地検証（SDK経由実行との違いも比較）8. [08-write-testing.md](08-write-testing.md) — Step7の結果を踏まえて `testing.md` を執筆

**ログ抽出スクリプト** 9. [09-experiment-extraction-needs.md](09-experiment-extraction-needs.md) — Step1/3/7で得た実ログ（`cline.log`/`hub-daemon.log`/`hooks.jsonl`/セッションJSON等）を手作業で読み、抽出スクリプトに本当に必要な機能を洗い出す10. [10-implement-and-verify-extract-script.md](10-implement-and-verify-extract-script.md) — Step9の結果を踏まえて `scripts/extract_log.py` を実装し、実データ＋`aim` CLIへの受け渡しで反復検証する

**結線** 11. [11-finalize.md](11-finalize.md) — SKILL.mdの決定表・リンクを完成させ、README.md（メンテナ向け）を書き、全体の整合性を最終確認する

## 主要な決定事項

| 決定                                                                                                                                                                                                                                                               | 理由                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 新スキルは `.cline/skills/cline-debugging/` に新規作成し、既存の `cline-*` スキル群は変更しない                                                                                                                                                                    | ユーザー指示。既存スキルは参考資料としてのみ使う。統合・相互参照によるDRY化は今回のスコープ外                                                                                                                                                    |
| 一次情報の細部だけ `cline-docs` / `cline-cli-docs` への参照を残し、それ以外は全て新スキル配下のファイルに転記・保持する（DRYより網羅性を優先）                                                                                                                     | Claude Code版（`claude-code-debug-skill`）と同じ方針を採る。デバッグ時に複数スキルを往復しないで済むようにするため                                                                                                                               |
| SKILL.md本体は「何をしたいか→どのファイルを見るか」の決定表とポインタのみに留め、詳細本文は同階層の複数ファイルに分割する                                                                                                                                          | `cline-skill-writer`の作法（本体は5k tokens程度に絞り、100行超のリファレンスは別ファイルへ逃がす）を守るため                                                                                                                                     |
| SKILL.md frontmatterは`meta_field.yaml`をSSOTとする`meta:`ブロック全フィールドを記入し、`version: 1.0.0`から始める                                                                                                                                                 | `.claude/rules/skill-meta-fields.md`の規約。既存`.cline/skills`の全スキルが従っている形式に合わせる                                                                                                                                              |
| 各成果物の執筆・実装の前に対応する実地検証ステップを独立させて挟み、実装ステップは検証ステップが残す「検証結果メモ」だけを前提に書く                                                                                                                               | Claude Code版で確立された型。実際にhookを仕込む・OTelを動かす・CLIを分離実行する・ログを読む過程で初めて見える情報（Windows特有の挙動、抽出すべき粒度）があり、事前に確定できないため                                                            |
| 実地検証は副作用（設定変更・API呼び出し・課金）を伴うため、Haikuサブエージェントへの委任は行わず、実装者自身が実行して結果を解釈する                                                                                                                               | `.claude/plans/README.md`が定義する「軽量なコードベース内調査」の委任基準（設計判断を伴わない、grepで済む）に該当しないため                                                                                                                      |
| 実地検証で行う変更は一時領域（`temp/`配下、`--data-dir`・`--hooks-dir`の一時差し替え）に限定し、各検証ステップの最後で必ず元の状態に戻す。`~/.cline`の本番設定とVSCode拡張のglobalStorageは読み取り中心で変更しない                                                | 日常使いのCline環境に検証用の変更を残さないため                                                                                                                                                                                                  |
| OTel収集基盤は新設せず、`.claude/skills/claude-code-debugging/otel-stack/`と`scripts/query_otel_logs.py`を再利用する。Cline専用のコピーは作らず、`.claude/skills/claude-code-debugging/`側のファイルにも一切変更を加えない                                         | 同じポート（4317/3100/3000）をループバックにbindする設計のため2系統は同時起動できず、同一マシン・同一目的の基盤を二重保守する意味もない。イベントの識別は`service_name`ラベルで行う（`query_otel_logs.py`の`--service`引数で絞り込める既存設計） |
| ClineがOTLPを実際に送出できるか（個人環境で有効化できるか）はStep5の実地検証で確定する。送出できない場合、Step6の`otel-reference.md`は「公式ドキュメント由来の未検証情報」と「検証できた範囲」を明確に分けた縮小版とし、基盤再利用手順は検証できた範囲のみ記載する | 公式ドキュメントが`enterprise-solutions/monitoring/`配下にあり、個人利用のCLI/拡張で同じ手順が使える保証がないため。実際に動かない手順を「動く」ものとして書かない                                                                               |
| Windows既知問題は`integrations/CLINE.md`の転記で終わらせず、Step1で現在の再現状態（hub-daemonポート占有の有無、pnpm storeのパッケージングバグの有無、`cline config`のTTY制約）を実地確認してから`windows-known-issues.md`に書く                                    | このプラン作成時にも`cline --help`がhub-daemonのEADDRINUSEで失敗する事象を実測しており、既知問題は現在も生きている。転記だけでは陳腐化に気づけない                                                                                               |
| 実験で使うCline CLI呼び出しは、軽量モデル（`cline-pass/minimax-m3`）の短い単発プロンプトに留め、大掛かりなコーディングタスクは実行しない                                                                                                                           | CLI呼び出しはAPI課金を伴うため。検証目的は挙動確認であり、生成物の質は問わない                                                                                                                                                                   |
| `scripts/extract_log.py`は抽出専用とし、要約は`aim` CLIへのパイプ/ファイル渡しの2段構成とする                                                                                                                                                                      | `aim-cli`スキルとの責務分離。スクリプト内でAI呼び出しを実装するとAPIキー管理等の複雑さを持ち込むため                                                                                                                                             |
| `.cline/skills/CATALOG.md`は手動編集しない                                                                                                                                                                                                                         | lefthookのpre-commitフックが`**/skills/**`の変更を検知して`tools/internal/plugin_meta/generate/generate_skills_catalog_md.py`を自動実行するため、コミット時に自動反映される                                                                      |
| `ai-tools.yaml`へのプラグイン登録（skills-site公開）は今回のスコープ外とし、公開が必要になった時点で`.claude/rules/skill-publication.md`に従って別途行う                                                                                                           | ユーザーからはスキル作成のみが依頼されており、公開範囲の判断は別タスクとするため                                                                                                                                                                 |

## 変更/新規ファイル一覧

（各ファイルを最終的にどのステップで書き上げるかは実装ステップ一覧を参照。実験ステップ自体はファイルを変更しない）

### 新規

- `.cline/skills/cline-debugging/SKILL.md`（Step2で雛形作成、Step11で結線完成）
- `.cline/skills/cline-debugging/logs-and-settings.md`（Step2）
- `.cline/skills/cline-debugging/windows-known-issues.md`（Step2）
- `.cline/skills/cline-debugging/hooks-logging.md`（Step4）
- `.cline/skills/cline-debugging/otel-reference.md`（Step6）
- `.cline/skills/cline-debugging/testing.md`（Step8）
- `.cline/skills/cline-debugging/scripts/extract_log.py`（Step10）
- `.cline/skills/cline-debugging/README.md`（Step11、メンテナ向け）

### 変更

- なし（`.cline/skills/CATALOG.md`は自動生成のため対象外。OTel基盤は再利用のみで`.claude/skills/claude-code-debugging/`側にも変更を加えない）

## `.claude/rules` 更新ポイント

- なし。新規スキル追加は既存の運用規約（`cline-skill-writer`スキル、`.claude/rules/skill-meta-fields.md`）の範囲内であり、新たなパス限定ルールを必要としない。
