# Step 3: claude-plugins/my-tools/skills/linear-cli/ スキル作成

> [02-tool-implementation.md](02-tool-implementation.md) の続き。Step2 で実装した `linear` コマンドを前提としたスキルを作成する。

## やること

`tav-cli` スキルと同構成で、`linear` コマンドの判断フロー・使い方をまとめたスキルを作成する。インストール・セットアップは扱わず、インストール済みの `linear` コマンド経由を前提とする。

## 読むべきファイル・実行推奨Grep

**tav-cliスキルの構成・meta block 書き方を踏襲するため（優先度: 高）**

- 読む: `claude-plugins/my-tools/skills/tav-cli/SKILL.md` — 判断フロー・`!`動的コンテキスト埋め込み・meta block（requires_repo_tools/requires_env/requires_install）の書き方
- 読む: `claude-plugins/my-tools/skills/tav-cli/README.md` — スキルの設計意図 README の書き方
- 読む: `claude-plugins/my-tools/skills/tav-digest/SKILL.md` — 依存スキル宣言（`requires_skills`/`dependencies`）の書き方参考
- 読む: `.claude/rules/skill-meta-fields.md` — meta block の必須フィールド・許容値（version/status 等）

**aim-askスキルの CLI前提スキルの書き方を参考にするため（優先度: 中）**

- 読む: `claude-plugins/my-tools/skills/aim-ask/SKILL.md` — インストール前提・エラー時のユーザー案内の書き方

## 触るファイル

### 新規

- `claude-plugins/my-tools/skills/linear-cli/SKILL.md` — `linear` コマンドの判断フロー・サブコマンド一覧・使い方例・meta block（`requires_repo_tools: linear`, `requires_env: LIN_API_KEY`, `requires_install: uv tool install --editable tools/linear-cli`）
- `claude-plugins/my-tools/skills/linear-cli/README.md` — スキルの設計意図・前提条件の背景（人間メンテナ向け、tav-cli README.md 相当）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                        | 理由                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| SKILL.md のエントリポイントは `linear --help` を `!` で動的埋め込み                                                                         | tav-cli と同じ。サブコマンド一覧の更新漏れを防ぐ                                                   |
| meta block の `requires_repo_tools: linear` / `requires_env: LIN_API_KEY` / `requires_install: uv tool install --editable tools/linear-cli` | tav-cli SKILL.md の meta定義と同じ形式。Step2 の実装と一致させる                                   |
| スキルはインストール・セットアップを行わない                                                                                                | tav-cli/aim-ask と同じ。未インストール時は `tools/linear-cli/README.md` の手順をユーザーに案内する |

## 注意点・落とし穴

- SKILL.md の判断フローは「issue 一覧/取得/作成/更新/検索」など Step2 で確定したサブコマンドに合わせる。コマンド名・引数は実装後に `linear --help` 出力と一致させること（`!` 埋め込みで自動追随する部分と手動記述部分を混同しない）。
- meta block の `version` は既存スキルに倣って新規 `1.0.0` とする（`.claude/rules/skill-meta-fields.md` の規約に従う）。
- 新規スキルを公開カタログへ登録する場合は `tools/internal/plugin_meta`（`ai-tools.yaml` SSOT）の更新が必要。`.claude/rules/skill-publication.md` の手順に従う。本ステップではスキル本文作成までとし、カタログ登録は別途。

## `.claude/rules` 更新ポイント

- このステップでは `.claude/rules` を更新しない（共通規約は Step2 で `cli-wrapper-tools.md` に集約済み）。スキル公開・メタフィールドは既存 `skill-publication.md` / `skill-meta-fields.md` に従う。

---

## 書き方のポイント

- スキル側は CLI の判断フロー・使い方が責務。コード実装詳細は `tools/linear-cli/README.md` 側に任せ、SKILL.md に持ち込まない（tav-cli と同じ境界）。
- `!` 動的コンテキスト埋め込みで `linear --help` を取り込むことで、サブコマンド追加時の手動追記漏れを防ぐ（tav-cli SKILL.md 参照）。
- 既存ルールへの追記でパスに変更が無ければフロントマターの変更は不要（本ステップはルール更新なしなので該当せず）。
