---
type: Repo Convention
title: リポジトリ構成とJunctionの規約
description: "Explains which submodules this umbrella has (skills / tools / agent-compat / site), which repository owns which generated file, how to clone, open a submodule alone in Claude Code (skill junctions, `_umbrella/` folders, per-submodule hooks), commit in a submodule and then update the pointer, and how this repository declares directory junctions in a committed `.links.yaml` instead of committing them, how `just links-sync` / `links-check` / `links-clean` create, verify and remove them (registering each in the owning repo's info/exclude first), which junctions are forbidden (pointing at an ancestor, into another junction, overlapping, outside the umbrella), why scanners must not walk into junctions, and the checkout hazard when a commit tracks files at a junction path. Use when cloning, opening a submodule folder alone, committing inside a submodule, updating a submodule pointer, adding a junction, when `links-check` or the post-checkout warning fires, before checking out an old commit, or when writing code that walks the repository tree."
tags: [repo-wide]
status: draft
---

# リポジトリ構成とJunctionの規約

このリポジトリは、アンブレラ（ルート、`fdshg693/AI`）と 4 つのサブモジュールから成る（再編の経緯は完了後に削除したプラン `plans/repo-restructure/` に残る。git 履歴で参照する）。サブモジュール単体のフォルダを Claude Code で開けるように、上位や兄弟のフォルダを **Windows の Junction** で参照する。本ドキュメントは置き場所の判定基準、サブモジュールの運用、Junction の宣言・作成・禁止事項を定める。

## 置き場所の判定基準

新しいスキル・スクリプト・文書は、次の順に当てはめて置き場所を決める（2026-11 の再編で決めた基準）。

| 区分                   | 判定                                                                                                         | 置き場所                                                        |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| リポジトリ都合         | このリポジトリの保守にしか意味がない（生成器、pre-commit、メンテ手順のスキル、規約文書）                     | `maintenance/plugin`・`maintenance/scripts`・`maintenance/docs` |
| SSOT                   | 複数の生成物・検査が読む手編集の yaml                                                                        | `registry/`                                                     |
| tools 付属スキル       | 本文が `tools/<name>` の CLI のインストールを必須にしている（`meta.requires_repo_tools` の値だけで決めない） | `tools/_plugin/my-tools/skills/`                                |
| 汎用スキル             | 上のどれでもない Claude Code スキル。CLI を任意で使うだけ（無くても動く）ならここ                            | `skills/plugins/<plugin>/skills/`                               |
| 他 AI ツールの知識     | Codex・Copilot 等の使い方を説明するスキル（中身は普通の SKILL.md）                                           | `skills/plugins/ai-tools-knowledge/`                            |
| マルチ AI 対応の仕組み | 複数の AI ツールへ同じものを届ける仕組み（フック・コンテキスト注入）。スキルの実体は置かない                 | `agent-compat/agent-tooling/`                                   |
| ツール固有書式の見本   | そのツールの書式でしか書けないファイル（plugin manifest、rules の frontmatter 等）                           | `agent-compat/formats/<tool>/`                                  |

他ツールへの届け方（マーケットプレイスの `sources`、gitignore 済みの `workspace_copies`）は [ai-tools-config](./ai-tools-config.md)。生成コピー（`.cline/skills/` 等）は Junction ではなく実ディレクトリで、目印 `.agent-compat-copy` によって走査から外す。

スクリプトを同梱して `tools/` のインストールが要らないスキルは汎用側（例: `skills/plugins/web-lookup`、`skills/plugins/doc-tools`）。CLI 本体は `tools/<name>` の平坦配置のまま（`registry/repo-tools.yaml` の `path` 契約）。

## サブモジュール

