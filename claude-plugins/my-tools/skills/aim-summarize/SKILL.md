---
name: aim-summarize
description: リポジトリ内のファイルをファイル単位でAI要約し、SQLite DB（.aim-use/summaries.db）に永続化する`aim-summarize` CLIツールの使い方を説明する。ファイル要約を生成・更新したい、変更されたファイルだけ再要約したい、DBから要約を取得したい場合に使う。
# 前提条件: `aim-summarize`コマンドがPATH上にインストール済み（`uv tool install --editable tools/aim-use/aim-summarize`）であり、OPENROUTER_API_KEYが設定済み（aim-cliが内部で要求）であること。このスキルはインストール・セットアップは一切行わない
# このスキルの設計意図・前提条件の背景は tools/aim-use/aim-summarize/README.md および PLAN.md 参照（人間のメンテナ向け）
meta:
  tag: []
  requires_repo_tools: git
  requires_env: OPENROUTER_API_KEY
  dependencies: none
  requires_install: aim-summarize
  requires_hooks: none
  requires_skills: aim-cli
  status: stable
  description: no description
  version: 1.0.0
---

# aim-summarize の使い方

`aim-summarize`は、リポジトリ内のファイルをファイル単位でAI要約し、結果をSQLite DB（`.aim-use/summaries.db`）に永続化するCLI。`aim`パッケージ（`aim_cli`）をライブラリとして使い、OpenRouterへの要約リクエストを非同期で並行実行する。`aim-ask`と異なりステートフルで、内容が変わっていないファイルは再要約せずスキップする。

## 前提条件

- `aim-summarize`コマンドが既にインストールされ、PATH上で実行可能であること
- `OPENROUTER_API_KEY`が環境変数または`tools/aim/.env`で設定済みであること
- 対象リポジトリのルートに`.aim-use/config.toml`が作成済みであること（未作成の場合は下記「初回セットアップ」を案内する）
- 未インストール・未設定の場合はこのスキルでは対処しない。エラーが出た場合はユーザーに`tools/aim-use/aim-summarize/README.md`のセットアップ手順を案内する

## 初回セットアップ（対象リポジトリ側、未実施の場合のみ）

```bash
mkdir -p .aim-use
cp <このリポジトリへのパス>/tools/aim-use/aim-summarize/config.toml.example .aim-use/config.toml
```

`.gitignore`に`.aim-use/summaries.db`を追記しておく（DBファイルはコミット対象外）。

`aim-summarize`はカレントディレクトリから親方向に`.aim-use/config.toml`を探索してリポジトリルートを特定する（`git`が`.git`を探索するのと同様）。

## 使い方

```bash
# 要約DBを構築・更新する（新規/変更ファイルのみAI呼び出しが発生する）
aim-summarize generate

# 特定のパス配下のみ対象にする
aim-summarize generate src/foo/ src/bar.py

# ハッシュが一致していても全件再生成する
aim-summarize generate --force

# 実際には生成せず、対象件数・一覧のみ確認する
aim-summarize generate --dry-run

# DBから要約を取得する（AI呼び出しは発生しない）
aim-summarize get
aim-summarize get src/foo/ src/bar.py
aim-summarize get --format json
```

### `generate`

| オプション  | 説明                                             |
| ----------- | ------------------------------------------------ |
| `paths`     | 対象パス（複数可、省略時はリポジトリ全体）       |
| `--force`   | sha256ハッシュ一致でも対象全件を再生成する       |
| `--dry-run` | 実際には生成せず、対象件数・一覧のみ表示して終了 |

- `.gitignore`を常に尊重し、`config.toml`の`include`/`exclude`正規表現で対象ファイルを絞り込む
- ファイルサイズが`max_file_size_bytes`超過、またはバイナリ/デコード不能なファイルは自動的にスキップされ、理由付きで記録される（AI呼び出しは発生しない）
- ファイル内容のsha256ハッシュが前回と一致する場合は再生成をスキップする（`--force`で無視可能）
- OpenRouter API呼び出しが失敗した場合は1回だけリトライし、それでも失敗したらそのファイルだけスキップして記録し、他のファイルの処理は継続する
- 並列実行数は対象リポジトリの`config.toml`の`jobs`（2〜10）に従う。CLI引数での上書きは不可
- ディスク上から消えたファイルのDBレコードは毎回の実行時に自動削除される（孤立レコード削除）
- 完了時に生成/維持/スキップ（理由別）/孤立レコード削除の件数サマリーを表示する

### `get`

| オプション | 説明                               |
| ---------- | ---------------------------------- |
| `paths`    | 対象パス（複数可、省略時はDB全件） |
| `--format` | `markdown`（既定）または`json`     |

- DBから読むだけで、AI呼び出しは発生しない
- ディレクトリを指定した場合はその配下の全ファイルを展開して出力する
- 要約が存在しないパスを指定した場合は「要約未生成」として出力に明示し、非ゼロ終了はしない

## 設定ファイル（`.aim-use/config.toml`）

```toml
model = "gpt-120b"
jobs = 4
max_file_size_bytes = 204800

[[include]]
pattern = ".*\\.py$"

[[include]]
pattern = ".*\\.md$"

[[exclude]]
pattern = "^tests/fixtures/"
```

- パスはリポジトリルートからの相対パス（POSIX区切り`/`）に対して正規表現マッチする
- `include`を1件も指定しない場合は「バイナリでないテキストファイル全て」が対象になる
- `exclude`は`include`より優先される
- `model`には`aim --list-models`で表示される略記のいずれかを指定する（詳細は`aim-cli`スキル参照）
- `jobs`は2〜10の範囲でのみ指定可能。範囲外は起動時エラー

## 既知の制約

- `.gitignore`の解釈は`git ls-files`に委譲している。対象リポジトリがgit管理下でない、または`git`コマンドが利用できない環境では、警告を出したうえで`.gitignore`を無視して全ファイルを走査する
- ファイルのテキスト判定はUTF-8デコード可否とNULバイトの有無によるヒューリスティック。UTF-8以外のテキストエンコーディング（Shift_JISなど）は`binary_or_encoding_error`としてスキップされる

## エラー時の挙動

`.aim-use/config.toml`が見つからない、モデル略記が不正、OpenRouter側エラーが発生した場合はエラーメッセージを標準エラー出力に表示し、非ゼロで終了する。個別ファイルの読み込み失敗・生成失敗は全体を止めず、そのファイルのみスキップ記録される。
