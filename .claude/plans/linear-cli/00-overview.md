# Linear操作CLIラッパーツール + スキル 実装プラン - 概要

## 要件

- Linear（GraphQL API）をCLI/コードで簡単に操作できる Python ラッパーツールを `tools/linear-cli/` に作成する。`tav` コマンドと同様、単一の `linear` consoleコマンド + サブコマンドで主要操作（issue 一覧/取得/作成/更新、team/project/label 一覧、コメント、検索）を抽象化する。
- `tav-cli` スキルと同様、インストール済みの `linear` コマンドを前提とした判断フロー・使い方をまとめたスキルを `claude-plugins/my-tools/skills/linear-cli/` に作成する。
- 認証は個人APIキー（`LIN_API_KEY`）を `.env` で扱い、tav-cli / aim-ask と同じく `uv tool install --editable` でインストール前提とする。

## 実装ステップ

1. [01-research-linear-api.md](01-research-linear-api.md) — Linear GraphQL API仕様と Python 実装方式の事前調査（サードパーティ `linear` パッケージ vs 生 GraphQL httpx、スキーマ・認証・ページネーション・レート制限）
2. [02-tool-implementation.md](02-tool-implementation.md) — `tools/linear-cli/` のCLI実装（dispatcher + coreパッケージ + 各操作ラッパー）
3. [03-skill-implementation.md](03-skill-implementation.md) — `claude-plugins/my-tools/skills/linear-cli/` の SKILL.md / README.md 作成

## 主要な決定事項

| 決定                                                                                                                   | 理由                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| コマンド名は `linear`（`ln` ではない）                                                                                 | `ln` は POSIX のリンク作成コマンドと衝突する。tav-cli 同様にツール名そのままを consoleコマンドにする                                   |
| 認証は個人APIキーのみ（OAuth は扱わない）                                                                              | 個人/チーム内 CLI ツールが用途。OAuth アプリの認可フローは個人 CLI には過剰であり、tav-cli の `TAVILY_API_KEY` と同じ1キー運用に揃える |
| Python + uv（`uv tool install --editable`）で実装                                                                      | tav-cli / aim-ask / my-agents 等の既存ラッパーツール群とスタックを統一。編集時の再インストール不要                                     |
| 共通実装は `linear_core/` パッケージに集約し、各操作は薄いラッパースクリプト + `linear_cli.py` ディスパッチャ          | tav-cli の `tav_core/` + `tav_cli.py` 構成を踏襲。core に client生成/.env読込/出力/戻り値契約を持たせ、ラッパーは引数→操作に集中させる |
| 出力はデフォルト JSON to stdout（`--format table\|markdown` 切替可）                                                   | パイプ/API連携用途の既定値。tav-cli の ResultEnvelope 思想に準じ、人間向けは format 切替で賄う                                         |
| ツール本体（`tools/linear-cli/README.md`）とスキル（`claude-plugins/my-tools/skills/linear-cli/SKILL.md`）の責務を分離 | tav-cli と同じ境界。コード説明は tools 側、AI 判断フローは skills 側。スキルから Python スクリプトを直接叩かない                       |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `tools/linear-cli/`（pyproject.toml / linear_cli.py / linear_core/ / 各操作ラッパー / README.md / .env.example / tests/）
- `claude-plugins/my-tools/skills/linear-cli/`（SKILL.md / README.md）
- `.claude/rules/cli-wrapper-tools.md`

### 変更

- なし（ルールは新規作成のみ）

## `.claude/rules` 更新ポイント

- `cli-wrapper-tools.md`（Step2, 新規作成・フロントマター付き）: 外部APIラッパーCLIツールの共通規約（単一 dispatcher + coreパッケージ集約 + .env のAPIキー + JSON stdout 出力契約 + ツール/スキル責務分離）。tav-cli が既に従っている慣行を明文化し、linear-cli 以降の乖離を防ぐ

---

## 書き方のポイント

- **要件は2〜4行の箇条書きで十分。** 背景説明・動機は書かない。
- **外部API（Linear GraphQL）は実装前にWeb上の仕様を確認しないと決定事項が固まらないため、調査を独立したStep1として先に置く。** Step2 はその結果を前提に書ける（調査時の文脈を持ち込まない）。
- **決定事項は「決定」と「理由」を1行ずつ。** tav-cli/aim-ask との整合理由を明示する。
- **ファイル一覧は「新規」「変更」の2分類のみ。** 詳細な手引きは各ステップファイル側に書く。
