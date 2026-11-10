---
type: Repo Convention
title: リポジトリ構成とJunctionの規約
description: "Explains how this repository declares directory junctions in a committed `.links.yaml` instead of committing them, how `just links-sync` / `links-check` / `links-clean` create, verify and remove them (registering each in the owning repo's info/exclude first), which junctions are forbidden (pointing at an ancestor, into another junction, overlapping, outside the umbrella), why scanners must not walk into junctions, and the checkout hazard when a commit tracks files at a junction path. Use when adding a junction, when `links-check` or the post-checkout warning fires, before checking out an old commit, or when writing code that walks the repository tree."
tags: [repo-wide]
status: draft
---

# リポジトリ構成とJunctionの規約

このリポジトリは、アンブレラ（ルート）と、のちに切り出すサブモジュールから成る（再編の経緯は `plans/repo-restructure/`）。サブモジュール単体のフォルダを Claude Code で開けるように、上位や兄弟のフォルダを **Windows の Junction** で参照する。本ドキュメントは Junction の宣言・作成・禁止事項を定める。境界（何をどこに置くか）の節は再編の 05・09 で追記する。

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

| レシピ             | 内容                                                                                                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `just links-sync`  | 宣言を検証し、各パスを所有リポジトリの `info/exclude` の管理ブロックへ `/path/` 形式で書いてから Junction を作る。参照先が違う Junction は張り直し、宣言から消えたものは外す。              |
| `just links-check` | 欠けている・参照先が違う・exclude に無い・宣言に無い Junction、アンブレラ外を指す Junction、Junction のパスの下に追跡ファイルがある状態をエラーにする。過去に追跡されていたパスは警告する。 |
| `just links-clean` | 宣言と管理ブロックにある Junction を外し（参照先は消さない）、管理ブロックを空にする。                                                                                                      |

実体は [`tools/internal/links/`](../../tools/internal/links/)。`--dry-run`（sync・clean）と `--quiet` を渡せる。

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

- Python は「symlink か Junction か」を `os.lstat` の `st_reparse_tag` で判定する `is_link_like` を使い、`os.walk` の `dirnames` から外す。tools/internal は [`links/fs.py`](../../tools/internal/links/fs.py)、独立配布の `tools/skill-tools` と `agent-tooling` は同じ関数をパッケージ内に持つ（配布物どうしで依存させないため）。`Path.walk()` の既定も辿らない。
- Node は `fs.readdir` の Dirent の `isSymbolicLink()` が Junction で true になるので、それで飛ばす。tinyglobby／fast-glob は `followSymbolicLinks: false` を明示する。
- pytest はルートの [`conftest.py`](../../conftest.py) の `pytest_ignore_collect` で Junction を収集対象から外す。
- git の一覧に従うもの（skill-tools の通常経路、rg 既定、codegraph、textgraph、lefthook）と、prettier・ruff は exclude 済みの Junction を辿らないので対応不要。

## 関連

- [justfile-conventions](/repo-wide/justfile-conventions.md) — `links-*` レシピの置き方
- [lefthook-automation](/repo-wide/lefthook-automation.md) — `post-checkout` の警告
