---
paths:
  - "tools/install/**"
---

# ツールインストール方法

各ツールのインストール方法をまとめる。同階層の `justfile` から実行可能。

```bash
just aim-local   # aim CLI (tools/aim) をエディタブルインストール
just tavily-local  # tav-cli の tav CLI をエディタブルインストール
just cline-personal-info  # cline-personal-info plugin (tools/cline-wrapper, cline-plugins/meta) を Cline にインストール
```

APIキー設定など、インストール後のセットアップは各ツールの README を参照（例: `tools/aim/README.md`、`tools/tav-cli/README.md`、`integrations\CLINE.md`）。

`cline-personal-info` は内部で Git Bash 経由に `cline plugin install` を叩く。PowerShell/cmd から `cline plugin install` を直に打つと `error: ENOENT: no such file or directory, uv_spawn 'npm'` で失敗するため（詳細は `integrations\CLINE.md`）。

## タグ+Releaseによるバージョン管理

対象パッケージについて、`.github/workflows/tool-release.yml` が main ブランチへの push をトリガーに、パッケージごとの git タグと GitHub Release を自動発行する。スケジュール実行ではなく「`pyproject.toml` のバージョンが上がった」ときだけ発行される（対象タグが既に存在する場合はサイレントにスキップ）。

- タグ命名規則: `<pyprojectのnameフィールド>-v<version>`（例: `aim-cli-v0.1.0`）
- 対象パッケージ（4つ。ワークスペース内の兄弟パッケージに依存しないもののみ）

  | パッケージ名  | ディレクトリ    |
  | ------------- | --------------- |
  | `aim-cli`     | `tools/aim`     |
  | `tav-cli`     | `tools/tav-cli` |
  | `mslearn-cli` | `tools/mslearn` |
  | `ctx7-cli`    | `tools/ctx7`    |

- `aim-ask` / `aim-summarize` / `my-agents` は対象外。`[tool.uv.sources]` で workspace 内の兄弟パッケージ（`aim-cli`・`mslearn-cli`・`tav-cli`）を参照しているが、この解決は `uv build` が生成する wheel には反映されず、workspace 外で単体インストールすると壊れるため。`my-agents` は依存パッケージ名（`mslearn-cli`・`tav-cli`）が PyPI 上に存在せず素直にインストールエラーになるが、`aim-ask`/`aim-summarize` は依存名 `aim-cli` が PyPI 上の無関係な別パッケージ（[Aim](https://aimstack.io/) という MLOps 向け実験管理ツール）に静かに誤解決されてしまい、インストール自体はエラーなく完了した上で実行時に `ModuleNotFoundError` で壊れる（dependency confusion）。このため `justfile` にもこの3パッケージ向けの `-git` レシピは意図的に追加していない。

- ピン留めインストール（対象4パッケージのみ）:

  ```bash
  uv tool install "git+https://github.com/fdshg693/AI.git@<tag>#subdirectory=tools/<dir>"
  # 例
  uv tool install "git+https://github.com/fdshg693/AI.git@aim-cli-v0.1.0#subdirectory=tools/aim"
  ```

  `tools/<dir>` は上表の「ディレクトリ」列を使う。`justfile` の `*-git` レシピ（常に最新mainを追う）と異なり、`@<tag>` を固定することで特定バージョンにピン留めできる。
