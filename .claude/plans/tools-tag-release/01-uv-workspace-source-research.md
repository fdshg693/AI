# Step 1: uvワークスペース依存の単体インストール挙動検証

✅完了 — 詳細結果は [progress/01-research-results.md](progress/01-research-results.md) 参照

## やること

`aim-ask` / `aim-summarize` / `my-agents` の `pyproject.toml` は `[tool.uv.sources]` で兄弟パッケージ（`aim-cli`, `mslearn-cli`, `tav-cli`）を `{ workspace = true }` として参照している。この解決が uv workspace コンテキスト外（`uv build` 単体実行、または `git+<url>#subdirectory=` 経由の単体 install）でも有効かを検証し、Step2 のリリース対象パッケージ範囲（CIワークフローの matrix）を確定する。

## 読むべきファイル・実行推奨Grep

**現状の未検証の根拠を裏取りするため（優先度: 高）**

- 読む: `tools/aim-use/aim-ask/pyproject.toml` / `tools/aim-use/aim-summarize/pyproject.toml` / `tools/my-agents/pyproject.toml` の `[tool.uv.sources]` — workspace参照の対象を再確認
- Grep: `tools/install/justfile` 内の `-git` 接尾辞のレシピ — `aim-git` / `tavily-git`（`aim-cli`・`tav-cli`、いずれも workspace 依存を持たない）にしか存在せず、`aim-ask` / `aim-summarize` / `my-agents` 向けの `-git` レシピが無いことを確認する（意図的に避けられている可能性の裏取り）

**uvの実際の挙動を手元で確認するため（優先度: 高）**

- 実行: `cd tools/aim-use/aim-ask && uv build` → 生成された `dist/*.whl` を展開（`python -m zipfile -e` 等）し、`*.dist-info/METADATA` の `Requires-Dist: aim-cli` 行にバージョン指定やURLが埋め込まれているか確認する
- 実行: 上記wheelを、この workspace 外の一時venv（例: `uv venv <tmp> && uv pip install --python <tmp>/... dist/*.whl`）に単体インストールしてみて、`aim-cli` の解決に失敗する（PyPI上に同名の別物が存在しない限りエラーになる）ことを実際に再現する
- 参照: uv公式ドキュメントの workspace / `tool.uv.sources` セクション（`https://docs.astral.sh/uv/concepts/projects/workspaces/` 等）で、workspaceソースの解決範囲（`uv sync`/`uv lock` 等 workspace コマンド限定か否か）が明記されているか確認する

## 決定事項・注意点／落とし穴

検証の結果、仮説は概ね確認された（ただし想定より悪いケースが1つあった）。

- `tool.uv.sources` の workspace 解決は `uv build` が生成する wheel のメタデータには一切反映されない（`Requires-Dist` は `[project.dependencies]` の素のパッケージ名がそのまま出力される）ことを実機で確認済み。
- **`my-agents`**（依存: `mslearn-cli`, `tav-cli`）は、workspace外の単体インストール時に「PyPI上に見つからない」という明確なエラーで失敗する（仮説どおり）。
- **`aim-ask` / `aim-summarize`**（依存: `aim-cli`）は、より悪いケースだった。PyPI上に無関係な同名パッケージ（Aim、MLOps向け実験管理ツール）が実在するため、単体インストール自体はエラーなく「成功」してしまう。しかし実行時に `ModuleNotFoundError: No module named 'aim_cli'` で確実に壊れる（誤ったパッケージを静かに掴む dependency confusion 寄りのリスク）。詳細は [progress/01-research-results.md](progress/01-research-results.md) 参照。
- 上記により、Step2のリリース対象は「workspace内の兄弟パッケージに依存しない4パッケージ」（`aim-cli`, `tav-cli`, `mslearn-cli`, `ctx7-cli`）に確定。`aim-ask` / `aim-summarize` / `my-agents` は今回のスコープ外とする（別途、依存を直接 git 参照に切り替える等の対応が必要になるが、それは本プランでは扱わない）。
- Step2でドキュメント化する際は、`aim-ask`/`aim-summarize`が「単に失敗する」のではなく「無関係なパッケージを誤って掴んだ上で実行時に壊れる」点を明記し、`tools/install/justfile`に対象外3パッケージ向けの`-git`レシピを追加しないことも明記する。

## ルール更新ポイント

なし（このステップは調査のみ。結論の反映はStep2で行う）。
