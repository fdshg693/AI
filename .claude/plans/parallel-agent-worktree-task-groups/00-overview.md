---
type: Plan
status: ready
---

# parallel-agent-worktree: タスクグループ対応（ブランチ共有・依存関係・worktree再利用） 実装プラン - 概要

## 背景・要件

- 現行の[parallel-agent-worktree](../../../claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md)は「1 issue = 1 worktree」固定で、依存関係のある一連のissueを同じブランチ上で順番に実装する手段がなく、issueを消化するたびにworktreeが増え続ける（乱立）。
- 実現したい要件（ユーザー指示より）:
  - どのISSUE群（タスクグループ）に現在取り組んでいるかを可視化し、そのグループが全完了・ユーザー確認後に次グループへ進められる仕組み
  - 各ISSUEが依存関係（先行issue）と作業ブランチ（最初のissueはどのブランチから切るか）を明示し、同じブランチ上で関連issueを順番に実装できる仕組み
- 対象はこのスキル専用の型を持つISSUEに限定してよい（汎用issue全般との後方互換は不要。「特定のタイプのISSUEのみが配置される前提」）。

## 実装ステップ

1. ✅ [01-issue-shape-and-project-config.md](01-issue-shape-and-project-config.md) — 期待するISSUEの姿・Linear側設定を1ファイル（`issue-shape.md`）にまとめる
2. ✅ [02-issue-authoring-procedure.md](02-issue-authoring-procedure.md) — タスクをISSUE群に分割・配置するAI向け手順書（`issue-authoring.md`）を作る
3. ✅ [03-linear-cli-extension.md](03-linear-cli-extension.md) — `linear-cli`にラベルフィルタ・ラベル付与・`show`コマンドを追加
4. [04-skill-rewrite.md](04-skill-rewrite.md) — `SKILL.md`/`README.md`を新方式（グループ可視化・依存関係チェック・ブランチ/worktree再利用）に書き換え

Step1→2で仕様（ラベル命名・description構造化ヘッダ・config.jsonの使い方）を固定し、Step3（CLI拡張）とStep4（スキル本体）はその仕様を実装する、という順で依存する。

## 主要な決定事項

| 決定                                                                                                                                                                                | 理由                                                                                                                                                                                                                                                                                                                                                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 「タスクグループ」の可視化・切り替えはLinearのラベルではなく **Linear Project + `.linear-cli/config.json`の`project`既定値** で行う                                                 | `linear-cli search`/`create`は既に`--project`を持ち、コード変更ゼロで「現在アクティブなグループ」の絞り込みができる。`config.json`はリポジトリにコミットされるため、グループ切り替え（次タスクへ進める操作）がgit diffとして残り監査可能。ユーザー提案の「ラベル」から意図的に逸脱した決定であり、実装着手前にユーザーへ一言確認するのが安全（[01](01-issue-shape-and-project-config.md)参照） |
| 「ブランチ」は独自ラベル`branch:<slug>`で表現する                                                                                                                                   | LinearにはProject以上に細かい粒度のnativeグルーピングが無く、ブランチ単位でProjectを作るのは過剰。ラベルは`search --label`で「同じブランチに未完了issueが残っているか」を問い合わせるためだけに使う軽量な仕組みで足りる                                                                                                                                                                        |
| 依存先issue・ベースブランチはissue descriptionの構造化ヘッダ（`depends_on:`/`branch:`/`base_branch:`をfrontmatter風に記述）で表現し、Linear純正のissue relations APIは使わない      | relations APIはSDK側の対応状況の裏取りが別途必要で実装コストが高い。依存先は1〜2件程度で、CLIの新設`show`コマンドで都度読めば十分。「専用の型を持つISSUE」という前提とも整合する                                                                                                                                                                                                               |
| worktree再利用の判定は「トラッキングissueのコメント」ではなく、そのホスト上の`git worktree list`を正とする                                                                          | worktreeはホストローカルなファイルシステム状態であり、Linear側のテキストを正にすると乖離（stale化）するリスクがある。トラッキングissueは「今どこが稼働中か」という占有チェック（衝突防止）専用に留める                                                                                                                                                                                         |
| ベースブランチがリポジトリのdefaultブランチと異なる場合、`EnterWorktree`の`worktree.baseRef`設定は切り替えず、`git worktree add`で手動作成後に`EnterWorktree({path})`でアタッチする | `EnterWorktree`は呼び出し単位でbase refを指定できず、`worktree.baseRef`はリポジトリ全体設定のため、切り替えは他の同時セッションに影響し安全でない。`path`引数は「`git worktree add`で作った既存worktreeへの後からのアタッチ」を明示的にサポートしており、この経路に統一できる                                                                                                                  |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `claude-plugins/coding/skills/parallel-agent-worktree/issue-shape.md`
- `claude-plugins/coding/skills/parallel-agent-worktree/issue-authoring.md`
- `tools/linear-cli/src/show.mjs`

### 変更

- `tools/linear-cli/src/search.mjs` / `create.mjs` / `update.mjs` / `cli.mjs`
- `tools/linear-cli/README.md`
- `claude-plugins/my-tools/skills/linear-cli/SKILL.md` / `README.md`
- `claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md` / `README.md`

## ルール更新ポイント

このリポジトリは`.claude/rules`を使わず`AGENTS.md`でルール管理する方針（[.claude/plans/AGENTS.md](../AGENTS.md)）。今回の変更はスキル自身のドキュメント（`SKILL.md`/`README.md`/新規2ファイル）を直接書き換えるものであり、別立てのルールファイル更新は無い。ただし`SKILL.md`のfrontmatter変更を伴うため、リポジトリ直下[AGENTS.md](../../../AGENTS.md)のSSOT規約（「SKILL.md meta フィールドのSSOT」節）に従い`meta.version`のbumpが各ステップで必須（各ステップの注意点に記載）。

## 推奨の進め方（概要ファイル）

- **立案時**: 本プランは要件・設計判断まで固めた状態で作成した。実装着手前に、特に「Project+configへの変更」（要件原文の「ラベル」からの逸脱）をユーザーに一言確認してから進めるのが安全。
- **TODO化**: ステップ一覧をそのままTODO項目にする。Step3（linear-cli拡張）・Step4（スキル本体）はStep1/2（ドキュメント）が定める命名規約・書式に依存するため、Step1→2→3→4の順で進める。
- **実行主体**: 全ステップとも1〜数ファイルの変更で完結する規模のため、メインエージェント単独で十分。並行化・worktree isolationは不要。
