# Step 2(執筆): SKILL.md雛形 + logs-and-settings.md

> [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) の続き。Step1の検証結果メモを前提に書く。

## やること

SKILL.mdの雛形（frontmatter + 「何をしたいかで使うものを選ぶ」決定表 + 各ファイルへのポインタ）を作成する。あわせて、Step1の実地検証結果を踏まえて、既存ログの所在・デバッグフラグ/スラッシュコマンド・settings起因の不具合切り分けをまとめた `logs-and-settings.md` を作成する。このステップの時点では `hooks-logging.md` / `otel-reference.md` / `testing.md` はまだ存在しないため、SKILL.mdの決定表からのリンクは一部プレースホルダとして残る（Step4・6・8で実体化する）。

## 読むべきファイル・実行推奨Grep

**このステップ自身の検証結果を反映するため（優先度: 最高）**

- 読む: [01-experiment-logs-and-flags.md](01-experiment-logs-and-flags.md) の「検証結果の記録方法」に実装時に追記された内容 — ドキュメントとの相違点・実際の出力サンプルを`logs-and-settings.md`に反映する

**既存の類似スキルの構成・文体を踏襲するため（優先度: 高）**

- 読む: `.claude/skills/claude-logs-investigate/SKILL.md` — 「何をしたいかで使うものを選ぶ」決定表の書き方、既存ログ所在一覧・デバッグフラグ一覧の内容そのもの（`logs-and-settings.md`への統合元）
- 読む: `.claude/skills/claude-settings/SKILL.md` と `.claude/skills/claude-settings/settings.md` — スコープ表・permissions評価順・sandbox構造・反映タイミング・チェックリストの内容そのもの（統合元）

**SKILL.mdのfrontmatter作法を確認するため（優先度: 高）**

- 読む: `.claude/skills/writing-skill/skills-reference.md` — frontmatter全フィールド（`allowed-tools`は許可であって制限ではない点、`meta.version`等）の意味
- 読む: `.claude/skills/writing-skill/bestpractices.md` — 500行制約、参照ファイルが100行超なら目次を置く、`${CLAUDE_SKILL_DIR}`でのファイル参照、frontmatterの`#`コメントで前提条件・依存関係を書く作法

**多階層スキルでの「細部だけ委譲」の実例を確認するため（優先度: 中）**

- 読む: `.claude/skills/claude-code-docs/SKILL.md` — `claude-code-docs`スキルへの参照の書き方（「詳細はこちらで確認」の実例）

## 触るファイル

### 新規

- `.claude/skills/claude-code-debugging/SKILL.md` — 決定表 + 各ファイルへの導線。frontmatterに`allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/*.py *)`を含める（Step10で作成する`extract_log.py`を先取りしてパスだけ確定させる）
- `.claude/skills/claude-code-debugging/logs-and-settings.md` — 既存ログ所在、デバッグフラグ・スラッシュコマンド一覧、settings起因の不具合切り分け。Step1で確認した実際の出力例・相違点を反映する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                   | 理由                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `logs-and-settings.md`には`claude-logs-investigate`/`claude-settings`の内容を要約せず、原典に近い粒度で転記した上で、Step1の実地検証で見つかった相違点・実例を追記する | [00-overview.md](00-overview.md)のDRY非優先方針どおり。実地検証の裏取りがあることで、原典の記述が古くなっていた場合にも気づける |
| SKILL.md本体には決定表とファイルへのポインタのみを書き、本文の詳細は`logs-and-settings.md`側に置く                                                                     | Step4〜10でさらにファイルが増えることを見越し、最初から本体を薄く保つ                                                           |
| このステップ時点でSKILL.mdから`hooks-logging.md`/`otel-reference.md`/`testing.md`へのリンクは書くが、対象ファイルは未作成のまま残る                                    | ステップ分割の都合上避けられない一時的な状態。Step11完了までリンク切れが残る点を実装者は認識しておく                            |

## `.claude/rules` 更新ポイント

- なし
