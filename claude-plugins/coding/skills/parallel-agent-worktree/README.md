# parallel-agent-worktree スキル

## このスキルの狙い

同一ローカル環境上で複数のClaude Codeセッションを並行起動し、Linearの未着手issueをタスクキューとして衝突なく分担するための「使い方」を与える薄いオーケストレーション層。専用の常駐オーケストレータープロセスは作らず、各セッションが自然言語のSKILL.md指示に従って自律的に「検索→worktree作成→claim→作業→完了報告」を行う設計（詳細な経緯・検討過程は[.claude/plans/parallel-agent-worktree/00-overview.md](../../../../.claude/plans/parallel-agent-worktree/00-overview.md)参照）。

このスキル自体はソースコードを持たず、[linear-cli](../../../my-tools/skills/linear-cli/)（Linear操作）とハーネス組み込みの`EnterWorktree`/`ExitWorktree`（worktree管理）を繋ぐ判断フローだけを提供する。

## 1セッション=1タスクで完結させる理由

当初案では「1タスク完了ごとに`ExitWorktree`して次のタスクへ進む」自律ループを想定していたが、実装時に`ExitWorktree`ツール自体の説明文が「Do NOT call this proactively — only when the user asks」と明記していることが判明した。`EnterWorktree`にある「プロジェクト指示（CLAUDE.md/memory等）による起動なら明示指示として扱ってよい」という例外が`ExitWorktree`側には無く、字面通りに読むとタスク完了ごとの自動`ExitWorktree`呼び出しはツールの想定用途から外れる。

ユーザー確認の結果、「1タスクのcommit・pushをもって処理は完結し、続けて別タスクに着手したい場合はユーザーが新しいセッションを起動する」という運用に倒すことでこの制約と両立させた。そのため`ExitWorktree`はSKILL.mdからは能動的に呼ばず、ユーザーが明示的に要求した場合、またはharness標準のセッション終了時keep/remove確認に委ねる。

## トラッキングissue方式に変更した経緯

当初案は「稼働中（ステータス=作業中）issue群それぞれに付いた環境コメントを人間が目視で回って空き状況を把握する」設計だった。実装後にユーザーから「これでは空きworktreeの判定が事実上不可能」との指摘を受けた。理由は2点:

1. **解放シグナルが無い** — タスク完了時にissueのステータスは変わるが、環境コメント自体は削除されず、コメントだけを見ても「まだ稼働中か」を判断できない
2. **1箇所に集約されていない** — タスクissueの数だけ分散するため、空き状況を知るには稼働中issueを1件ずつ開いて回る必要がある

これを解消するため、専用の**トラッキングissue1件**に環境エントリを集約する方式に変更した。claim時にエントリを`comment`で追加し、完了時に同じエントリを`comment-delete`で削除することで、トラッキングissueのコメント一覧＝現在の占有状況そのものになる（[linear-cli](../../../my-tools/skills/linear-cli/)側に`create`/`comments`/`comment-delete`を追加実装。詳細は[linear-cli README](../../../my-tools/skills/linear-cli/README.md)の「スコープを絞った理由」節参照）。

この方式にも限界はある。エージェントがクラッシュする等で完了操作（5.）を踏まずに終わった場合、そのエントリは占有中のまま残り続ける（自動失効なし）。ベストエフォート運用（claimの排他制御と同じ思想）として許容し、明らかに古いエントリは人間またはエージェントが目視で気づいて手動削除する運用にした。

## スコープ外・意図的に持たない機能

- **claimの厳密な排他制御** — 比較更新・楽観ロックは持たない（ベストエフォート、ユーザー確認済み）。`linear-cli`側も同じ方針（[linear-cli README](../../../my-tools/skills/linear-cli/README.md)参照）
- **占有エントリの自動失効・自動クリーンアップ** — クラッシュ等で残った古いエントリの検出は人手に委ねる（上記「トラッキングissue方式に変更した経緯」参照）
- **PR作成・マージタイミングの固定ルール化** — issueごとにエージェントが判断する

## メンテナンス上の注意

- `EnterWorktree`/`ExitWorktree`ツールの説明文（挙動・制約）が変わった場合、SKILL.mdの該当節（特に「ExitWorktreeを能動的に呼ばない理由」）を合わせて見直すこと（自動追随しない）
- `linear-cli`側のサブコマンド・オプションが変わった場合も、このSKILL.mdの記載例が古くならないよう確認すること
- トラッキングissueのタイトル文字列（`[worktree-tracking] 稼働中worktree一覧`）を変更する場合、SKILL.md本文の全箇所を揃えて更新すること（検索・作成の両方で同じ文字列を使うため、片方だけ変えると新規作成が乱立する）
