# linear-cli — Linear連携CLI

**関連スキル: `claude-plugins/my-tools/skills/linear-cli`**

[`@linear/sdk`](https://www.npmjs.com/package/@linear/sdk)を使い、[parallel-agent-worktree](../../claude-plugins/coding/skills/parallel-agent-worktree/)スキルが必要とする最小限のLinear操作（issue検索・作成・ステータス更新・コメント追加/一覧取得/削除）だけを提供するNode CLI。設計の背景・決定事項は[.claude/plans/linear-integration/](../../.claude/plans/linear-integration/)を参照。

CLIオプション・設定ファイル形式・挙動を変更した場合は、上記スキルの`SKILL.md`も同じ変更の中で更新すること（スキル側は自動追随しない）。

## インストール

```bash
cd tools/linear-cli
pnpm add -g .
```

登録後はリポジトリ内のどこからでも`linear-cli`コマンドが使える（設定・APIキーの解決はCLIのソースディレクトリ基準の絶対パスで行うため、実行時のカレントディレクトリには依存しない。ただし`.linear-cli/config.json`の探索だけはカレントディレクトリ基準、後述）。不要になったら解除する。

```bash
pnpm remove -g linear-cli
```

グローバル登録せずに使う場合（CI・一時的な確認など）は、リポジトリルートから`pnpm --filter linear-cli exec`経由で呼ぶ。

```bash
pnpm --filter linear-cli exec node src/cli.mjs search --status Todo
```

## セットアップ（APIキー）

個人APIキー（[Linear Settings > API](https://linear.app/settings/account/security)で発行）を、以下のいずれかで`LINEAR_API_KEY`として指定する（環境変数が優先）。

1. 環境変数`LINEAR_API_KEY`
2. `tools/linear-cli/.env`（`.env.example`をコピーして値を設定。`linear-cli`実行時のカレントディレクトリに依存せず、常にこのファイルを参照する）

```bash
cp tools/linear-cli/.env.example tools/linear-cli/.env
# .env を編集して LINEAR_API_KEY=lin_api_... を設定
```

OAuthの対話フローは対象外（非対話・スクリプト実行前提のため）。

## 設定ファイル（`.linear-cli/config.json`、省略可）

team/projectの既定値を固定できる。カレントディレクトリから親方向に`.linear-cli/config.json`を探索し、見つからない場合はエラーにせずteam/project絞り込み無し（=APIキーがアクセス可能な全team）で動作する。

```bash
cp tools/linear-cli/.linear-cli/config.json.example .linear-cli/config.json
# 対象リポジトリのルートに配置し、team/projectを編集する
```

```json
{
  "team": "ENG",
  "project": "My Project"
}
```

`--team`/`--project`のコマンドライン引数はこの設定ファイルの値より優先される。

## サブコマンド

### `search` — 未着手issue検索

```bash
linear-cli search --status Todo --assignee none
linear-cli search --team ENG --project "My Project" --status "In Progress"
linear-cli search --status Todo --limit 20 --json
linear-cli search --title "[worktree-tracking] 稼働中worktree一覧" --team ENG
```

| オプション   | 説明                                                                                               |
| ------------ | -------------------------------------------------------------------------------------------------- |
| `--team`     | teamキーで絞り込む。省略時は設定ファイルの既定値                                                   |
| `--project`  | project名で絞り込む。省略時は設定ファイルの既定値                                                  |
| `--status`   | ワークフロー状態名（例: `Todo`）で絞り込む。省略時は絞り込み無し                                   |
| `--assignee` | 担当者メールアドレスで絞り込む。`none`を指定すると未アサインissueに絞り込む                        |
| `--title`    | タイトル完全一致で絞り込む。特定のissue（トラッキングissue等）の存在確認に使う                     |
| `--limit`    | 取得件数の上限（既定50）                                                                           |
| `--json`     | JSON配列を標準出力へ。未指定時は`identifier`/`status`/`assignee`/`title`/`url`のタブ区切りテーブル |

### `create` — issue新規作成

```bash
linear-cli create --title "[worktree-tracking] 稼働中worktree一覧" --team ENG
linear-cli create --title "..." --team ENG --project "My Project" --description "..."
```

`--title`/`--team`は必須（`--team`省略時は設定ファイルの既定値）。`--project`省略時はどのprojectにも属さないissueになる。issueの新規作成・削除・複数team横断操作は原則スコープ外だが、[parallel-agent-worktree](../../claude-plugins/coding/skills/parallel-agent-worktree/)がトラッキングissueを「無ければ作る」ために必要な最小限のみ実装している（他ユースケース向けの汎用issue作成機能ではない）。

### `update` — ステータス更新・担当者割当

```bash
linear-cli update ENG-123 --status "In Progress"
linear-cli update ENG-123 --status Done --assignee someone@example.com
linear-cli update ENG-123 --assignee none
```

`--status`/`--assignee`の少なくとも一方が必須。`--status`の状態名はteamのワークフロー状態一覧から都度解決するため、CLI側に固定の状態名はない（Linearの初期セットに限らず、チーム独自のカスタム状態名でも動く）。claim（未着手→作業中）の競合はこのCLI側では制御しない（比較更新・楽観ロック無し。ベストエフォート）。

### `comment` — issueへのコメント追加

```bash
linear-cli comment ENG-123 --body "環境情報: host=..., worktree=..."
echo "作業完了しました" | linear-cli comment ENG-123
```

`--body`省略時は標準入力を読む（`aim`コマンドの`--prompt`と同じ慣習）。本文はMarkdownとしてそのまま渡される。

### `comments` — コメント一覧取得

```bash
linear-cli comments ENG-123
linear-cli comments ENG-123 --json
```

指定issueのコメントを`id`/`body`/`createdAt`/`url`付きで取得する。トラッキングissueの現在の占有エントリを読むために使う。

### `comment-delete` — コメント削除

```bash
linear-cli comment-delete <comment-id>
```

コメントIDはLinear上でグローバルに一意なため、issue IDの指定は不要。占有解除（環境コメントの削除）に使う。

## エラー時の挙動

`LINEAR_API_KEY`未設定・issue/ユーザー/状態が見つからない・Linear側APIエラーが発生した場合、エラーメッセージを標準エラー出力に表示し、非ゼロで終了する。

## ファイル構成

```
tools/linear-cli/
├── README.md                  # 本ファイル
├── package.json                # パッケージ定義 + bin (linear-cli)
├── .env.example / .env         # LINEAR_API_KEY（.envはgitignore対象）
├── .gitignore
├── .linear-cli/
│   └── config.json.example    # 対象リポジトリにコピーする設定ファイルのサンプル（省略可）
└── src/
    ├── cli.mjs                 # サブコマンドディスパッチャ（bin実体）
    ├── env.mjs                  # .env読み込み
    ├── client.mjs                # LinearClient生成（LINEAR_API_KEY検証込み）
    ├── config.mjs                 # .linear-cli/config.json の探索・読み込み
    ├── search.mjs                  # issue検索
    ├── update.mjs                   # ステータス更新・担当者割当
    ├── create.mjs                    # issue新規作成
    └── comment.mjs                    # コメント追加・一覧取得・削除
```
