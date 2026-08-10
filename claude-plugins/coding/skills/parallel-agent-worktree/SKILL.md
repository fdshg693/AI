---
name: parallel-agent-worktree
description: 複数のClaude Codeセッション（同一ローカル環境上で並行して動くエージェント）が、Linearの未着手issueをタスクキューとして使い、それぞれ別のgit worktreeで衝突なく1タスクずつ分担して作業を進めるためのスキル。Linear issueの検索→claim→worktree作業→完了報告までの一連の流れを自然言語指示で進めたい場合に使う。専用のトラッキングissue1件で「どの環境がどのworktreeを使用中か」を追跡し、空き状況を判定可能にする。専用オーケストレーター（常駐プロセス等）は前提とせず、1タスクのcommit・push完了をもって処理は完結する（次のタスクへ自動で継続しない）。
# 前提条件（このスキル自体はインストール・セットアップを一切行わない）:
#   - `linear-cli` コマンドがPATH上で使え、LINEAR_API_KEYが設定済みであること
#     （セットアップは claude-plugins/my-tools/skills/linear-cli/SKILL.md 参照）
#   - `EnterWorktree`/`ExitWorktree` がハーネス組み込みツールとして利用可能であること
#
# 依存スキル: claude-plugins/my-tools/skills/linear-cli（issue検索・作成・ステータス更新・コメント追加/一覧取得/削除）
# このスキルはlinear-cliとハーネス組み込みworktreeツールを繋ぐ薄いオーケストレーション層で、
# 自前のソースコードは持たない。
meta:
  requires_repo_tools: none
  requires_env: LINEAR_API_KEY
  dependencies: linear-cli
  requires_install: none
  requires_hooks: none
  requires_skills: linear-cli
  status: experimental
  description: no description
  version: 2.0.0
---

# parallel-agent-worktree の使い方

同一ローカル環境上で複数のClaude Codeセッションを並行起動し、Linearの未着手issueをタスクキューとして分担するためのスキル。**1セッション=1タスクで完結**させる設計で、複数タスクを続けて処理したい場合はユーザーがセッションを複数起動する（このスキル自体はループしない）。

「どの環境（PC・worktree）が今どのタスクを処理中か」は、専用の**トラッキングissue**1件に集約する。稼働中issue群のコメントを1件ずつ目視で回る必要はなく、トラッキングissueのコメント一覧を見るだけで空き状況が分かる。

## トラッキングissueのタイトル

固定文字列 `[worktree-tracking] 稼働中worktree一覧` を使う（team内で1件のみ存在する前提。複数ヒットした場合は重複なのでユーザーに知らせ、先頭の1件を使う）。

## 全体の流れ

```markdown
0. トラッキングissueの確認・作成
   linear-cli search --title "[worktree-tracking] 稼働中worktree一覧" --team <team>
   → 0件なら作成する
   linear-cli create --title "[worktree-tracking] 稼働中worktree一覧" --team <team>
   → 1件以上あれば（複数ヒットなら先頭を使う）そのidentifierを以後の手順で使い回す

1. 未着手タスクの検索
   linear-cli search --status <未着手を表す状態名> --assignee none
   → 候補issueの一覧から着手する1件を選ぶ（複数候補があれば先頭など任意の1件でよい。
   排他制御は無いため他エージェントとの重複は許容する。「claim」節参照）

2. Worktree作成
   EnterWorktree（ハーネス組み込みツール）を使い、選んだissueのidentifier
   （例: ENG-123）を含む名前でworktreeを新規作成する
   EnterWorktree({ name: "<identifier>" のような名前 })
   → セッションの作業ディレクトリが新規worktreeへ切り替わる

3. Claim（ベストエフォート）
   linear-cli update <identifier> --status <作業中を表す状態名> --assignee me@example.com
   linear-cli comment <identifier> --body "host=<PCのホスト名>, worktree=<worktreeの絶対パス>"
   linear-cli comment <トラッキングissueのidentifier> --body "host=<PCのホスト名>, worktree=<worktreeの絶対パス>, issue=<identifier>"
   → 最後のコマンドが返す comment の id を、5.の削除で使うため記憶しておく
   → いずれかのステップが失敗した場合は「claim失敗時の後始末」節に従う

4. 作業
   通常のエンジニアリング作業をworktree内で行う

5. 完了
   - Linear issueのステータスを完了を表す状態名へ更新する
     linear-cli update <identifier> --status <完了を表す状態名>
   - 変更をコミットし、push する
   - トラッキングissueから自分のエントリを削除し、占有を解放する
     linear-cli comment-delete <3.で記憶したcomment id>
   - PRを作成するか・いつマージするかはissueの性質に応じてエージェントが判断する
     （固定ルールにしない）
   - commit・push・占有解放が終わった時点でこのスキルの処理は完了。次のissueへは
     自動で進まない（「終了・次のタスクへの引き継ぎ」節参照）

6. 終了・次のタスクへの引き継ぎ
   ExitWorktree はここでは能動的に呼ばない（「ExitWorktreeを能動的に呼ばない理由」節参照）。
   ユーザーが続けて別タスクに着手したい場合は、新しいセッションを開始してもらう
```