| パス            | リポジトリ                                                              | 中身                                                |
| --------------- | ----------------------------------------------------------------------- | --------------------------------------------------- |
| `skills/`       | [fdshg693/AI-skills](https://github.com/fdshg693/AI-skills)             | 汎用スキルのプラグイン（`plugins/<plugin>/`）       |
| `tools/`        | [fdshg693/AI-tools](https://github.com/fdshg693/AI-tools)               | CLI 群（`<name>/` の平坦配置）と `_plugin/my-tools` |
| `agent-compat/` | [fdshg693/AI-agent-compat](https://github.com/fdshg693/AI-agent-compat) | `agent-tooling/`・`formats/`・`docs/differences/`   |
| `site/`         | [fdshg693/AI-site](https://github.com/fdshg693/AI-site)                 | `skills-site/`・`tools-site/`                       |

`maintenance/`・`registry/`・`docs/`・`plans/` とツール設定フォルダ（`.claude/` 等）はアンブレラに残る。パスはどこでもアンブレラのルート相対で書く（`tools/aim`、`skills/plugins/coding`）。サブモジュールの中の相対パスにするのは、そのリポジトリだけで完結する記述（各リポジトリの README など）に限る。

### 生成物の所有権

- **アンブレラが持つ**: 複数のリポジトリから集める生成物。`.claude-plugin/marketplace.json`・`skill-catalog.json`、`.agents/plugins/marketplace.json`、`.github/plugin/marketplace.json`、README のツール節、`registry/` の互換コピー、`uv.lock`・`pnpm-lock.yaml`（ワークスペースのメンバーはサブモジュールにあるが、ルート定義はアンブレラだけに置く。サブモジュール直下に `pyproject.toml`・`pnpm-workspace.yaml`・lockfile を置かない）。
- **サブモジュールが持つ**: その中で完結する生成物。各プラグインの `skills/CATALOG.md`、`SKILL.md` の `meta` 既定値、ツールの版数、agent-tooling の `hooks/generated/`。
- サブモジュール内のプラグインを指す marketplace のエントリは、相対パスではなくそのリポジトリを指す（Claude Code・Codex は `git-subdir`、Copilot は `github`+`path`。`ref` は付けず既定ブランチを追う）。生成器が `.gitmodules` から決める（[`plugin_source.py`](../scripts/plugin_meta/util/plugin_source.py)）。サイトの GitHub リンクも同じ規則でサブモジュールのリポジトリを指す。

### clone と日々の操作

```sh
git clone --recurse-submodules https://github.com/fdshg693/AI.git
cd AI
lefthook install && just sub-hooks-install   # アンブレラと各サブモジュールに lefthook を入れる
just links-sync                              # .links.yaml の Junction を作る
just agent-compat-sync                       # Cline・Kilo・Antigravity 向けのスキルのコピー
just hooks-install && just sub-agent-hooks-install  # エージェントフック（下の「サブモジュールを単体で開く」）
```

- `git pull` のあとは `just sub-init`（`git submodule update --init --recursive`）。未初期化のサブモジュールがあると uv はそのメンバーを黙って無視し、`uv lock` から落ちる。`uv lock` の前に必ず初期化する。
- サブモジュールは記録された commit で detached HEAD になる。作業する前に `just sub-sync`（全サブモジュールで `main` を checkout して fast-forward）か、そのサブモジュールで `git switch main`。状態は `just sub-status`。

### 作業ブランチ（アンブレラとサブモジュールで揃える）

アンブレラでブランチを切っても、サブモジュールのブランチは変わらない（アンブレラが持つのは commit のポインタだけ）。複数の端末で作業するときは、同じ名前のブランチを全リポジトリに切る。`just branch-*` がアンブレラと全サブモジュールでまとめて行う（実体は [`maintenance/scripts/branches/`](../scripts/branches/)）。

| レシピ                                           | 動作                                                                                                                      |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `just branch-status`                             | 各リポジトリのブランチ・upstream との差・未コミット数・ポインタの状態                                                     |
| `just branch-list`                               | ローカルブランチを、どのリポジトリにあるか付きで一覧                                                                      |
| `just branch-new <name> [--from BASE]`           | 全リポジトリで作って切り替える                                                                                            |
| `just branch-switch <name> [--create]`           | 全リポジトリで切り替える。ローカルに無くても `origin/<name>` があれば追跡ブランチを作る（別の端末で作ったブランチを拾う） |
| `just branch-push`                               | 今のブランチを upstream 付きで push。サブモジュールを先にし、失敗したらアンブレラは push しない                           |
| `just branch-pull`                               | 今のブランチを upstream から fast-forward。`sub-sync` と違って `main` に戻さない                                          |
| `just branch-delete <name> [--remote] [--force]` | ある所だけ削除。`main`・`master`・既定ブランチ、今いるブランチ、未マージのブランチ（`--force` なし）は断る                |

- どのレシピも `--only <submodule>...` で対象のサブモジュールを絞れる（アンブレラは常に含む）。
- 状態を変えるレシピは全リポジトリを先に検査し、1 つでも引っかかれば何も変えない（途中まで切り替わった状態を残さない）。
- `main` への直接コミットは `pre-commit` がブロックする（アンブレラと全サブモジュール。merge・rebase 中は除く）。作業は必ずブランチで行う。
- 作業ブランチにいる間は `just sub-sync` を使わない（全サブモジュールを `main` に戻す）。
- マージはサブモジュールが先。サブモジュールの作業ブランチを `main` にマージして push し、アンブレラのポインタをその `main` の commit に合わせてからアンブレラをマージする。

### コミットは 2 段階

1. **サブモジュールの中でコミットする。** そのサブモジュールのフォルダで `committing` スキルのラッパーを使う。フックは `maintenance/lefthook/submodule.yml`（各サブモジュールの `lefthook.yml` が `extends` する）から来て、アンブレラと同じ再生成・整形・検査が走る。単体で clone したときは `extends` 先が無いので何も走らない。
2. **アンブレラでポインタを更新する。** アンブレラで `git add <submodule>`（と、手順 1 で再生成されたアンブレラ側の生成物）をコミットする。gitlink の変更で marketplace・`skill-catalog.json` が再生成される。push はサブモジュールを先にする（アンブレラが未 push の commit を指さないように）。

1 つの変更がサブモジュールとアンブレラの両方にまたがっても、アトミックにはコミットできない。サブモジュール → アンブレラの順に分けてコミットする。CI の [`umbrella-check.yml`](../../.github/workflows/umbrella-check.yml) が、生成物の再生成漏れと `uv lock --check` を検査する。

### サブモジュールを単体で開く

サブモジュールのフォルダだけを Claude Code で開いて作業できる（アンブレラ配下に clone されている前提）。開く前に、アンブレラのルートで次を 1 回ずつ実行する。

```sh
just links-sync               # 各サブモジュールの .links.yaml の Junction（スキルと _umbrella/）を作る
just sub-agent-hooks-install  # アンブレラと同じ Claude Code フックを各サブモジュールに入れる
```

- **見えるもの**: 親の `CLAUDE.md`（とその `@./AGENTS.md`）は Claude Code が自動で読む。親の `.claude/skills`・`.claude/agents`・`.claude/settings.json` は読まない（サブモジュールが repo root になり、遡りが止まる）。そのため、そのフォルダの作業に要るアンブレラのスキル（`committing` など）を `.claude/skills/<name>` の Junction で見せる。
- **何を見せるか**: 宣言は各サブモジュールの `.links.yaml` が正本で、このドキュメントには一覧を書かない。足すのは「そのフォルダの作業に要るもの」だけにする（アンブレラ全体を見せると単体で開く意味が無くなる）。スキルは `.claude/skills/<name>`、強く結びついたアンブレラのフォルダ（`registry/` など）は `_umbrella/<name>` という名前で見せる。
- **アンブレラで開いたとき**: サブモジュールの `.claude/skills` は起動時には読まれない。サブモジュール内のファイルを読むと、`skills:committing`・`tools:committing` のようなディレクトリ別のスキルとして遅延ロードされる（中身は同じスキル。Claude Code 2.1 で確認）。
- **`_umbrella/` の中身はアンブレラ（または別のサブモジュール）のファイル**。そこで直したら、コミットはそのファイルが属するリポジトリで行う。サブモジュールのコミットには入らない（Junction は exclude 済み）。
- **`plans/` は全サブモジュールで共有**: 各サブモジュール直下の `plans/` はアンブレラの `plans/` を参照する。作成・変更したプランはアンブレラに属する。
- **指示ファイル**: サブモジュールの `CLAUDE.md` は `@./AGENTS.md` だけ。`@../...` で親を import しない（親は自動で読まれるので二重になる。外部 import の承認も出る）。サブモジュールの `AGENTS.md` には、アンブレラの規約と重複しない、そのフォルダ固有の責務だけを書く。
- **フック**: 各サブモジュールの `.claude/skill-tools.hooks.yaml`（source はアンブレラ）をコミットし、入れたフックと `.claude/settings.json`・`.skill-tools/` は gitignore する。`.claude/hooks` を Junction で共有しない（`.env`・`logs/`・`state/` まで共有し、サブモジュールでのインストールがアンブレラの実体を書き換える）。カタログを再生成したら `just sub-agent-hooks-update`。
- **ワークスペース**: `uv run`・pnpm はアンブレラの workspace と `.venv` をそのまま使う。サブモジュール直下に `pyproject.toml`・`pnpm-workspace.yaml` を置かない。
- **単体で clone した場合**: `.links.yaml` の参照先が無いので Junction は作られず、親の指示・フック・lefthook も無い。Claude Code の起動自体はできる。`--plugin-dir <アンブレラ>/maintenance/plugin` を渡せば、Junction の代わりにメンテ用スキルを 1 セッションだけ読み込める。

### CI とリリース

- アンブレラのワークフローは `actions/checkout` に `submodules: recursive` を付ける。`paths:` はサブモジュールの中のパターンでは発火しない（アンブレラから見えるのは gitlink だけ）ので、`skills`・`tools`・`site` のようにサブモジュールのパスそのものを書く。
- サイトの公開（Azure Static Web Apps・GitHub Pages）はアンブレラで動く。サブモジュールへの push だけではサイトは更新されず、アンブレラのポインタ更新で動く。
- CLI のタグと GitHub Release は AI-tools の `tool-release.yml` が作る（対象はアンブレラの `registry/repo-tools.yaml` を読んで決める）。`git+https://github.com/fdshg693/AI-tools.git#subdirectory=<name>` でインストールする。

## Junction はコミットせず `.links.yaml` で宣言する

Git は Junction を実ディレクトリとして辿り、参照先の中身を通常ファイルとしてステージしてしまう。そこで Junction 自体はコミットせず、各リポジトリのルートに置く `.links.yaml` に宣言をコミットする。

```yaml
links:
  - path: .claude/skills/committing # このリポジトリのルートからの相対
    target: maintenance/plugin/skills/committing # アンブレラのルートからの相対
    why: サブモジュール単体で開いたときにコミット手順を使うため
```

- キーは `path`・`target`・`why` の 3 つだけ。区切りは `/`。絶対パス・`..`・`.` は不可。
- アンブレラのルートは、目印ファイル [`.umbrella-root`](../../.umbrella-root) を持つ最も近い祖先。`.gitmodules` には頼らない。
- `.links.yaml` を読むのは、アンブレラと、チェックアウト済みのサブモジュール（再帰）のルート直下だけ。

## 操作は `just links-*` だけで行う

| レシピ             | 内容                                                                                                                                                                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `just links-sync`  | 宣言を検証し、各パスを所有リポジトリの `info/exclude` の管理ブロックへ `/path` 形式（末尾 `/` なし。mac/Linux のシンボリックリンクにも一致させる）で書いてから Junction を作る。参照先が違う Junction は張り直し、宣言から消えたものは外す。 |
| `just links-check` | 欠けている・参照先が違う・exclude に無い・宣言に無い Junction、アンブレラ外を指す Junction、Junction のパスの下に追跡ファイルがある状態をエラーにする。過去に追跡されていたパスは警告する。                                                  |
| `just links-clean` | 宣言と管理ブロックにある Junction を外し（参照先は消さない）、管理ブロックを空にする。                                                                                                                                                       |

実体は [`maintenance/scripts/links/`](../scripts/links/)。`--dry-run`（sync・clean）と `--quiet` を渡せる。

- **直接 `mklink /J` しない**。exclude に登録されない Junction は、中身の一部が ignore 対象のとき `git clean -fd` が参照先のファイルを個別に消す。
- **Junction を `rm -rf`・`Remove-Item -Recurse`・`shutil.rmtree` で消さない**。参照先の中身まで消えるおそれがある。`just links-clean` を使う（中では `is_link_like` を確かめてから `os.rmdir`）。
- exclude の場所は `git rev-parse --path-format=absolute --git-path info/exclude` で求める。サブモジュールの `.git` はファイルなので `.git/info/exclude` を直書きしない。
- 参照先がこの clone に無い（サブモジュールを単体で clone した）ときは、`sync` は警告して飛ばす。失敗にはしない。
- Junction は作成時の絶対パスを持つ。アンブレラを移動・コピーしたら `links-check` が「参照先が違う」と出すので `links-sync` で張り直す。
- 対象はディレクトリだけ。ファイル単体は Junction にできないので、ディレクトリ単位で参照するか `@` import（指示ファイル）で済ませる。シンボリックリンクは開発者モードが要るので使わない。

## 禁止事項（`sync`・`check` が検査する）

- 自分自身・自分の祖先を指す（再帰走査が無限ループになる）。
- 自分の中を指す。別の Junction の中を指す・経由する（連鎖は解決順に依存する）。
- 宣言どうしが重なる（同じパス、または一方が他方の祖先）。
- Junction の中に Junction を作る。宣言したリポジトリの外（入れ子のサブモジュールの中）に作る。
- `path` に実体のファイル・ディレクトリが既にある（`sync` は触らずエラーにする）。

## checkout・switch の危険

Junction のパスを実ディレクトリとして追跡しているコミットへ `switch`／`checkout` すると、Git は ignore 対象を上書きしてよいものとして扱い、**参照先の同名ファイルを無警告で上書きし、戻ると参照先から削除する**。再編では「実ディレクトリだったパスを Junction にする」ため、古いコミットで必ず起こる。

- Junction のパスは、なるべく過去に追跡されていたパスと重ねない。重なる宣言は `links-check` が警告する。
- そのようなコミットを checkout する前に `just links-clean`、戻ったら `just links-sync`。
- lefthook の `post-checkout` が `links post-checkout` を実行し、追跡ファイルが Junction のパスにある状態を警告する（事後の警告で、防止はしない）。参照先が書き換わっていたら、参照先で `git status` を見て `git restore` する。
- `git stash -a` は Junction を実ディレクトリのコピーに化けさせるので使わない。

## リポジトリを走査するコードの約束

Python の `Path.is_symlink()`／`os.path.islink()` は Junction で False を返し、`os.walk(followlinks=False)`・`rglob` は Junction の中へ入る。走査するコードは次を守る（二重計上・二重書き込み・無限ループの防止）。

- Python は「symlink か Junction か」を `os.lstat` の `st_reparse_tag` で判定する `is_link_like` を使い、`os.walk` の `dirnames` から外す。maintenance/scripts は [`links/fs.py`](../scripts/links/fs.py)、独立配布の `tools/skill-tools` と `agent-tooling` は同じ関数をパッケージ内に持つ（配布物どうしで依存させないため）。`Path.walk()` の既定も辿らない。
- Node は `fs.readdir` の Dirent の `isSymbolicLink()` が Junction で true になるので、それで飛ばす。tinyglobby／fast-glob は `followSymbolicLinks: false` を明示する。
- pytest はルートの [`conftest.py`](../../conftest.py) の `pytest_ignore_collect` で Junction を収集対象から外す。
- git の一覧に従うもの（skill-tools の通常経路、rg 既定、codegraph、textgraph、lefthook）と、prettier・ruff は exclude 済みの Junction を辿らないので対応不要。
- `git ls-files`・`git diff --cached` はサブモジュールの中を返さない（gitlink のパスが 1 行出るだけ）。サブモジュールの中まで見るコードは、チェックアウト済みのサブモジュールで同じコマンドを実行してパスを前置する。maintenance/scripts は [`repo_git.py`](../scripts/repo_git.py)、skill-tools は `LocalSource`／`GitHubSource` が自前で行う。

## 関連

- [justfile-conventions](./justfile-conventions.md) — `links-*` レシピの置き方
- [lefthook-automation](./lefthook-automation.md) — `post-checkout` の警告
