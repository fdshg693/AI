# Step 2(執筆): SKILL.md雛形 + logs-and-settings.md + windows-known-issues.md

> [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) の続き。Step1の検証結果メモを前提に書く。

## やること

SKILL.mdの雛形（frontmatter + 「何をしたいかで使うものを選ぶ」決定表 + 各ファイルへのポインタ）を作成する。あわせて、Step1の実地検証結果を踏まえて、既存ログの所在・デバッグ関連フラグ・設定起因の不具合切り分けをまとめた `logs-and-settings.md` と、Windows既知問題をまとめた `windows-known-issues.md` を作成する。このステップの時点では `hooks-logging.md` / `otel-reference.md` / `testing.md` / `scripts/extract_log.py` はまだ存在しないため、SKILL.mdの決定表からのリンクは一部プレースホルダとして残る（Step4・6・8・10で実体化する）。

## 読むべきファイル・実行推奨Grep

**このステップ自身の検証結果を反映するため（優先度: 最高）**

- 読む: [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) の「検証結果の記録方法」に実装時に追記された内容 — 実際に見えたファイル構成・フォーマット・フラグの実効性・既知問題の再現有無を各ファイルに反映する

**Clineスキルのfrontmatter・文体の作法を確認するため（優先度: 高）**

- 読む: `.cline/skills/cline-skill-writer/SKILL.md` — 作成・編集フロー（name/descriptionの決め方、本文の前倒し、補助ファイルへの逃がし方）、落とし穴、チェックリスト
- 読む: `.cline/skills/cline-skill-writer/skills-reference.md` — 配置場所・公式フィールド・補助ファイルの詳細仕様（`allowed-tools` の記法や `${CLAUDE_SKILL_DIR}` 相当の変数展開の可否はこのファイルと既存スキルの実例に従う）
- 読む: `.claude/rules/skill-meta-fields.md` と `meta_field.yaml` — `meta:`ブロックのSSOT。全フィールド（`requires_repo_tools` / `requires_env` / `dependencies` / `requires_install` / `requires_hooks` / `requires_skills` / `status` / `description` / `version`）を漏れなく記入する
- 読む: `.cline/skills/cline-cli-docs/SKILL.md` — `allowed-tools`・frontmatterコメント・バンドル済みoutputの参照という既存実例

**転記元となる内容を確認するため（優先度: 高）**

- 読む: `integrations/CLINE.md` — `windows-known-issues.md` の転記元（PATH大文字小文字問題、hub-daemon EADDRINUSE、`@cline/cli-windows-x64` パッケージングバグ、TTY制約）
- 読む: `.cline/skills/cline-cli-docs/output/help_result.yaml` — CLIフラグ・サブコマンドの正確な文言（一次情報）

**構成テンプレートを確認するため（優先度: 中。内容は転記しない）**

- 読む: `.claude/skills/claude-code-debugging/SKILL.md` — 「何をしたいかで使うものを選ぶ」決定表の書き方（構成の参考のみ。内容はClineの検証結果で新規に書く）

## 触るファイル

### 新規

- `.cline/skills/cline-debugging/SKILL.md` — 決定表 + 各ファイルへの導線。frontmatterは`meta:`ブロック全フィールド記入、`version: 1.0.0`。`allowed-tools` にStep10で作成する `scripts/extract_log.py` の呼び出しパターンを先取りして含める（記法はskills-reference.mdと既存実例に従う）
- `.cline/skills/cline-debugging/logs-and-settings.md` — 既存ログ所在（CLI側 `~/.cline/data/` とVSCode拡張側globalStorageに分けて）、デバッグ関連フラグ・出力制御の一覧、設定スコープと設定起因の不具合切り分け。Step1で確認した実際の出力例・相違点を反映する
- `.cline/skills/cline-debugging/windows-known-issues.md` — `integrations/CLINE.md` の3事例＋TTY制約を、Step1で再現確認した結果（再現した／しなかった、現行バージョン）とともに整理。診断コマンドと回避手順をセットで記載する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                | 理由                                                                                                                      |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `logs-and-settings.md` には実際に見えたパス・フォーマット・サイズをそのまま書き、`cline-docs` / `cline-cli-docs` の内容を要約転記はしない（細かい仕様の細部だけ参照リンクに留める） | [00-overview.md](00-overview.md)のDRY非優先方針どおり。一次情報の細部以外はこのスキル内で完結させる                       |
| `windows-known-issues.md` は「Step1で再現確認できたもの」と「確認できなかった／過去の記録のみのもの」を明確に区別して記載する                                                       | 実地検証と伝聞情報を混同しないため。既知問題はバージョンアップで解消されうるため、確認時点の記録が必須                    |
| `secrets.json` / `providers.json` / APIキー関連の値は一切書かず、ファイルの存在と構造（どんな種別の情報が入るか）のみ記載する                                                       | 秘密情報をスキルファイルに残さないため（`cline-docs`スキルの注意事項にも同趣旨の記載あり）                                |
| SKILL.md本体には決定表とファイルへのポインタのみを書き、本文の詳細は各ファイル側に置く                                                                                              | Step4〜10でさらにファイルが増えることを見越し、最初から本体を薄く保つ（`cline-skill-writer`の「本体は短く、参照は遅延」） |
| このステップ時点でSKILL.mdから `hooks-logging.md` / `otel-reference.md` / `testing.md` / `scripts/extract_log.py` へのリンクは書くが、対象ファイルは未作成のまま残る                | ステップ分割の都合上避けられない一時的な状態。Step11完了までリンク切れが残る点を実装者は認識しておく                      |
| ドキュメント中のパスはWindows環境でも `/`（forward slash）で書く                                                                                                                    | `cline-skill-writer`のベストプラクティス「パスは `/` で書く」に従う                                                       |

## `.claude/rules` 更新ポイント

- なし
