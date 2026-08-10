# `parallel-agent-worktree` の動作確認テスト

このスキルは自前のソースコードを持たない薄いオーケストレーション層（[linear-cli](../../../my-tools/skills/linear-cli/) + ハーネス組み込み`EnterWorktree`/`ExitWorktree`）なので、`writing-skill-web/tests`のようなpytestスイートは書けない。ここには**実際にLinear issueとgit worktreeを動かす手動テストシナリオ**を置く。

未実施の動作確認（[.claude/plans/parallel-agent-worktree/00-overview.md](../../../../../.claude/plans/parallel-agent-worktree/00-overview.md)の「動作確認（実issueでの通し実行）」）に対応する。

## スコープ

**このディレクトリは`parallel-agent-worktree`スキル自身の通し動作確認のみを対象とする。** `linear-cli`単体のユニットテストはここでは扱わない（`linear-cli`はNode CLIとして別途テストを持つべきだが、2026-08-11時点で未整備。必要になれば`tools/linear-cli/`側に用意する）。

## 事前準備（全テストケース共通）

1. `linear-cli`がPATH上で使えること
   ```bash
   which linear-cli
   ```
   使えない場合は`cd tools/linear-cli && pnpm add -g .`でインストールする（[linear-cliスキル](../../../my-tools/skills/linear-cli/SKILL.md)参照）。
2. `LINEAR_API_KEY`が設定済みであること（`tools/linear-cli/.env`または環境変数）。設定確認は次の読み取り専用コマンドで代用できる（エラーが出なければ疎通OK）。
   ```bash
   linear-cli search --team AI --project test
   ```
3. **team/projectは`AI`/`test`を使う。** これは本番運用のteamと分離された検証用team。teamキーは大文字`AI`（小文字`ai`ではヒットしない。`filter.team.key.eq`が大文字小文字を区別するため）。実issueが飛び交う本番teamでテストしないこと。
4. リポジトリルートに`.linear-cli/config.json`が無いため、テスト中の全`linear-cli`コマンドで`--team AI --project test`を毎回明示する（省略すると絞り込み無しで全team対象になってしまう）。恒久的に楽をしたい場合のみ、`tools/linear-cli/.linear-cli/config.json.example`をリポジトリルートの`.linear-cli/config.json`としてコピーしてよいが、他のテストや作業に影響しないよう本テスト専用に一時的に置く運用を推奨（終わったら消す）。**なお`tools/linear-cli/.linear-cli/config.json`（gitignore対象外だが未コミットのローカルファイル）は`"team": "ai"`と小文字になっており、そのままでは既定値として機能しない。ローカルでこの設定ファイルに頼る場合は`"AI"`に直す。**
5. ワークフロー状態名は既定の`Backlog`/`Todo`/`In Progress`/`Done`/`Canceled`（Linear初期セット）のままであることを`AI-1`（後述）で確認済み。未着手を表す状態名は`Backlog`（`Todo`ではない）なので、以下の`--status`はteamの実状態名に合わせて読み替えること。
6. トラッキングissue（固定タイトル`[worktree-tracking] 稼働中worktree一覧`）は使い回す前提。TC1で作成したものをTC2以降でも再利用する（毎回作り直さない）。
7. `linear-cli`に issue 削除コマンドは無いため、テストで作成したissueはLinear上に残り続ける。何度もテストを回す場合は新規issueを都度作らず、既存のテスト用issueのステータス/担当者をリセットして使い回す（`linear-cli update <id> --status Todo --assignee none`）。

## テストケース一覧

