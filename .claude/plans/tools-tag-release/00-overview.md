# my-tools CLI群のタグ+Releaseによるバージョン管理 実装プラン - 概要

## 要件

- `claude-plugins/my-tools` 配下のスキルが前提とする各CLI（`tools/aim`, `tools/tav-cli`, `tools/mslearn`, `tools/ctx7`, `tools/aim-use/aim-ask`, `tools/aim-use/aim-summarize`, `tools/my-agents`）について、mainブランチへのバージョン変更マージをトリガーに、パッケージごとの git タグ（`<pyprojectのname>-v<version>`）と GitHub Release を自動発行する CI を導入する。
- 目的は、モノレポ全体を clone しなくても `uv tool install "git+<repo_url>@<tag>#subdirectory=tools/<dir>"` で特定バージョンをピン留めインストールできるようにすること（現状の `tools/install/justfile` の `aim-git`/`tavily-git` は常に最新mainを追う方式で、バージョン固定ができない）。
- リリースはスケジュール実行ではなく「バージョン変更検知」でトリガーする（前回のやり取りで合意済み — コード変更が無くてもタグだけ増えるスケジュールリリースは無意味なため）。

## 実装ステップ

1. ✅ [01-uv-workspace-source-research.md](01-uv-workspace-source-research.md) — `[tool.uv.sources] xxx = { workspace = true }` を使う3パッケージ（`aim-ask`, `aim-summarize`, `my-agents`）が、workspace外（`uv build`単体実行 / git subdirectory単体install）でも正しくインストール可能かを検証し、今回のリリース自動化の対象パッケージ範囲を確定する
2. ✅ [02-release-workflow-implementation.md](02-release-workflow-implementation.md) — Step1の結論をもとに、タグ+Release自動発行のGitHub Actionsワークフローと、ピン留めインストール手順のドキュメントを実装する

## 主要な決定事項

| 決定                                                                                                                                                                             | 理由                                                                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| リリースは「バージョン差分検出」でトリガーする（スケジュール実行はしない）                                                                                                       | コード変更が無くてもタグが増えるスケジュールリリースは無意味。バージョンが上がった時だけリリースする方が利用者にとって意味のある単位になる                                                                                                                                    |
| タグ名は `pyproject.toml` の `[project] name` を接頭辞にする（例: `aim-cli-v0.1.0`）                                                                                             | ビルドされるwheelファイル名（`aim_cli-0.1.0-...`）と対応が付き、ディレクトリ名やjustfileのレシピ名（`tav-cli`ディレクトリだが既存レシピ名は`tavily-git`等、パッケージ名と不一致な箇所がある）に依存しない一意なキーになる                                                     |
| リリース対象パッケージの最終範囲はStep1の検証結果に従う（暫定仮説: workspace内の兄弟パッケージに依存しない4パッケージ = `aim-cli`, `tav-cli`, `mslearn-cli`, `ctx7-cli` が有力） | `tool.uv.sources`によるworkspace内解決は、`uv sync`等のworkspaceコマンド専用でビルド済みwheelのメタデータには反映されない可能性が高く、依存パッケージ（`aim-cli`等）がPyPI上に存在しないため単体インストールが壊れる懸念がある。実際の挙動をStep1で確認してから対象を確定する |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `.github/workflows/tool-release.yml`

### 変更

- `tools/install/AGENTS.md`

## ルール更新ポイント

- `tools/install/AGENTS.md`（既存ファイルへの追記。対象パスに変更が無いためフロントマター不要、セクション見出しで対象を示す単一ファイル方式）: パッケージごとのタグ+Release運用（トリガー条件・タグ命名規則・ピン留めインストール手順・対象パッケージ一覧）を追記
