# レポジトリサマリツール（aim-summarize）

## 問題設定

- 巨大レポジトリでは、全てのコードを読むことは不可能なので、ドキュメントが重要
- しかし、ドキュメントは陳腐化しやすいうえに、ドキュメントの内容が正しいかどうかを確認することも難しい

## 解決策

- ドキュメントという整合性が取りにくい情報源ではなく、ファイル単位で要約を持つようにする
  - ドキュメントを置き換えるものではなく、ドキュメントは本来あるべき、全体像に集中させて、そのうえで個々の詳細をファイル要約によって補完する
- 各ファイルを aim CLI によって要約させて、ファイルパスと紐づく要約を SQLite DB に保存する
  - 要約生成時のファイル内容のハッシュを保持し、再生成時にハッシュが変わっていなければスキップすることで、無駄なコスト（API課金・待ち時間）を削減する
- 開発者は、複数パスを指定して DB に保存された要約を一括で取得することで、ドキュメントを読まずとも全体像を把握できる

## 全体方針（決定事項）

以下は検討の結果、決定した設計方針。

| 論点                              | 決定                                                                               |
| --------------------------------- | ---------------------------------------------------------------------------------- |
| 実装形態                          | 独立CLIツール（`aim` CLI を基盤とした aim-use 配下の新規パッケージ）               |
| DB配置                            | 要約対象リポジトリのルートに配置（そのリポジトリ専用のローカルDB）                 |
| 変更検知                          | ファイル内容のハッシュ比較のみ（変更量の算出はしない）                             |
| 対象ファイル選定                  | テキストファイルのみを対象とし、その中で設定ファイルの正規表現パターンで絞り込む   |
| 要約生成モデル                    | `aim` の `gpt-oss-120b`（無料枠）をデフォルトに使用                                |
| 一括取得の出力形式                | Markdown をデフォルトとし、`--format json` にも対応                                |
| コマンド構成                      | `generate`（生成・更新）と `get`（取得のみ）の2サブコマンドに分離                  |
| DBのGit管理                       | Git管理対象外（`.gitignore`）。開発者ごとにローカルで生成する                      |
| generate実行タイミング            | v1では手動実行のみ。CI連携・pre-commitフック連携は将来検討                         |
| ファイルサイズ上限                | 設定ファイルで閾値（バイト数）を指定。超過ファイルは要約対象から自動スキップ       |
| 並列実行数                        | 設定ファイルで指定（2〜10の範囲のみ許可、範囲外はエラー）                          |
| リトライ                          | aim CLI呼び出し失敗時は1回までリトライ。それでも失敗したらスキップしてその旨を記録 |
| バイナリ/エンコーディング判定失敗 | 要約対象から除外し、その旨を記録（例外を投げてgenerate全体を止めない）             |

## ディレクトリ構成

`tools/aim` と同じパターンで、`tools/aim-use` 配下に専用パッケージとして配置する。

```
tools/aim-use/
├── README.md
└── aim-summarize/
    ├── README.md
    ├── PLAN.md                    # 本ファイルをここに移設
    ├── pyproject.toml             # console script: aim-summarize
    ├── .gitignore
    ├── aim_summarize/
    │   ├── __init__.py
    │   ├── cli.py                 # argparse: generate / get サブコマンド
    │   ├── config.py              # .aim-use/config.toml の読み込み・バリデーション
    │   ├── scanner.py             # 対象ファイル列挙（.gitignore尊重 + 正規表現 + バイナリ判定）
    │   ├── hasher.py               # sha256計算
    │   ├── db.py                    # SQLite CRUD（file_summaries テーブル）
    │   ├── summarizer.py            # aim CLI呼び出し（subprocess）+ プロンプト組み立て
    │   └── formatter.py             # markdown / json 整形
    └── config.toml.example          # 対象リポジトリにコピーする設定ファイルのサンプル
```

要約対象となる各リポジトリ側には、以下が作られる（`aim-summarize` パッケージ自体とは別物）。

