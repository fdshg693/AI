# パターン: 外部ドキュメント調査

## 該当するタスクの例

- 「Azure Functionsの最新の書き方を調べて実装に反映して」
- 「このライブラリのv3での破壊的変更を教えて」
- 「Web上の記事を集めて要点をまとめて」

## 情報源ごとの使い分け

| 調べたい対象                                                     | 使うスキル                                                                                     |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Microsoft/Azure/.NET/M365 公式ドキュメント                       | `ms-learn`（検索・取得）。結果件数が多い/大きいファイルが複数あるときは`ms-digest`で並列AI抽出 |
| ライブラリ・フレームワークの最新API・移行ガイド（Microsoft以外） | `use-context`（Context7経由）                                                                  |
| 一般Web検索・複数URL・サイトマップ/クロール                      | `tav-cli`（本体）。既知の1URLだけなら`tav-lit`で十分。`--topic`収集後の絞り込みは`tav-digest`  |
| すでに手元にある複数ファイルへの一括質問（要約・バグ指摘等）     | `aim-ask`                                                                                      |

## 手順

1. 調べたい対象がMicrosoft公式かそれ以外かで`ms-learn`か`use-context`/`tav-cli`に分岐する。
2. 検索結果・取得結果のファイル数が多い（目安5件以上）場合は、1件ずつReadせず`ms-digest`または`tav-digest`で並列AI抽出する。
3. 結果を実装・ドキュメントに反映する。

## スキルの場所

| スキル        | パス                                                  |
| ------------- | ----------------------------------------------------- |
| `ms-learn`    | `claude-plugins/my-tools/skills/ms-learn/SKILL.md`    |
| `ms-digest`   | `claude-plugins/my-tools/skills/ms-digest/SKILL.md`   |
| `use-context` | `claude-plugins/my-tools/skills/use-context/SKILL.md` |
| `tav-cli`     | `claude-plugins/my-tools/skills/tav-cli/SKILL.md`     |
| `tav-lit`     | `claude-plugins/my-tools/skills/tav-lit/SKILL.md`     |
| `tav-digest`  | `claude-plugins/my-tools/skills/tav-digest/SKILL.md`  |
| `aim-ask`     | `claude-plugins/my-tools/skills/aim-ask/SKILL.md`     |

## この流れで足りないとき

- 上記4スキルのいずれにも当てはまらない情報源（例: 社内Wiki、特定SaaSのAPI） → `skill-search`で個別に探す。