| #                                                     | シナリオ                                      | 目的                                                                                               |
| ----------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| [TC1](#tc1-通しの正常系初回トラッキングissue作成込み) | 通しの正常系（トラッキングissue新規作成込み） | 0→10のフルフロー（検索→worktree作成→claim→作業→完了→占有解放）が指示通りに進むこと                 |
| [TC2](#tc2-トラッキングissue再利用時)                 | トラッキングissue再利用時                     | 既存トラッキングissueを誤って再作成せず、既存の1件を使い回すこと                                   |
| [TC3](#tc3-二重claimシミュレーション)                 | 二重claimシミュレーション                     | ベストエフォート方式で二重claimが起きても、後から気づいた側が別issueへ切り替える運用が機能すること |
| [TC4](#tc4-claim失敗時の後始末)                       | claim失敗時の後始末                           | claim手順の一部が失敗した場合にworktreeが放置されず`remove`されること                              |
| [TC5](#tc5-環境不足の可視化)                          | 環境不足の可視化                              | `linear-cli comments <トラッキングissue>`だけで稼働中一覧が分かること                              |
| [TC6](#tc6-exitworktreeを能動的に呼ばないこと)        | ExitWorktreeを能動的に呼ばないこと            | 完了操作後、ユーザーが指示しない限りセッションがworktreeに留まること                               |

---

### TC1: 通しの正常系（初回・トラッキングissue作成込み）

**事前準備**

- team `AI` / project `test` を使う（他のテストと同時に走らせない）
- テスト対象issueを1件作成しておく。**`AI-1`（タイトル`[test] parallel-agent-worktree TC1`・ステータス`Backlog`）が既に存在する場合はそれを流用してよい**（無ければ以下で新規作成する）
  ```bash
  linear-cli create --title "[test] parallel-agent-worktree TC1" --team AI --project test
  ```
  → 作成直後のステータス（既定は`Backlog`）と、返ってきた`identifier`（例: `AI-1`）を控える。

**テスト方法**

1. Claude Codeセッションを1つ起動し、「parallel-agent-worktreeスキルを使って、team AI / project testで未着手タスクを1つ処理して」のように自然言語で指示する。
2. エージェントが以下を順に行うことを観察する。
   - トラッキングissue（`[worktree-tracking] 稼働中worktree一覧`）を`--title`で検索 → 0件 → `linear-cli create`で新規作成
   - `linear-cli search --status Backlog --assignee none --team AI --project test`でTC1のissueを発見
   - `EnterWorktree({ name: "<identifier>を含む名前" })`でworktree作成、セッションの作業ディレクトリが切り替わる
   - ステータスを作業中へ更新 + タスクissue・トラッキングissue双方へ環境情報コメント（`host=..., worktree=...`）を投稿
   - worktree内で何らかの作業（ダミーで良い。例: README一行追記）を行う
   - ステータスを完了へ更新 → commit → push
   - トラッキングissueから自分のエントリを`comment-delete`で削除
   - `ExitWorktree`を能動的に呼ばず処理完了を報告する（TC6で別途検証）

**期待結果**

- トラッキングissueがLinear上に1件だけ新規作成されている（タイトル完全一致）
- TC1のissueのステータスが完了相当に変わっている
- TC1のissueにコメントが1件残っている（`host=..., worktree=...`。削除されない）
- トラッキングissueのコメントは0件（claim時に追加→完了時に削除されているため）
  ```bash
  linear-cli comments <トラッキングissueのidentifier>
  ```
- worktree内でのcommitがpushされている（`git log`にコミットが乗り、リモート追跡ブランチに反映されている）
- エージェントが「次のissueへ自動で進む」ことなく、1タスクで処理を終えて報告している

---

### TC2: トラッキングissue再利用時

**事前準備**

- TC1完了済み（トラッキングissueが既に1件存在する状態）
- 新しいテスト対象issueをもう1件作成
  ```bash
  linear-cli create --title "[test] parallel-agent-worktree TC2" --team AI --project test
  ```

**テスト方法**

1. 新しいClaude Codeセッションを起動し、TC1と同じ指示を出す。
2. エージェントの最初の動作（トラッキングissue確認ステップ）を観察する。

**期待結果**

- `linear-cli search --title "[worktree-tracking] 稼働中worktree一覧"`が1件ヒットし、`linear-cli create`が**呼ばれない**（トラッキングissueが重複作成されない）
- 以降TC1と同じ流れでTC2issueが処理される
- テスト後、トラッキングissue（タイトル完全一致）がLinear上に1件のみであることを確認する
  ```bash
  linear-cli search --title "[worktree-tracking] 稼働中worktree一覧" --team AI
  ```

---

### TC3: 二重claimシミュレーション

SKILL.mdの「Claim（ベストエフォート）」節が想定する「排他制御なし」を確認する。2セッション同時起動が難しい場合は、片方をコマンドで代行してよい。

**事前準備**

- テスト対象issueを1件作成
  ```bash
  linear-cli create --title "[test] parallel-agent-worktree TC3" --team AI --project test
  ```

**テスト方法**

1. Claude Codeセッションを起動し、「TC3のissueを見つけたらclaimする直前で一度止めて」のように、claim直前まで進めて一時停止させる（またはエージェントに未着手issue検索まで行わせ、claim実行前に手動でステップ2を横取りする）。
2. エージェントがclaimする前に、別ターミナルから同じissueを先にclaimしてしまう。
   ```bash
   linear-cli update <identifier> --status "In Progress" --assignee someone-else@example.com
   ```
3. その後、エージェントに続行させclaimを実行させる。

**期待結果**

- `linear-cli update`自体はエラーにならず上書きで成功する（比較更新・楽観ロックが無いため）
- エージェントは二重claimの発生に気づける材料（担当者が既に別人になっている等）を持たないまま処理を続けてしまう可能性がある — これはSKILL.md記載どおりの既知の許容仕様であることを確認する（「後から気づいた側が担当者/ステータスを見直し、別issueへ切り替える」運用は人間の目視 or 次にそのissueを触った別エージェントが担当者不一致に気づいた時点で発動する、というドキュメント上の想定と実際の挙動が一致するかを見る）
- このテストの主目的は「エラーで落ちないこと」と「ドキュメント記載の許容範囲を超える異常（例外送出やworktree破損）が起きないこと」の確認であり、衝突が自動検出・自動回避されることは期待しない

---

### TC4: claim失敗時の後始末

**事前準備**

- テスト対象issueを1件作成
  ```bash
  linear-cli create --title "[test] parallel-agent-worktree TC4" --team AI --project test
  ```

**テスト方法**

1. Claude Codeセッションを起動し、通常通り未着手issue検索→worktree作成まで進めさせる。
2. claim手順の最初のコマンド（ステータス更新）がわざと失敗するよう仕向ける。最も再現しやすいのは**存在しない状態名を使わせる**こと。例えば指示文に「ステータス更新には"作業中"ではなく存在しないダミーの状態名"NoSuchStatus"を使ってみて」と含める、または`.env`の`LINEAR_API_KEY`を一時的に空文字に書き換えてAPIエラーを起こす。
   - `LINEAR_API_KEY`を使う場合は必ずテスト後に元の値へ戻す（`.env`は`.gitignore`対象なのでcommit事故の心配は無いが、他の作業に影響するため）
3. エージェントがエラーを検知した後の挙動を観察する。

**期待結果**

- ステータス更新コマンドが非ゼロ終了し、エラーメッセージが出る
- SKILL.mdの「claim失敗時の後始末」節どおり、エージェントが`ExitWorktree({ action: "remove" })`を呼んで作成済みworktreeを削除する
- `discard_changes`が必要な状況（コミット済みの変更が残っている）でない限り、追加確認なしで削除が完了する
- 対象issueのステータス・担当者が未着手のまま変化していない（更新自体が失敗しているので通常は変化しないはずだが、部分的に成功していた場合は巻き戻しまたはユーザーへの報告が行われることを確認する）
- worktree一覧（`.claude/worktrees/`）に残骸が残っていない

---

### TC5: 環境不足の可視化

**事前準備**

- 上記テストの少なくとも1つでclaim済み・未解放のエントリがトラッキングissueに残っている状態を作る（例: TC4の失敗テストを`remove`前に一時停止させておく、または TC1〜TC3のいずれかを意図的に完了操作の直前で止める）

**テスト方法**

```bash
linear-cli comments <トラッキングissueのidentifier>
```

**期待結果**

- 稼働中の占有エントリの数だけコメントが返る
- 各コメントの本文が`host=<ホスト名>, worktree=<絶対パス>, issue=<identifier>`形式になっている
- この1コマンドの出力だけで「どの環境がどのissueを処理中か」が分かり、稼働中issue群を個別に巡回する必要が無いことを確認する

---

### TC6: ExitWorktreeを能動的に呼ばないこと

**事前準備**

- TC1などで1タスクの完了操作（commit・push・占有解放）まで完了した直後のセッション状態

**テスト方法**

1. 完了報告後、エージェントに何も追加指示を出さずセッションの挙動を観察する。
2. 続けて「worktreeを閉じて」「元のディレクトリに戻って」と明示的に指示する。

**期待結果**

- 手順1: エージェントが`ExitWorktree`を自発的に呼ばない。作業ディレクトリはworktree内に留まったまま
- 手順2: 明示指示後、`ExitWorktree`が呼ばれる。呼び出し時の`action`が以下の基準と一致する
  - push済み（コミットがリモートに存在する）→ `action: "remove"`
  - 未pushの差分が残っている → `action: "keep"`

## 後片付け

- テストで作成したLinear issue（TC1〜TC4）はステータスを`Todo`・担当者を`none`に戻せば次回テストで再利用できる。使い切りにする場合はタイトルに`[test]`プレフィックスを付けているので、Linear Web UIから手動アーカイブ/削除する（`linear-cli`に削除コマンドは無い）。
- トラッキングissueはテスト専用に使い回すため、テスト終了後も削除しない（次回のTC1〜TC6で再利用する）。
- テストで作成したgit worktree（`.claude/worktrees/`配下）とブランチは、`ExitWorktree({ action: "remove" })`または手動の`git worktree remove`で片付ける。pushしていないコミットが残っている場合は先に内容を確認してから削除する。
