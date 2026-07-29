# Step 11: SKILL.mdの結線 + README.md + 最終整合性確認

> [10-implement-and-verify-extract-script.md](10-implement-and-verify-extract-script.md) の続き。実験ステップは終わり、ここからは通常の仕上げ作業。

## やること

Step1〜10で作成した全ファイル（`logs-and-settings.md` / `hooks-logging.md` / `otel-reference.md` / `otel-stack/`一式 / `scripts/query_otel_logs.py` / `testing.md` / `scripts/extract_log.py`）へのリンクをSKILL.mdの決定表に反映し、リンク切れが残っていないか最終確認する。あわせて、複雑なスキルであることを踏まえたメンテナ向け `README.md` を作成する。

## 読むべきファイル・実行推奨Grep

**メンテナ向けREADME.mdの書き方の実例を確認するため（優先度: 高）**

- 読む: `.claude/skills/writing-skill/bestpractices.md` の該当箇条書き — 「判断フローや前提条件が多く本文に収まりきらない複雑なスキルは、同階層にメンテナ向けREADME.mdを併設する」の基準
- 読む: `claude-plugins/my-tools/skills/aim-cli/README.md` — 人間のメンテナ向けに設計意図・前提条件を書くREADME.mdの実例

**全体の結線漏れを確認するため（優先度: 高）**

- Grep: `\.md\)` in `.claude/skills/claude-code-debugging/SKILL.md` — SKILL.md内のMarkdownリンクを洗い出し、リンク先ファイルが実在するか一つずつ確認する

## 触るファイル

### 変更

- `.claude/skills/claude-code-debugging/SKILL.md` — 決定表の全リンクを実体化し、Step1〜10で書いた各ファイルへの導線が過不足なく揃っているか最終確認する

### 新規

- `.claude/skills/claude-code-debugging/README.md` — メンテナ向け。なぜ`claude-logs-investigate`/`claude-settings`と内容を意図的に重複させたか（DRY非優先方針の背景）、各ファイルの役割分担、実験ステップで得られた「ドキュメントと実際の挙動が食い違っていた点」があれば特記事項として記録する。あわせて`otel-stack/`が`tools/infra/ai-logs/`とは独立した別物である旨（目的の違い・設定を参考にした関係）を明記する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                            | 理由                                                                                                                   |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| DRY非優先方針の背景（なぜ意図的に重複させたか）はSKILL.md本体ではなくREADME.md側に書く                                                                          | SKILL.mdはAIが実行時に読む判断・手順に専念させ、設計意図の説明で本文を汚さないため（`bestpractices.md`の責務分離方針） |
| `CATALOG.md`はこのステップでも手動編集しない                                                                                                                    | [00-overview.md](00-overview.md)の決定事項どおり、lefthookのpre-commitフックで自動再生成される                         |
| このステップの完了をもって「新スキルの初版完成」とし、既存の`claude-logs-investigate`/`claude-settings`との今後の統合可否検討は別タスクとしてこの場では行わない | ユーザーからは新スキルの新規作成のみが依頼されており、既存スキルの統合・非推奨化は明示的にスコープ外のため             |

## `.claude/rules` 更新ポイント

- なし
