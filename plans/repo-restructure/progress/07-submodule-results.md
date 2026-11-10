# 07 実行記録（サブモジュールへの切り出し）

## 作ったリポジトリ（すべて public、2026-11-10）

| パス            | リポジトリ                                                              | 切り出し時の初回コミット                           |
| --------------- | ----------------------------------------------------------------------- | -------------------------------------------------- |
| `site/`         | [fdshg693/AI-site](https://github.com/fdshg693/AI-site)                 | `14b31b7`                                          |
| `agent-compat/` | [fdshg693/AI-agent-compat](https://github.com/fdshg693/AI-agent-compat) | `e8f0efc`                                          |
| `tools/`        | [fdshg693/AI-tools](https://github.com/fdshg693/AI-tools)               | `9d9ccea`                                          |
| `skills/`       | [fdshg693/AI-skills](https://github.com/fdshg693/AI-skills)             | `221547a`                                          |
| アンブレラ      | [fdshg693/AI](https://github.com/fdshg693/AI)                           | `4bb7938`（ローカルの `master` を `main` へ push） |

## コミット（アンブレラ）

| コミット              | 内容                                                                                                                                                             |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `5890dd4`             | `maintenance/scripts/repo_git.py`: ステージ済み一覧・`git show`・`git add` をサブモジュールの中まで（アンブレラ相対のパスで）。gitlink で集約生成物を再生成      |
| `9cf696b` + `4c22cbf` | skill-tools `GitHubSource` がサブモジュールを辿る（`.gitmodules` の URL → 記録 SHA のツリー）。解決できなければエラー。`GITHUB_TOKEN` 対応                       |
| `1bf7ca3`             | site を切り出し。`.gitmodules`、`maintenance/lefthook/submodule.yml`、`just sub-*`、サイト系ワークフローの `submodules: recursive` と gitlink の `paths:`        |
| `97863d2`             | agent-compat を切り出し。アンブレラの lefthook からフック再生成の glob を外す（サブモジュール側で走る）                                                          |
| `09d6589` + `a372b45` | skill-tools の local source がサブモジュールの中を列挙する（`git ls-files` を各サブモジュールで実行）。`self-update` の既定を AI-tools に、旧 URL の利用者も移す |
| `099ebb3`             | AI-tools 用の `tool-release.yml`（アンブレラでは不活性）                                                                                                         |
| `2e2e0e9` + `2e5506d` | tools を切り出し。marketplace 生成器が `git-subdir`／`github`+`path` を出す（`plugin_source.py`）。git インストール URL、docs、`tool-release.yml` の移動         |
| `e85d38a`             | skills を切り出し。marketplace 再生成、Codex・Claude Code の導入手順                                                                                             |
| `cb2f65b`             | 生成器の書き込みを LF に（Windows で CRLF を書くたびにサブモジュールが変更ありに見えた）                                                                         |
| `3565a5d`             | `umbrella-check.yml`（集約生成物の再生成漏れと `uv lock --check`）、triage の checkout にサブモジュール、`.gitignore` の不要行                                   |
| `4bb7938`             | repo-layout（サブモジュール節）、committing スキル（2 段階コミット）、lefthook-automation、gh-actions-lifecycle、README・AGENTS.md・CONTRIBUTING                 |

サブモジュール側: AI-site に `59522ec`（サイトの GitHub リンクをサブモジュールのリポジトリへ。`skills-site/scripts/github-url.mjs`）。

## 決めたこと

- **切り出し方法**: `git filter-repo` は未導入なので、Git 標準の `git subtree split --prefix=<dir>` で履歴付きのブランチを作り、スクラッチの clone でリポジトリ単位のファイル（`.gitignore`・`.gitattributes`・`LICENSE`・`lefthook.yml`、README が無ければ README）を初回コミットに足した。05 で移動する前の履歴は付かない（アンブレラには残る）。
- **アンブレラ側の置き換え**: ignore 対象を列挙 → フォルダごとリポジトリ外（`C:/C/ai-split-backup/<name>`）へ退避 → `git rm -r --cached` → `git submodule add` → ignore 対象だけを元の場所へ戻す → サブモジュールの `git status` が clean であることを確認。
- **リポジトリ単位の設定**: `.gitignore`（ルートの汎用規則を複製。サブモジュールにはアンブレラの `.gitignore` が効かない）・`.gitattributes`・`LICENSE` は複製。secretlint・commitlint・prettier・ruff の設定はアンブレラのものを使う（`../` 経由。単体 clone では使えないが方針どおり）。
- **lefthook**: 各サブモジュールの `lefthook.yml` は `extends: [../maintenance/lefthook/submodule.yml]` だけ。共通設定は `../maintenance/scripts` の precommit・secretlint、`../node_modules` の prettier・commitlint、`uv run --project ..` の ruff を呼ぶ。サブモジュールのコミットで pre-commit・commit-msg が走ることを使い捨てブランチで確認した（Prettier の整形、commitlint の拒否）。
- **marketplace の source**: サブモジュール内のプラグインは、Claude Code・Codex は `git-subdir`、Copilot は `github`+`path`。`ref`／`sha` は付けない（既定ブランチを追う）。固定すると、push 前の SHA を指したエントリが生まれうるため。
- **tool-release**: AI-tools 側へ移した。対象はアンブレラの main の `registry/repo-tools.yaml` を raw URL で取得して決め、`uv build --out-dir` で各パッケージを単体ビルドする（8 パッケージとも単体ビルドできることを確認）。
- **サイトのリンク**: `github.com/fdshg693/AI/tree/main/<submodule>/...` は 404 になるので、`.gitmodules` を読んでサブモジュールのリポジトリへリンクする（skills-site・tools-site 共通の `github-url.mjs`）。
- **アンブレラのブランチ**: ローカルは `master` のまま、リモートには `main` として push した（ワークフローがすべて `main` を対象にしているため）。

## 計画との差分

- 計画に無かった修正が 2 つ要った。skill-tools の **local** source も `git ls-files` でサブモジュールの中が見えない（agent-compat の切り出し直後に hooks カタログのテストで判明）。また、サイトの GitHub リンクもサブモジュールの中を指すと 404 になる。
- 事前の実験リポジトリは作らず、本番リポジトリで確認した（ユーザー回答）。

## 検証

- 各切り出しの前に、新リポジトリのファイル一覧と全履歴のパスに `.env`・`*.pem`・tfstate 等が無いことと、secretlint を確認した。アンブレラも push 前に同じ確認をした（secretlint は Windows のコマンドライン長の制限があるので 40 件ずつ）。
- テスト: maintenance/scripts 40、skill-tools 311、agent-tooling 248、skills/plugins 114 + doc-transcription 37（別プロジェクト）、skills-site 40（新規 1 件）。`just skills-site-check`、`precommit-check --all`、`uv lock --check`、`claude plugin validate`、`just links-check`。
- 本番での確認:
  - CI の `Umbrella check` が通った（サブモジュールの再帰 checkout、Linux での生成物の一致、`uv lock --check`）。
  - 隔離した設定ディレクトリで `claude plugin marketplace add https://github.com/fdshg693/AI.git` → `coding`（AI-skills）・`my-tools`（AI-tools）を `git-subdir` 経由でインストールできた。
  - `uvx --from "git+https://github.com/fdshg693/AI-tools.git#subdirectory=textgraph"` でインストールできた。
  - GitHub source の `skill-tools list-skills` がサブモジュールを辿り、local と同じ 122 件を列挙した。

## 残課題（未確認・後続へ）

- **gitlink の更新で `paths:` が発火するか**（計画の実験 1）は未確認。アンブレラの初回 push は新規ブランチのため、skill-site・tools-site は走らなかった。次のポインタ更新で確認する。
- **AI-tools の `Tool release`** は、アンブレラがまだ無い時点で走って失敗した（`repo-tools.yaml` を取得できない）。次に AI-tools の main へ push したとき、または `workflow_dispatch` で再実行したときに、8 パッケージ分のタグと Release が作られる。外部向けの操作なので未実行。
- **アンブレラのシークレットと設定**: 新しい `fdshg693/AI` には Actions のシークレット（`AZURE_STATIC_WEB_APPS_API_TOKEN`・`OPENROUTER_API_KEY`・`ANTHROPIC_API_KEY`・Codex/gh-aw 用）が無い。GitHub Pages（tools-site）も未設定。サイトのデプロイと triage bot はそれまで失敗する。
- **skill-tools の表示 URL**: GitHub source の `list-skills`／`search` が出す blob URL は、サブモジュールの中のファイルでもアンブレラのパス（404）になる。`display_skill_path` は descriptor しか受け取らないので、サブモジュールの対応表を descriptor か index に持たせる必要がある。
- **退避フォルダ** `C:/C/ai-split-backup/`（リポジトリ外）には、切り出し前の追跡ファイルのコピーだけが残っている（ignore 対象は戻した）。確認後に削除してよい。
- `registry/` の互換コピー（ルートの yaml 4 本）をいつ消すかは、まだ決めていない（skill-tools の利用者が `registry/` 対応版に上がった後）。
