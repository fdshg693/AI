---
paths:
  - "tools/aim-use/aim-ask/**"
---

# aim-ask — 複数ファイルへの並列AIプロンプト投げツール

**関連スキル: `claude-plugins\my-tools\skills\aim-ask`**

`aim` パッケージ（`tools/aim`、`aim_cli` モジュール）をライブラリとして直接インポートし、複数ファイルに同一プロンプトを非同期（`asyncio`）で並行投入するステートレスなCLIツール。`aim-summarize` と異なりDBへの永続化は行わず、実行のたびにその場で結果を返す。設計の背景・決定事項は [PLAN.md](PLAN.md) を参照。

CLIオプション・設定ファイル形式・挙動を変更した場合は、上記スキルの `SKILL.md` も同じ変更の中で更新すること（スキル側は自動追随しない）。

## インストール

`OPENROUTER_API_KEY` の設定が済んでいることが前提（[tools/aim/README.md](../../aim/README.md) のセットアップ手順を参照）。`aim-cli` パッケージはグローバルインストール不要（本ツールの依存パッケージとして自動的に解決される）。

グローバルCLIとして使う場合は `uv tool install --editable`（`pip install -e` の代替）でエディタブルインストールする。

```bash
uv tool install --editable tools/aim-use/aim-ask
```

インストール後は `aim-ask` コマンドが PATH 上でどこからでも使える。

## 使い方

```bash
# 指定したファイルをデフォルトプロンプト（要約）で並列に問い合わせる
aim-ask src/foo.py src/bar.py

# プロンプトを動的に上書きする（全ファイルに同一のプロンプトが使われる）
aim-ask src/foo.py src/bar.py --prompt "このファイルのバグを指摘してください"

# 使用モデル・並列数を指定する
aim-ask src/foo.py --model glm-5.2 --jobs 2

# JSON形式で出力する
aim-ask src/foo.py src/bar.py --format json
```

### 挙動

- 相対パスはカレントディレクトリ（CWD）基準で解決する
- 各ファイルにつき1回のAI呼び出しを行う（複数ファイルを1回の呼び出しにまとめることはしない）
- 全ファイルへの呼び出しは `--jobs` で指定した並列数（既定4）で同時実行される
- 与えられるプロンプトはファイルごとに変化せず、全ファイルに同一のものが使われる（ファイルパスはプロンプト文言に埋め込まれない）
- 存在しないパス・ディレクトリ・バイナリ/デコード不能ファイル・AI呼び出し失敗（1回リトライ後も失敗）は、そのファイルだけ失敗として記録され、他ファイルの処理は継続する
- 出力は入力順を維持し、各要素は `path`（指定したパス文字列そのまま）と `resolved_path`（解決後の絶対パス）の両方を持つため、応答とファイルの対応が常に明確になる

## 設定ファイル（`.aim-use/aim-ask.toml`、省略可）

```toml
model = "gpt-120b"
jobs = 4

prompt = """\
以下のファイル内容を日本語で要約してください。
...
"""
```

- カレントディレクトリから親方向に `.aim-use/aim-ask.toml` を探索する。見つからない場合はエラーにせず、組み込みデフォルト（要約プロンプト / `gpt-120b` / `jobs=4`）を使う
- `--prompt` / `--model` / `--jobs` のCLI引数は、設定ファイルの値より優先される
- `model` には `tools/aim` の `aim --list-models` で表示される略記のいずれかを指定する
- `jobs` は1〜10の範囲でのみ指定可能

## 出力形式

### Markdown（既定）

```markdown
## src/foo.py

（応答本文、またはエラー時は「⚠ エラー: ...」）

## src/bar.py

（応答本文）
```

### JSON（`--format json`）

```json
[
  {
    "path": "src/foo.py",
    "resolved_path": "/abs/path/to/src/foo.py",
    "success": true,
    "response": "...",
    "error": null
  }
]
```

## ファイル構成

```
tools/aim-use/aim-ask/
├── README.md            # 本ファイル
├── PLAN.md              # 実装プラン
├── pyproject.toml        # パッケージ定義 + console script (aim-ask)
├── .gitignore
├── config.toml.example   # 対象リポジトリにコピーする設定ファイルのサンプル（省略可）
└── aim_ask/
    ├── __init__.py
    ├── cli.py             # argparseエントリポイント
    ├── config.py           # .aim-use/aim-ask.toml の探索・読み込み（省略可）
    ├── asker.py             # aim ライブラリ呼び出し（非同期）+ デフォルトプロンプト
    └── formatter.py           # markdown / json 整形
```
