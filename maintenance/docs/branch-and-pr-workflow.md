---
type: Repo Convention
title: ブランチ運用とmainへのPR手順（サブモジュール込み）
description: "Explains how this umbrella and its submodules are branched and merged: `main` is the default branch everywhere, each machine keeps one fixed working branch name (e.g. `windows`) used with the same name in the umbrella and every submodule, changes reach `main` only through pull requests (submodule PRs first, then a pointer update, then the umbrella PR), PRs are merged with a merge commit so the working branch can fast-forward afterwards, `main` is brought back into the working branch after every merge, and a messy working branch is deleted and recut from `main`. Use when opening a PR to main, merging one, deciding the working branch name on a new machine or worktree, bringing an updated main back into the working branch, or when a working branch has diverged and needs to be recut."
tags: [repo-wide]
status: draft
---

# ブランチ運用とmainへのPR手順（サブモジュール込み）

アンブレラと 5 つのサブモジュール（[repo-layout](./repo-layout.md#サブモジュール)）は別々のリポジトリなので、ブランチも PR もリポジトリごとにある。本ドキュメントは、それらを 1 つの作業セットとして扱うためのブランチ名・PR の順番・取り込みの規約を定める。`just branch-*` レシピ自体の動作は [repo-layout の「作業ブランチ」](./repo-layout.md#作業ブランチアンブレラとサブモジュールで揃える)を参照。

## ブランチの規約

- **`main` がメインブランチ。** アンブレラも全サブモジュールも既定ブランチは `main`。`main` への直接コミットは `pre-commit` がブロックする。
- **作業ブランチは端末ごとに 1 つの固定名。** `windows` のように端末（環境）ごとに名前を決め、作業のたびに新しいブランチを切らず、その名前を使い続ける。他の端末・エージェントと名前が重ならないようにする（例: `windows`・`windows2`・`claude-cloud`）。
- **アンブレラと全サブモジュールで同じ名前にする。** アンブレラが `windows` ならサブモジュールも `windows`。名前がずれると、どのポインタがどのブランチの commit かが追えなくなる。作るのも切り替えるのも `just branch-new` / `just branch-switch` で全リポジトリまとめて行う。
- **並行して別の作業をしたいときは、ブランチを増やさず作業場所を増やす。** 別の端末を使うか、git worktree で別の作業ツリーを作り、そこに別の固定名（`windows2` など）を割り当てる。1 つの作業ツリーで複数のブランチを行き来しない。
- **`main` へは PR 経由でだけ入れる。** ローカルで `main` にマージして push しない。

## mainへのPR手順

変更がサブモジュールとアンブレラにまたがるときも、2 段階コミット（[repo-layout の「コミットは 2 段階」](./repo-layout.md#コミットは-2-段階)）と同じく**サブモジュールが先、アンブレラが後**。アンブレラの `main` が、サブモジュールの `main` に無い commit を指さないようにするため。

1. **状態を確かめて push する。**

   ```sh
   just branch-status   # 全リポジトリが作業ブランチにいて、未コミットが無いこと
   just branch-push     # サブモジュール → アンブレラの順に push
   ```

2. **変更のあるサブモジュールで PR を出してマージする。** `main` との差があるサブモジュールだけが対象（`git -C <submodule> log --oneline origin/main..HEAD` が空でないもの）。

   ```sh
   cd <submodule>
   gh pr create --base main --head windows --fill
   gh pr merge --merge     # マージ方式は下の「マージ方式」
   ```

3. **サブモジュールの作業ブランチに `main` を取り込み、アンブレラのポインタを合わせる。**

   ```sh
   cd <submodule>
   git fetch origin && git merge --ff-only origin/main && git push
   cd ..
   git add <submodule>  # ポインタがサブモジュールの main の commit を指す
   ```

   アンブレラで `chore(repo): update <submodule> pointer` としてコミットし（`committing` スキルのラッパーを使う）、`just branch-push`。

4. **アンブレラで PR を出してマージする。** 本文に、先にマージしたサブモジュールの PR を列挙する。CI の `umbrella-check.yml` が生成物の再生成漏れと `uv lock --check` を検査するので、通ってからマージする。

   ```sh
   gh pr create --base main --head windows --fill
   gh pr merge --merge
   ```

5. **アンブレラの作業ブランチに `main` を取り込む**（次節）。

サブモジュールだけの変更でも、手順 3〜4 のポインタ更新 PR をアンブレラに出す。サイトの公開などはアンブレラのポインタ更新で動くため（[repo-layout の「CI とリリース」](./repo-layout.md#ci-とリリース)）。

### マージ方式

PR は **merge commit**（`gh pr merge --merge`）でマージする。squash・rebase にすると、作業ブランチの commit が `main` の祖先にならず、次のようになる。

- 作業ブランチに `main` を fast-forward で取り込めず、同じ変更が 2 系統の履歴に分かれる。
- アンブレラが指していたサブモジュールの commit が `main` から辿れなくなる。

squash・rebase でマージしてしまったら、下の「ブランチを切り直す」で作業ブランチを `main` から作り直す。

## mainの更新を取り込む

自分の PR がマージされたとき、または他の端末・エージェントの PR で `main` が進んだときは、作業ブランチに `main` を取り込む。

```sh
# サブモジュールごと（変更が無いものも含めて）
git -C <submodule> fetch origin && git -C <submodule> merge origin/main
# アンブレラ
git fetch origin && git merge origin/main
just sub-status      # ポインタと各サブモジュールの HEAD がずれていないか
just branch-push
```

- 取り込みもサブモジュールが先。アンブレラの `main` のポインタが指す commit を、サブモジュール側に先に持ってくるため。
- 自分の未マージの commit が無ければ fast-forward になる。ある場合は merge commit ができる。
- アンブレラの merge でポインタが衝突したら、そのサブモジュールの作業ブランチの HEAD（`main` を取り込んだ後のもの）を `git add <submodule>` で採る。
- `just sub-sync` は使わない（全サブモジュールを `main` に戻してしまう）。

## ブランチを切り直す

取り込みの merge commit が重なった、squash でマージされた、試行錯誤の commit が残ったなどで作業ブランチが汚くなったら、直さずに消して `main` から切り直す。

```sh
just branch-status                          # 未 push・未マージの commit が無いことを確かめる
just branch-switch main
just branch-delete windows --remote --force # 未マージ扱いでも消す（中身が main に入っていることを確かめてから）
git fetch origin && just sub-init           # main とポインタの指す commit を最新にする
just branch-new windows --from origin/main
just branch-push
```

- `--force` は、作業ブランチの変更がすべて `main` に入っている（squash 済みを含む）ときだけ使う。`git log origin/main..windows` に残っている commit の中身を確かめてから消す。
- 他の端末が同じ名前のブランチを使っていないこと（端末ごとに固定名にしている理由）。

## 関連

- [repo-layout](./repo-layout.md) — サブモジュールの構成、2 段階コミット、`just branch-*` レシピ
- [lefthook-automation](./lefthook-automation.md) — `main` への直接コミットをブロックする `pre-commit`
- [gh-actions-lifecycle](./gh-actions-lifecycle.md) — PR で走る CI
