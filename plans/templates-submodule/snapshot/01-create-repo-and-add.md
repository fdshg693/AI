---
type: Plan Step
status: ready
---

# Step 1: リポジトリ作成とサブモジュール追加

## やること

`temp/templates` を git リポジトリにして初回コミットし、GitHub に `fdshg693/AI-templates` を作って push する。アンブレラで `git submodule add` して `templates/` に置き、`.gitmodules` とポインタをコミットする。

## 読むべきファイル・実行推奨Grep

**前例を確認するため（優先度: 高）**

- `git show --stat c3cb74a` — `infra/` 追加時のアンブレラ側コミット（`.gitmodules` とポインタだけを 1 コミットにしている）
- 読む: `maintenance/docs/repo-layout.md`「サブモジュール」「作業ブランチ」 — 2 段階コミット、`main` 直コミット禁止、`branch-*` の扱い

**取り込む中身を確認するため（優先度: 中）**

- 読む: `temp/templates/.gitignore` — `__pycache__/` は除外済み。`temp/`（templates 内の作業メモ `temp/web-lookup/`）は未除外
- `find temp/templates -name __pycache__ -o -name '*.sqlite*' -o -name '.env*'` — 初回コミットに入れてはいけない生成物・秘密が無いか

## 触るファイル

### 新規

- `temp/templates/.git`（`git init -b main`）
- GitHub リポジトリ `fdshg693/AI-templates`（PUBLIC、description は英語 1 行。`AI-infra` に合わせる）
- `templates/`（サブモジュール）

### 変更

- `temp/templates/.gitignore` — 初回コミット前に `temp/` を足す
- `.gitmodules` — `[submodule "templates"]`

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| ---- | ---- |
| 初回コミットは templates 側で hooks なしで作り、整形はしない | まだ `lefthook.yml` が無い。整形は Step 2 で別コミットにして、取り込みと整形の差分を分ける |
| 初回コミットの直後に secretlint を手で 1 回かける（`just --justfile maintenance/scripts/justfile scan-staged-secrets` 相当を templates の全ファイルに） | hooks 無しで PUBLIC リポジトリへ push するため |
| `git submodule add https://github.com/fdshg693/AI-templates.git templates` で新規 clone し、`temp/templates` は動作確認後に削除 | `temp/templates` をそのまま移動するより、他の端末と同じ clone 状態で確認できる |
| GitHub リポジトリ作成と push は実行前にユーザーへ確認する | 外部への公開操作で、取り消しにくい |

- アンブレラは作業ブランチ `windows` にいる。サブモジュール追加のコミットもこのブランチで行い、`main` へは PR で入れる。
- 追加直後のサブモジュールは `main` にいる。Step 2 の前に `just branch-switch --create --only templates`（またはサブモジュール内で `git switch -c windows`）で作業ブランチをそろえる。
- `uv lock` への影響は無い（workspace メンバーにしない）が、`just sub-init` 後に `uv lock --check` が通ることは確認する。

## ルール更新ポイント

なし（Step 3 でまとめて行う）。

## 進め方

- メインのエージェントが直接進める。TODO は「初回コミット」「GitHub 作成・push（要確認）」「submodule add とアンブレラのコミット」の 3 つ。
