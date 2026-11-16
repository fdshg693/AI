---
type: Plan Progress
status: implementing-done
---

# Step 1 実装メモ

- `temp/templates/.gitignore` に `temp/` を追加。`git init -b main` 後の初回コミット `514e244`（298 ファイル。`__pycache__`・`temp/`・`core/threads/planning` Junction は含まない）。
- secretlint: アンブレラから `temp/templates/**/*` を渡すと何も検査されない（`temp/` が無視される）。`temp/templates` を cwd にして `node_modules/.bin/secretlint --secretlintrc <umbrella>/.secretlintrc.json "**/*" ".claude/**/*"` で実行し、検出 0 件。仕込んだダミートークンが検出されることも確認済み。
- `gh repo create fdshg693/AI-templates --public`（description: "Operational templates for working with AI agents in fdshg693/AI"）で作成・push。
- アンブレラ `windows` で `git submodule add` → コミット `c1fb9da`（`.gitmodules` と `templates` ポインタのみ）。clone 内容は `temp/templates` と改行コード以外一致（`diff -rq --strip-trailing-cr`）。
- `uv lock --check` 通過。`just branch-switch --create --only templates` で templates を `windows` に。
- 未実施: `temp/templates` の削除。templates 側の作業メモ `temp/templates/temp/web-lookup/` はリポジトリに入れていないため、削除前にユーザーへ確認する。
