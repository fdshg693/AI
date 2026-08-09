# Step1 調査: 詳細結果

> [../01-uv-workspace-source-research.md](../01-uv-workspace-source-research.md) の実行結果。本体には要約のみを残し、実行コマンド・生の出力はここに置く。

## 実行したコマンドと結果

### 1. `aim-ask` を単体 `uv build` → wheel メタデータ確認

```
cd tools/aim-use/aim-ask && uv build
```

生成された `aim_ask-0.1.0-py3-none-any.whl` の `METADATA`:

```
Requires-Dist: aim-cli
```

バージョン指定・URLともに埋め込まれておらず、`tool.uv.sources` の workspace 参照はビルド後の配布物には一切反映されない（`[project.dependencies]` に書いた素のパッケージ名がそのまま出力される）ことを確認した。

### 2. workspace外の一時venvにこのwheelを単体インストール

```
uv venv test_venv_outside
uv pip install --python test_venv_outside/Scripts/python.exe dist/aim_ask-0.1.0-py3-none-any.whl
```

結果: **エラーにならず「成功」してしまった**。ただし解決された `aim-cli==2.7.4` は、このリポジトリの `tools/aim`（`aim_cli` モジュール、OpenRouter経由のモデル呼び出しCLI）とは全くの別物で、PyPI上に実在する [Aim](https://aimstack.io/)（MLOps向け実験管理・トラッキングツール）の配布物だった（`aimrecords` / `flask` / `tensorboard` / `grpcio` / `numpy` 等、大量の無関係な依存が同時にインストールされた）。

事前の仮説は「PyPI上に同名の別物が存在しない限りエラーになる」だったが、実際には **PyPI上に同名の別物（`aim-cli`）が実在したため、依存解決自体は静かに成功してしまう** ことが判明した。想定より悪いケース（dependency confusion）。

### 3. ランタイム動作確認

```
python -c "import aim_cli"
# → ModuleNotFoundError: No module named 'aim_cli'

aim-ask --help
# → ModuleNotFoundError: No module named 'aim_cli'（aim_ask/cli.py の `from aim_cli import ...` で失敗）
```

PyPI版 `aim-cli` パッケージは `aim_cli` という importable モジュールを提供しない（別のトップレベルパッケージ構成）ため、`pip install` は成功してもコマンド実行時に確実に壊れる。「エラーなくインストールできたように見えて、実際には動かない」という、単純なインストール失敗より発見しづらい壊れ方をする。

`aim-summarize` は `aim-ask` と依存構造が完全に同一（`dependencies = ["aim-cli"]` のみ、`tool.uv.sources` で `aim-cli = { workspace = true }`）のため、個別に再実行はしていないが同じ結論が適用される。

### 4. `my-agents` を単体 `uv build` → wheel メタデータ確認 + 単体インストール

```
cd tools/my-agents && uv build
```

`METADATA` の該当行:

```
Requires-Dist: mslearn-cli
Requires-Dist: tav-cli
```

こちらも workspace 参照はビルド後の配布物に反映されない。workspace外の一時venvに単体インストールを試みたところ:

```
uv pip install --python .../python.exe dist/my_agents-0.1.0-py3-none-any.whl
```

```
× No solution found when resolving dependencies:
  ╰─▶ Because mslearn-cli was not found in the package registry and
      my-agents==0.1.0 depends on mslearn-cli, ...
```

`mslearn-cli` / `tav-cli` はPyPI上に同名パッケージが存在しないため、こちらは仮説通り明確な解決エラーで失敗した（`aim-ask`/`aim-summarize` のような静かな誤解決は起きない）。

## 検証時の後片付け

`uv build` はリポジトリルート直下の `dist/`（gitignore対象、`dist/.gitignore` が自動生成される）に出力された。検証終了後、`dist/` ディレクトリごと削除済み。作業用venvはスクラッチパッド配下に作成しており、リポジトリには影響なし。

## 参照ドキュメント

- https://docs.astral.sh/uv/concepts/projects/workspaces/ — `tool.uv.sources` の workspace 参照とワークスペースメンバー間の編集可能依存について記載はあるが、「`uv build` が生成する wheel メタデータに反映されるか否か」への明示的な言及は見当たらなかった。今回の結論は上記の実機検証（1〜4）に基づく。

## 後続ステップ（Step2）への引継ぎ

Step2は以下を前提として書く:

1. リリース対象は `aim-cli` / `tav-cli` / `mslearn-cli` / `ctx7-cli` の4パッケージに確定（`aim-ask` / `aim-summarize` / `my-agents` はworkspace依存を持つため対象外）。
2. 対象外の3パッケージについて、`tools/install/AGENTS.md` 等のドキュメントに「単体インストール不可」の理由を明記する際は、単に「失敗する」ではなく **`aim-ask`/`aim-summarize` は依存名 `aim-cli` がPyPI上の無関係な別パッケージ（Aim実験管理ツール）に静かに誤解決され、実行時に初めて壊れる** という具体的なリスクを書くこと（`my-agents` は素直にインストールエラーになる、という対比も明記できるとよい）。
3. `tools/install/justfile` に `aim-ask-git` / `aim-summarize-git` / `my-agents-git` のようなレシピを追加してはならない（意図せず壊れた、あるいは無関係なパッケージを掴むインストール手段を公式に提供してしまうため）。