```
<対象リポジトリルート>/
└── .aim-use/
    ├── config.toml     # 対象ファイル選定ルール・使用モデルなどの設定（Git管理対象）
    └── summaries.db    # 要約DB（Git管理対象外。.gitignoreへの追記が必要）
```

## 設定ファイル（`.aim-use/config.toml`）

```toml
model = "gpt-oss-120b"
jobs = 4                    # 並列実行数（2〜10の範囲のみ許可。範囲外は起動時エラー）
max_file_size_bytes = 204800  # 要約対象とするファイルサイズの上限（超過分はスキップ）

[[include]]
pattern = ".*\\.py$"

[[include]]
pattern = ".*\\.md$"

[[exclude]]
pattern = "^tests/fixtures/"
```

- パスはリポジトリルートからの相対パス（POSIX区切り `/`）に対して正規表現マッチする
- `include` を1件も指定しない場合は「バイナリでないテキストファイル全て」が対象になる
- `exclude` は `include` より優先される
- `.gitignore` は常に尊重し、無視対象ファイルは自動的に対象外とする
- バイナリ判定は拡張子に依存せず、ファイル先頭数KBにNULバイトが含まれるか等のヒューリスティックで行う
- `jobs` は2〜10の範囲でのみ指定可能。範囲外の値が設定された場合は `config.py` のバリデーションで起動時エラーとする
- `max_file_size_bytes` は必須ではなく、省略時はデフォルト値（例: 204800 = 200KB）を使う

## DBスキーマ（`.aim-use/summaries.db`）

```sql
CREATE TABLE file_summaries (
    file_path     TEXT PRIMARY KEY,  -- リポジトリルート相対パス（POSIX区切り）
    content_hash  TEXT NOT NULL,     -- ファイル内容の sha256 (hex)
    summary       TEXT NOT NULL,
    model         TEXT NOT NULL,     -- 要約生成に使用したモデルID
    generated_at  TEXT NOT NULL      -- ISO8601（JST）
);

CREATE TABLE skip_records (
    file_path    TEXT PRIMARY KEY,  -- リポジトリルート相対パス（POSIX区切り）
    reason       TEXT NOT NULL,     -- 'too_large' | 'binary_or_encoding_error' | 'generation_failed'
    detail       TEXT,              -- サイズ超過量、エラーメッセージなど
    recorded_at  TEXT NOT NULL      -- ISO8601（JST）
);
```

- `skip_records` は「要約できなかったファイル」を横断的に記録するテーブル。理由（`reason`）ごとに `too_large`（サイズ上限超過）/ `binary_or_encoding_error`（バイナリ判定・エンコーディング推定失敗）/ `generation_failed`（1回のリトライ後もaim CLI呼び出しが失敗）の3種を持つ
- あるファイルが `generate` で正常に要約できた場合、そのファイルの `skip_records` 行は削除する（スキップ理由が解消されたことを反映するため）
- スキップ理由が解消されない限り、`generate` を再実行するたびに同じ行が `recorded_at` 更新のうえ残り続ける

## CLIコマンド

### `aim-summarize generate [paths...] [--force] [--dry-run]`

- `paths` を省略した場合、`.aim-use/config.toml` が見つかるリポジトリルート配下全体が対象
- 対象ファイルを列挙 → `.gitignore` + `config.toml` の `include`/`exclude` でフィルタ
- 列挙した各ファイルに対して、以下の順でスキップ判定を行う
  1. ファイルサイズが `max_file_size_bytes` を超過 → `skip_records` に `too_large` として記録しスキップ
  2. バイナリ判定・エンコーディング推定に失敗 → `skip_records` に `binary_or_encoding_error` として記録しスキップ
  3. 上記に該当しなければ、ファイル内容のハッシュを計算しDB内の既存レコードと比較
     - ハッシュが一致 → 何もせず次のファイルへ（既存の要約を維持）
     - ハッシュが不一致、または新規ファイル → aim CLI で要約を生成し、成功すれば `file_summaries` へ upsert（既存の `skip_records` があれば削除）
       - aim CLI呼び出しが失敗した場合は1回だけリトライする
       - リトライ後も失敗した場合は `skip_records` に `generation_failed`（エラーメッセージ付き）として記録し、次のファイルへ進む（generate全体は中断しない）
