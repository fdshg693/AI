# Step 11: SKILL.mdの結線 + README.md + 最終整合性確認

> [10-implement-and-verify-extract-script.md](10-implement-and-verify-extract-script.md) の続き。実験ステップは終わり、ここからは通常の仕上げ作業。

## やること

Step1〜10で作成した全ファイル（`logs-and-settings.md` / `windows-known-issues.md` / `hooks-logging.md` / `otel-reference.md` / `testing.md` / `scripts/extract_log.py`）へのリンクをSKILL.mdの決定表に反映し、リンク切れが残っていないか最終確認する。あわせて、複雑なスキルであることを踏まえたメンテナ向け `README.md` を作成する。

## 読むべきファイル・実行推奨Grep

**メンテナ向けREADME.mdの書き方の実例を確認するため（優先度: 高）**

- 読む: `.claude/skills/claude-code-debugging/README.md` — Claude Code版のメンテナ向けREADME（DRY非優先方針の背景・各ファイルの役割分担・実験で判明した食い違いの記録）の構成。内容はこのスキル向けに書き直す

**全体の結線漏れを確認するため（優先度: 高）**

- Grep: `\.md\)` in `.cline/skills/cline-debugging/SKILL.md` — SKILL.md内のMarkdownリンクを洗い出し、リンク先ファイルが実在するか一つずつ確認する
- Grep: `cline-debugging` in `.cline/skills/CATALOG.md` — コミット前の時点ではまだ反映されていないが、pre-commitフックで自動再生成されることを最終確認する（手動編集はしない）

**frontmatterの規約適合を最終確認するため（優先度: 中）**

- 読む: `meta_field.yaml` — `meta:` ブロックの全フィールドが記入済みで、値の形式（スカラー文字列、該当なしは `none`）に適合しているか照合する

## 触るファイル

### 変更

- `.cline/skills/cline-debugging/SKILL.md` — 決定表の全リンクを実体化し、Step1〜10で書いた各ファイルへの導線が過不足なく揃っているか最終確認する

### 新規

- `.cline/skills/cline-debugging/README.md` — メンテナ向け。なぜ `cline-docs` / `cline-cli-docs` と内容を意図的に重複させたか（DRY非優先方針の背景）、各ファイルの役割分担、実験ステップで得られた「ドキュメントと実際の挙動が食い違っていた点」があれば特記事項として記録する。あわせて OTel収集基盤が `.claude/skills/claude-code-debugging/otel-stack/` の共有物である旨（再利用の関係・片方を変更するともう片方に影響すること）を明記する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                  | 理由                                                                                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| DRY非優先方針の背景（なぜ意図的に重複させたか）はSKILL.md本体ではなくREADME.md側に書く                                                                                                | SKILL.mdはAIが実行時に読む判断・手順に専念させ、設計意図の説明で本文を汚さないため                     |
| OTel収集基盤の共有関係（このスキルから参照しているが、実体は `.claude/skills/claude-code-debugging/` 側の管理）をREADME.mdに明記する                                                  | 将来どちらかのスキルを変更・削除する際に、依存関係を見落とさないため                                   |
| `.cline/skills/CATALOG.md` はこのステップでも手動編集しない                                                                                                                           | [00-overview.md](00-overview.md)の決定事項どおり、lefthookのpre-commitフックで自動再生成される         |
| このステップの完了をもって「新スキルの初版完成」とし、既存の `cline-*` スキル群との今後の統合可否検討や `ai-tools.yaml` への登録（skills-site公開）は別タスクとしてこの場では行わない | ユーザーからは新スキルの新規作成のみが依頼されており、既存スキルの統合・公開は明示的にスコープ外のため |

## `.claude/rules` 更新ポイント

- なし