## Claim（ベストエフォート）

- 未着手→作業中の更新に、更新前後の厳密な排他制御（比較更新・楽観ロック）は行わない。まれに複数エージェントが同じissueを二重にclaimすることを許容する。二重着手に気づいた側は担当者/ステータスを見直し、別のissueへ切り替える運用でカバーする
- 環境情報コメント（`host=..., worktree=...`）は、claim時にタスクissue・トラッキングissueの両方へ1回ずつ投稿する。タスクissue側は履歴として残し続ける（削除しない）。トラッキングissue側は完了時に`comment-delete`で消し、現在の占有状況だけが残る設計

## claim失敗時の後始末

「3. Claim」の3コマンド（ステータス更新・タスクissueへのコメント・トラッキングissueへのコメント）のいずれかがAPIエラー等で失敗した場合、「worktreeだけ作って誰にも紐づかない」状態や「占有記録に失敗したまま作業を進める」状態を残さないため、作成したworktreeを `ExitWorktree({ action: "remove" })` で削除してから作業を中断する。まだコミットしていない段階なので `discard_changes` は不要なはずだが、エラーで停止して残っている場合は内容を確認してから判断する。それまでに成功していたコマンド（例: ステータス更新のみ成功しコメントが失敗した）があれば、可能な範囲で状態を巻き戻す（ステータスを元に戻す等）か、失敗内容をユーザーに報告して判断を仰ぐ。

## ExitWorktreeを能動的に呼ばない理由

`ExitWorktree` ツール自体の説明文は「Do NOT call this proactively — only when the user asks」と明記しており、`EnterWorktree` にある「プロジェクト指示（CLAUDE.md/memory等）による起動なら明示指示として扱ってよい」という例外が無い。そのため、このスキルはタスク完了（5. 完了）後に自動で `ExitWorktree` を呼ばない。

- ユーザーが明示的に「worktreeを閉じて」「元のディレクトリに戻って」等と指示した場合のみ `ExitWorktree` を呼ぶ。判断基準は次の通り:
  - push済み（コミットがリモートに存在する）→ `action: "remove"`（手元のworktreeを消しても作業は失われない。空きworktreeを増やして次のタスクに使い回せる）
  - 未pushの差分が残っている → `action: "keep"`
- ユーザーが何も指示しない場合は、セッション終了時のharness標準動作（keep/remove確認プロンプト）にそのまま委ねる

## 環境不足の可視化

```bash
linear-cli comments <トラッキングissueのidentifier>
```

このコマンド1回で、現在どの環境（PC・worktree絶対パス）がどのissueを処理中かの一覧が得られる（各コメントが1エントリ）。新しいworktreeを作るかどうかの判断は、この一覧をもとに人間またはエージェントが行う（空き状況の自動判定ロジックはこのスキルのスコープ外）。

- エントリが残ったまま完了操作（5.）が行われなかった場合（エージェントのクラッシュ等）、そのエントリは占有中として残り続ける。自動的な期限切れ処理は無いため、明らかに古い・対応するworktreeが実在しないエントリを見つけた場合は`comment-delete`で手動削除するか、ユーザーに確認する

## 注意点

- `EnterWorktree` は「既に別のworktreeセッションに入っている状態から `name` で新規作成」できない。1セッション=1タスクで完結させる設計上、通常はこの制約に触れない
- ワークフロー状態名（「未着手」「作業中」「完了」に相当する名前）はチームのLinear設定次第で異なる。ハードコードせず、`linear-cli search` を状態名なしで実行するかユーザーに確認して実際の状態名を把握する（`linear-cli` スキル参照）
- トラッキングissueのteamは、`.linear-cli/config.json`に既定値が無ければ`--team`を毎回指定する必要がある。不明な場合はユーザーに確認する
- `linear-cli` のインストール・`LINEAR_API_KEY` 設定はこのスキルでは行わない。未設定エラーが出た場合は `claude-plugins/my-tools/skills/linear-cli/SKILL.md` の案内に従う