- `--force` 指定時は、ハッシュが一致していても対象全件を再生成する（サイズ超過・バイナリ判定失敗によるスキップは `--force` でも対象外のまま）
- DB上には存在するがディスク上から消えているファイルのレコードは、generate実行時に `file_summaries` / `skip_records` の両方から自動的に削除する
- `--jobs` は `config.toml` の `jobs`（2〜10の範囲）を使用する。CLI引数での上書きは行わない（設定ファイルで一元管理する方針のため）。aim CLI 呼び出しはサブプロセス起動＋ネットワークI/O待ちが支配的なため、並列化で全体時間を短縮する
- `--dry-run` 指定時は実際にAI呼び出しをせず、新規生成/再生成/維持/各スキップ理由ごとの件数と対象ファイル一覧のみ表示する
- 実行完了時には、生成件数・維持件数・スキップ件数（理由別）のサマリーを標準出力に表示する

### `aim-summarize get [paths...] [--format markdown|json]`

- DBから読むだけで、AI呼び出しは発生しない
- `paths` を省略した場合はDB全件が対象
- `paths` にディレクトリを含む場合、DB内でそのディレクトリ配下に該当する `file_path` を展開する
- DBに要約が存在しないパスが指定された場合は「要約未生成」として出力に明示し、非ゼロ終了はしない

### 出力フォーマット

Markdown（デフォルト）:

```markdown
## src/foo.py

<summary text>

## src/bar.py

<summary text>
```

JSON（`--format json`）:

```json
[
  {
    "file_path": "src/foo.py",
    "summary": "...",
    "model": "openai/gpt-oss-120b:free",
    "generated_at": "2026-07-10T12:00:00+09:00",
    "content_hash": "..."
  }
]
```

## 要約生成プロンプト（`summarizer.py` に固定で埋め込む）

```
以下はリポジトリ内のファイル `{file_path}` の内容です。このファイルの要約を日本語で作成してください。

含めるべき観点:
- このファイルの役割・責務
- 主要な関数/クラス/エクスポートとその概要
- 他ファイルとの依存関係で注目すべき点
- 変更時に注意すべき点（あれば）

出力は300〜500文字程度の簡潔な文章または箇条書きでお願いします。コードブロックや前置きは不要です。

---
{file_content}
```

## 開発者向けワークフロー

1. `uv tool install --editable tools/aim-use/aim-summarize` でインストール（`aim` 同様グローバルCLIとして。`pip install -e` の代替）
2. 対象リポジトリのルートに `.aim-use/config.toml` を作成（`config.toml.example` をコピー）
3. 対象リポジトリの `.gitignore` に `.aim-use/summaries.db` を追記
4. `aim-summarize generate` を実行し、要約DBを構築（初回は全ファイル、以降は差分のみ）
5. 開発着手前に `aim-summarize get src/foo/ src/bar/ --format markdown` などで対象範囲の全体像を把握する
6. ファイルを変更したら、区切りの良いタイミングで再度 `generate` を実行し、要約を最新化する（v1では手動）

## v1スコープ外（将来検討）

- `generate` の自動トリガー（lefthook の pre-commit/pre-push フック、CI連携）
- DBのGit管理・チーム間共有運用
- 変更量（diff行数など）に応じた再生成要否の柔軟な判定
- ディレクトリ単位の集約要約（現状はファイル単位のみ）
- 要約プロンプトの `config.toml` でのカスタマイズ

## オープンな疑問点（実装時に要検討）

- `max_file_size_bytes` のデフォルト値（例では200KBを仮置き。適切な値は実際のリポジトリで試して調整）
- `skip_records` の内容を開発者が確認する手段（v1では `generate` 実行時のサマリー表示のみ。専用の `aim-summarize errors` 的なサブコマンドが将来必要かは要検討）
