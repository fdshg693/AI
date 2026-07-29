# skill-deploy

このリポジトリ内のスキル等のフォルダ/ファイルを、`config/` の設定に従って複数の配置先へコピーする
CLIツール。「スキル」専用ではなく、フォルダ単位・ファイル単位の汎用コピーとして動く。

## インストール

```bash
uv tool install --editable integrations/scripts
```

インストール後は `skill-deploy` コマンドが PATH 上でどこからでも使える。リポジトリを clone した
まま試すだけなら `uv run --project integrations/scripts skill-deploy ...` でも実行できる。

## 使い方

```bash
# 設定に従って何がどこにコピーされるかを確認する（ファイルシステムには一切書き込まない）
skill-deploy plan

# 実際にコピーを実行する
skill-deploy apply

# 特定のターゲットだけを対象にする（複数指定可）
skill-deploy apply --only my-target --only other-target

# case.yaml に定義済みのセット一覧を確認する
skill-deploy list-sets
```

`--config-dir` / `--repo-root` で、既定のディレクトリ（後述）を上書きできる。

## 設定ファイル（`config/`）

`config/` 配下の `*.yaml` / `*.yml` をすべて読み込んでマージする。**配置先ごとに設定ファイルを
分ける必要はない**——1ファイルに配置先（`targets`）を複数書いてよいし、好きな粒度でファイルを
分割してもよい（例: ツールごと、導入先ごとなど）。`case.yaml` だけは予約名で、`targets` ではなく
名前付きセット（`sets`）を定義する特別なファイルとして扱われる。

### `config/case.yaml` — 名前付きセットの定義

```yaml
sets:
  my-tools-skills:
    - claude-plugins/my-tools/skills/* # glob可（配下のスキルをまとめて指定）
  coding-core:
    - claude-plugins/coding/skills/testing
    - claude-plugins/coding/skills/systematic-debugging
```

ここで定義したセットは、他の設定ファイルの `items:` から `@セット名` として参照できる（後述）。
セットの中で別のセットを `@other-set` として参照することもできる（循環参照はエラーになる）。

### `config/*.yaml`（`case.yaml` 以外）— 配置先の定義

```yaml
targets:
  - name: vscode-user-skills # 省略可（省略時は "<ファイル名>#<連番>"）
    dest: ~/.claude/skills
    items:
      - "@my-tools-skills" # case.yaml のセットを展開
      - claude-plugins/coding/skills/testing # 単一パスも直接指定できる
      - claude-plugins/my-tools/skills/* # globも直接指定できる

  - name: another-repo-templates
    dest: C:/path/to/other-repo/.claude/skills
    items:
      - "@coding-core"
```

- `dest` は `~`・環境変数を展開する。相対パスはリポジトリルート基準、絶対パスはそのまま使う。
- `items` の各エントリは次のいずれか:
  - `@セット名` — `case.yaml` の `sets` を展開する
  - グロブパターン（`*` `?` `[]` を含む文字列）— リポジトリルート基準で `Path.glob()` により展開
    する（`**` による再帰も可）。一致が0件の場合はエラーにはせず警告のみ表示する
  - 通常のパス — リポジトリルート基準の単一ファイル/フォルダ。存在しない場合はエラー
- 同一ターゲット内で同じコピー元が複数回解決されても、コピーは1回だけ行われる（重複除去）。

## コピーの挙動

- コピー元がフォルダの場合: `dest/<フォルダ名>/` へクリーンコピーする。既存の同名フォルダは
  一度削除してから配置し直すため、コピー元に無くなったファイルが配置先に残り続けることはない。
- コピー元がファイルの場合: `dest/<ファイル名>` として配置する（既存ファイルは上書き）。
- `__pycache__` / `*.pyc` / `.pytest_cache` / `*.egg-info` / `.env` は既定で除外される。
  `.env` に実際の秘密情報が入っている前提のため、コピー元フォルダにこれが含まれていても配置先へは
  伝播しない（`.env.example` 等はそのままコピーされる）。それ以外の機密ファイルをフォルダに
  含めている場合は、配置対象のフォルダ自体から除外しておくこと（本ツールはフォルダ単位の
  汎用ミラーであり、それ以上のフィルタリングは行わない）。

## 動作確認用サンプル（`config/example.yaml`）

`dest: temp/skill-deploy-example/...` としているため、`skill-deploy apply` をそのまま実行しても
リポジトリ外には何も書き込まれない（`temp/` は gitignore 済み）。実際の配置先を追加する場合は、
この形式を真似て `config/` 配下に好きな名前で `*.yaml` を追加すればよい。

## テスト

```bash
uv sync && uv run pytest integrations/scripts
```
