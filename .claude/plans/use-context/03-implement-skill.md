# Step 3: `use-context`スキル本体の作成

> [02-implement-cli.md](02-implement-cli.md) の続き。`tools/ctx7`のCLIが利用可能であることを前提にする。

## やること

`claude-plugins/my-tools/skills/use-context/SKILL.md`を新規作成し、既存の調査メモ（[memo/00-overview.md](../../../claude-plugins/my-tools/skills/use-context/memo/00-overview.md) 〜 [03-skill-design.md](../../../claude-plugins/my-tools/skills/use-context/memo/03-skill-design.md)）の内容を土台にする。あわせて`README.md`を`ms-learn`・`tav-cli`と同じ「人間のメンテナ向け」構成に更新する。

## 読むべきファイル・実行推奨Grep

**SKILL.mdのフォーマット・フロントマターを揃えるため（優先度: 高）**

- 読む: `claude-plugins/my-tools/skills/ms-learn/SKILL.md` — frontmatterの`meta`各フィールド（`requires_repo_tools`, `requires_env`, `dependencies`, `requires_install`, `requires_hooks`, `requires_skills`, `status`, `version`）の書き方、` ```! `ブロックでの動的コンテキスト埋め込み（`mslearn --help`実行）
- 読む: `claude-plugins/my-tools/skills/tav-cli/SKILL.md` — 判断フロー（textコードブロック）の書き方、コマンド対応表、他スキルとの使い分け節の書き方
- 読む: `meta_field.yaml` — `meta`各フィールドの定義（SSOT）。新フィールドを増やさず既存フィールドで埋める（[[skill-meta-fields]]）

**本文に反映するため（優先度: 高。既に読了済みの調査結果の参照用）**

- 読む: `claude-plugins/my-tools/skills/use-context/memo/00-overview.md` — Context7利用要否判定、`ms-learn`との棲み分け方針
- 読む: `claude-plugins/my-tools/skills/use-context/memo/02-efficient-workflow.md` — 判断フロー・クエリ設計・コンテキスト分離のルール（SKILL.md本文にそのまま落とし込む）
- 読む: `claude-plugins/my-tools/skills/use-context/memo/03-skill-design.md` — frontmatter案・出力契約案・未決事項（Step1/Step2の決定で解消された項目を反映し、残っている未決事項はこのステップで確定させる）
- 読む: Step2で確定した`tools/ctx7`のサブコマンド仕様（実装済みの`--help`出力、終了コード）

**README.mdの構成を揃えるため（優先度: 中）**

- 読む: `claude-plugins/my-tools/skills/ms-learn/README.md`, `claude-plugins/my-tools/skills/tav-cli/README.md` — 「なぜこのスキルがあるか」「前提条件（重要）」「情報源と保守」の3節構成

## 触るファイル

### 新規

- `claude-plugins/my-tools/skills/use-context/SKILL.md` — スキル本体（frontmatter + エントリポイント + 判断フロー + サブコマンド対応表 + `ms-learn`との使い分け節）

### 変更

- `claude-plugins/my-tools/skills/use-context/README.md` — `ms-learn`/`tav-cli`と同様の「なぜこのスキルがあるか」「前提条件（重要）」「情報源と保守」構成に書き換え、`tools/ctx7/README.md`（セットアップ手順の一次情報）への導線を追加

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                | 理由                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SKILL.md本文はmemoの内容を要約するのではなく、判断フロー・クエリ具体化のコツ等はほぼそのまま転記する                                                                                                                | memoが既にSKILL.md向けの下書きとして書かれており（[03-skill-design.md](../../../claude-plugins/my-tools/skills/use-context/memo/03-skill-design.md)の「推奨する本文構成」）、要約による情報の劣化を避けるため |
| descriptionに「MCP経由ではなくCLI経由」である旨と、発火対象・対象外（Microsoft/Azure公式資料は`ms-learn`を優先、一般Web調査は対象外）を明記する                                                                     | 公式Context7 MCPプラグイン（`context7-mcp`）・`docs-researcher`エージェントとの二重発火を避けるため。ユーザー環境に公式プラグインが導入済みの可能性がある                                                     |
| memoの「未決事項」のうち、CLI実装方式（MCPクライアント経由 or REST直叩き）はStep1/Step2で解消済みとして反映する。それ以外（結果の出典表示ルール、品質閾値等）はこのステップで方針を確定させ、SKILL.md本文に反映する | 未決事項を放置したままSKILL.mdを完成させると、実行時の判断がエージェント任せになり挙動がぶれる                                                                                                                |

## `.claude/rules` 更新ポイント

- 更新なし。`.claude/rules/skill-meta-fields.md`は`paths: ["meta_field.yaml", "**/SKILL.md"]`で新規作成する`SKILL.md`も既にカバーしているため、新規ルールファイルは不要。
