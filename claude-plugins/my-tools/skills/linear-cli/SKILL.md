---
name: linear-cli
description: 未着手issue検索・issue作成・ステータス更新（担当者割当込み）・コメント追加/一覧取得/削除の各操作を提供する`linear-cli` CLIツールの使い方を説明する。Linear上のissueをタスクキューとして検索・claim・完了報告したい場合、およびトラッキング用issueの存在確認・作成・コメントによる占有状況管理をしたい場合に使う。issueの削除・複数team横断の一括操作は対象外。
# 前提条件: `linear-cli`コマンドがPATH上にインストール済み（`pnpm add -g .`をtools/linear-cli/で実行）であり、
# LINEAR_API_KEYが設定済みであること。このスキルはインストール・セットアップは一切行わない
# このスキルの設計意図・前提条件の背景は同階層のREADME.md参照（人間のメンテナ向け）
meta:
  requires_repo_tools: tools/linear-cli
  requires_env: LINEAR_API_KEY
  dependencies: "@linear/sdk"
  requires_install: "cd tools/linear-cli && pnpm add -g ."
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.1.0
---

# linear-cli の使い方

`linear-cli`はLinearのissueをタスクキューとして扱うための最小CLI。提供する操作はissue検索・作成・ステータス更新/担当者割当・コメント追加/一覧取得/削除で、issueの削除・複数team横断の一括操作は扱わない。

## 前提条件

- `linear-cli`コマンドが既にインストールされ、PATH上で実行可能であること
- `LINEAR_API_KEY`が環境変数または`tools/linear-cli/.env`で設定済みであること（個人APIキー。OAuth対話フローは対象外）
- 未インストール・未設定の場合はこのスキルでは対処しない。エラーが出た場合はユーザーに`tools/linear-cli/README.md`のセットアップ手順を案内する

## 設定ファイル（`.linear-cli/config.json`、省略可）

team/projectの既定値をリポジトリルートの`.linear-cli/config.json`で固定できる。省略時は絞り込み無し（APIキーがアクセス可能な全team）で動作するため、単一team運用ならこのファイルが無くても`--team`を毎回指定すれば足りる。

```json
{
  "team": "ENG",
  "project": "My Project"
}
```

## `search` — issue検索（未着手タスク検索・特定issueの存在確認）

```bash
linear-cli search --status Todo --assignee none
linear-cli search --team ENG --status "In Progress" --json
linear-cli search --title "[worktree-tracking] 稼働中worktree一覧" --team ENG
```

- `--status`にはteamのワークフロー状態名をそのまま渡す（`Todo`/`Backlog`等。ハードコードされた固定値は無く、team側でカスタム状態名が使われていてもそのまま動く。実際の状態名が分からない場合は`--status`を省略して一覧を見るか、ユーザーに確認する）
- `--assignee none`で未アサインissueに絞り込む（「未着手タスクの検索」の定型パターンはこの2引数の組み合わせ）
- `--title`はタイトル完全一致。特定の1件（トラッキングissue等）が既に存在するかを確認する用途に使う（結果0件なら`create`で作成する）
- `--json`を付けない場合はタブ区切りテーブル（`identifier`/`status`/`assignee`/`title`/`url`）が標準出力に出る

## `create` — issue新規作成

```bash
linear-cli create --title "[worktree-tracking] 稼働中worktree一覧" --team ENG
```

- `--title`/`--team`が必須（`--team`省略時は設定ファイルの既定値）。`--project`・`--description`は任意
- 用途は限定的（例: [parallel-agent-worktree](../../../coding/skills/parallel-agent-worktree/)がトラッキングissueを「無ければ作る」ため）。汎用のタスク起票コマンドとして多用する設計ではない

## `update` — ステータス更新・担当者割当（claim/完了報告）

```bash
# claim: ステータスを作業中へ、担当者を自分に
linear-cli update ENG-123 --status "In Progress" --assignee me@example.com

# 完了報告
linear-cli update ENG-123 --status Done

# 担当者を外す
linear-cli update ENG-123 --assignee none
```

- `--status`/`--assignee`の少なくとも一方が必須
- claim（未着手→作業中）はベストエフォート。このCLIは比較更新・楽観ロックを行わないため、複数エージェントが同時に同じissueを更新しようとしても衝突検知はしない（呼び出し側の運用で許容する前提）
- ステータス更新に失敗した場合（`--status`の状態名がteamに存在しない等）はエラー終了する。呼び出し側でworktree作成等の後続処理を行っていた場合は、その後始末（例: worktreeのremove）を呼び出し側の責務として行うこと

## `comment` — コメント追加（環境記録・完了報告用）

```bash
linear-cli comment ENG-123 --body "環境情報: host=my-pc, worktree=/path/to/worktree"
echo "作業完了しました" | linear-cli comment ENG-123
```

- `--body`省略時は標準入力を読む
- 本文はMarkdownとしてそのまま渡される。フォーマット（PC識別子・worktreeパスの書式等）はこのCLI側では決めない。呼び出し元スキルの取り決めに従う

## `comments` — コメント一覧取得（占有状況の確認用）

```bash
linear-cli comments ENG-123
linear-cli comments ENG-123 --json
```

- 指定issueのコメントを`id`/`body`/`createdAt`/`url`付きで返す
- トラッキングissue（環境情報コメントを追加・削除する専用issue）の現在の占有エントリを読む用途を想定

## `comment-delete` — コメント削除（占有解除用）

```bash
linear-cli comment-delete <comment-id>
```

- コメントIDはLinear上でグローバルに一意なため、issue IDの指定は不要
- `comment`で追加したコメントの`id`（コマンド結果に含まれる）を使って、そのエントリだけを消す。issueや他のコメントには影響しない

## エラー時の挙動

`LINEAR_API_KEY`未設定・指定issue/ユーザー/状態が見つからない・Linear側APIエラーが発生した場合、エラーメッセージを標準エラー出力に表示し、非ゼロで終了する。未インストール・未設定の場合の対処はこのスキルでは行わない。
