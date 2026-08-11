---
type: Plan Step
status: implementing-done
---

# Step 3: `linear-cli`拡張（ラベルフィルタ・ラベル付与・`show`コマンド）

> [01](01-issue-shape-and-project-config.md)で定めたラベル命名規約（`branch:<slug>`等）を実装対象にする。

## やること

`tools/linear-cli/`に以下を追加する。

- `search`に`--label <name>`（ラベル名で絞り込み。ID解決不要）
- `create`に`--label <name>`（複数指定可。issue作成時にラベルを付与）
- `update`に`--add-label <name>` / `--remove-label <name>`（複数指定可。optional機能・優先度低）
- 新規サブコマンド`show <identifier>` — 指定issueの`description`/`labels`/`status`/`assignee`/`project`/`url`を返す

## 読むべきファイル・実行推奨Grep

**既存の実装パターンを踏襲するため（優先度: 高）**

- 読む: `tools/linear-cli/src/search.mjs` — `state`/`title`をfilterへ**名前のまま**渡す既存パターン（`--label`もID解決せず同じ形で渡せる）
- 読む: `tools/linear-cli/src/update.mjs` — ワークフロー状態名をteamスコープで`client.workflowStates`から解決してIDに変換する既存パターン（ラベルも同様に`client.issueLabels`でteamスコープ解決する）
- 読む: `tools/linear-cli/src/comment.mjs` — 単一issueに対する専用コマンド（`comments`/`comment-delete`）の設計。`show`もこれに倣い「単一issue専用の詳細取得コマンド」として独立させる

**cli.mjsへの組み込み方を確認するため（優先度: 中）**

- 読む: `tools/linear-cli/src/cli.mjs` — サブコマンドディスパッチ・`parseArgs`オプション定義の追加パターン、`multiple: true`相当の繰り返し指定オプションの有無

## 触るファイル

### 新規

- `tools/linear-cli/src/show.mjs` — `getIssue(client, identifier)`：description/labels/status/assignee/project/urlを返す

### 変更

- `tools/linear-cli/src/search.mjs` — `label`パラメータ追加（`filter.labels = { name: { eq: label } }`）
- `tools/linear-cli/src/create.mjs` — `labels`パラメータ追加（team-scopedで`client.issueLabels`から名前→ID解決し`labelIds`として渡す）
- `tools/linear-cli/src/update.mjs` — `addLabels`/`removeLabels`パラメータ追加（現在の`issue.labels()`を読み、追加・削除後の集合を計算して`labelIds`として送るread-modify-write方式）
- `tools/linear-cli/src/cli.mjs` — `--label`（search）、`--label`繰り返し（create）、`--add-label`/`--remove-label`繰り返し（update）、`show`サブコマンドのディスパッチ追加
- `tools/linear-cli/README.md` — 上記オプション・`show`コマンドのドキュメント追加
- `claude-plugins/my-tools/skills/linear-cli/SKILL.md` / `README.md` — 同上をスキル側にも反映、`meta.version`をbump

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                      | 理由                                                                                                                                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search --label`はラベル名をID解決せずfilterへそのまま渡す                                                                                                                                | `state`/`title`と同じ既存パターンに揃えるだけで実装できる。Linear GraphQL APIのフィルタはネストしたフィールド名でのマッチが可能（IDの事前解決が必要なのはmutation側の`labelIds`入力のみ）                               |
| `create`/`update`はmutation入力に`labelIds`（ID配列）が必要なため、team-scopedでラベル名→IDを解決する。存在しないラベル名を指定した場合はエラー終了し、CLI側でラベルを自動作成しない      | 既存の`update.mjs`のワークフロー状態解決（存在しない状態名はエラー）と同じ思想。ラベルの新設はLinear UI側で人間が行う運用とし、typoによるラベル乱立を防ぐ                                                               |
| `update`のラベル追加・削除は「現在のlabelIdsを読み取り→追加/削除を計算→全体を送り直す」read-modify-write。比較更新（楽観ロック）は行わない                                                | 既存のclaim（ステータス更新）と同じベストエフォート方針（[SKILL.md](../../../claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md)の「Claim」節）に揃える。同一issueへの同時ラベル更新が稀に競合しても許容する |
| `update`のラベル機能はv1では必須ではなく優先度低（[00-overview.md](00-overview.md)の設計では、issue作成時に`create --label`でラベルを確定させれば足り、事後変更の必要性は薄い）と明記する | スコープ肥大化を避ける。実装時に時間が無ければ`update`側は見送ってもStep4は成立する                                                                                                                                     |
| `show`は`comments`/`comment-delete`と同じ「単一issue専用コマンド」という設計に揃え、`search`の出力フォーマット（テーブル/`--json`）は変更しない                                           | `search`は一覧・絞り込み用途、`show`は1件の詳細（description本文を含む）取得用途と役割を分離する。既存`search`のテーブル出力にdescriptionのような長文を混ぜると可読性を損なう                                           |

## ルール更新ポイント

`claude-plugins/my-tools/skills/linear-cli/SKILL.md`のfrontmatter変更（コマンド追加に伴う本文変更）を伴うため、リポジトリ直下[AGENTS.md](../../../AGENTS.md)のSSOT規約に従い`meta.version`をbumpすること（`just --justfile tools/internal/justfile skill-version-bump`、または手動）。コミット時のpre-commitフックの挙動・落とし穴は[docs/repo-meta/skill-md-commits.md](../../../docs/repo-meta/skill-md-commits.md)を参照。

## 推奨の進め方

- **実行主体**: メインエージェント単独（5ファイル程度の変更で、既存パターンの踏襲が中心。並列化のメリットは薄い）。
- **TODO化**: 「show.mjs新規作成」「search/create/update拡張」「cli.mjs配線」「README×2更新」を個別TODOに分ける（1項目=1コミット目安）。
- **関連スキル**: 特になし。
