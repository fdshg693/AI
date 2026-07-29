---
name: aim-ask
description: 指定した複数ファイルまたはディレクトリに同一プロンプトを並列に投げ、パスと応答の対応付きで結果を返すステートレスなCLIツール`aim-ask`の使い方を説明する。複数ファイルやスキルフォルダへ同じ質問（要約・バグ指摘など）を一括で投げたい場合に使う。DBへの永続化が必要な場合は`aim-summarize`を使う。
# 前提条件: `aim-ask`コマンドがPATH上にインストール済み（`uv tool install --editable tools/aim-use/aim-ask`）であり、OPENROUTER_API_KEYが設定済み（aim-cliが内部で要求）であること。このスキルはインストール・セットアップは一切行わない
# このスキルの設計意図・前提条件の背景は tools/aim-use/aim-ask/README.md および PLAN.md 参照（人間のメンテナ向け）
meta:
  requires_repo_tools: none
  requires_env: OPENROUTER_API_KEY
  dependencies: aim-cli, OPENROUTER_API_KEY
  requires_install: uv tool install --editable tools/aim-use/aim-ask
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

## 前提条件

- `aim-ask`コマンドが既にインストールされ、PATH上で実行可能であること
- `OPENROUTER_API_KEY`が環境変数または`tools/aim/.env`で設定済みであること
- 未インストール・未設定の場合はこのスキルでは対処しない。エラーが出た場合はユーザーに`tools/aim-use/aim-ask/README.md`のセットアップ手順を案内する

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

# スキルフォルダ全体（ツリーと各ファイル内容）を1回で問い合わせる
aim-ask claude-plugins/my-tools/skills/aim-ask --prompt "このスキルの役割と注意点を要約してください"

# ディレクトリ入力で、内容を渡すファイルをSKILL.md/README.mdだけに絞る（それ以外はパスのみツリーに残す）
aim-ask claude-plugins/my-tools/skills/aim-ask --full-content-names "SKILL.md,README.md" --prompt "..."
```

| オプション             | 必須 | 説明                                                                                                                         |
| ---------------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------- |
| `paths`                | ○    | 対象ファイルまたはディレクトリパス（複数指定可、相対パスはCWD基準で解決）                                                    |
| `--prompt`             | -    | AIに渡すプロンプト文字列。省略時は設定ファイル/組み込みデフォルト（要約）                                                    |
| `--model`              | -    | 利用するモデルの略記（`aim --list-models`参照）。省略時は設定ファイル/組み込みデフォルト                                     |
| `--jobs`               | -    | 並列実行数（1〜10）。省略時は設定ファイル/組み込みデフォルト（4）                                                            |
| `--format`             | -    | `markdown`（既定）または`json`                                                                                               |
| `--full-content-names` | -    | ディレクトリ入力時、内容を含めるファイル名のカンマ区切り指定（例`SKILL.md,README.md`）。省略時は配下の全ファイル内容を含める |

## 挙動

- 各ファイルにつき1回のAI呼び出しを行う（複数ファイルを1回の呼び出しにまとめることはしない）
- ディレクトリは配下の相対パスのツリー listing と各ファイル内容を1つにまとめ、ディレクトリ1つにつき1回のAI呼び出しを行う
- `--full-content-names`を指定した場合、ディレクトリ配下でファイル名が一致するものだけ内容を含め、それ以外はツリー listing 上のパス（`[内容省略（対象外ファイル）]`の注記付き）のみになる。大きな参照ドキュメント一式を抱えるディレクトリで、SKILL.md/README.mdなど一部ファイルの内容だけ判断材料にしたい場合に使う
- `.git`、`__pycache__`、`node_modules`、`.venv`、`venv` はディレクトリ入力時に走査から除外される
- 与えられるプロンプトはファイルごとに変化せず、全ファイルに同一のものが使われる（ファイルパスはプロンプト文言に埋め込まれない）
- 全ファイルへの呼び出しは`--jobs`で指定した並列数で同時実行される
- 存在しないパス・単一指定のバイナリ/デコード不能ファイル・AI呼び出し失敗（1回リトライ後も失敗）は、そのパスだけ失敗として記録され、他パスの処理は継続する
- ディレクトリ内のバイナリ/デコード不能ファイルはツリー listing に含め、「読み込みスキップ」と注記したうえで内容だけを除外する。総サイズの上限・切り詰めは行わない
- 出力は入力順を維持し、各要素は`path`（指定したパス文字列そのまま）と`resolved_path`（解決後の絶対パス）の両方を持つため、応答とファイルの対応が常に明確になる

## 設定ファイル（`.aim-use/aim-ask.toml`、省略可）

```toml
model = "gpt-120b"
jobs = 4

prompt = """\
以下のファイル内容を日本語で要約してください。
...
"""
```

- カレントディレクトリから親方向に`.aim-use/aim-ask.toml`を探索する。見つからない場合はエラーにせず、組み込みデフォルト（要約プロンプト / `gpt-120b` / `jobs=4`）を使う
- `--prompt`/`--model`/`--jobs`のCLI引数は、設定ファイルの値より優先される
- `model`には`aim --list-models`で表示される略記のいずれかを指定する（詳細は`aim-cli`スキル参照）
- `jobs`は1〜10の範囲でのみ指定可能。範囲外は起動時エラー

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

## エラー時の挙動

`--jobs`が範囲外、モデル略記が不正な場合はエラーメッセージを標準エラー出力に表示し、非ゼロで終了する。個別ファイルのパスエラー・読み込み失敗・AI呼び出し失敗は全体を止めず、そのファイルの`success: false`/`error`として結果に含まれる。
