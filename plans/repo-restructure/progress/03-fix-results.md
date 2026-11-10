# 03 実行記録（既存の不整合の修正）

## ユーザー判断（2026-11-10、すべて推奨どおり）

- `requires_repo_tools` の tools/ 以外の値: 外部コマンド（gh / git / uv / python / graphviz / curl）は `dependencies` へ移し、エージェントの組み込みツール名（WebFetch / Read / Grep / Bash）と `flow.dot` は削除。`meta_field.yaml` の `dependencies`・`requires_repo_tools` の説明を合わせて更新。meta-plugins の `lefthook.yml` は対象外（検査の除外どおり）
- aim-lib: frontmatter の `name` を `aim-lib` に変更（旧 `using-aim-library`。呼び出し名が変わる）
- aim-summarize / aim-use: 削除済みとして、members・README・docs・スキル本文の言及を全部外す
- 削除: `.kilo/skills/kilo-test-guide`、`.kilo/skills/using-kilo-cli`（追跡外だった）、`antigravity-plugins/`、`.cline/rules/README.md`

## コミット

| コミット               | 内容                                                                                                                                                                                                                            |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cbd38a5`              | `tools/scheule` → `tools/schedule`、members を実在パス（`tools/schedule/{ai-schedule,issue-agent}`）へ。`tools/aim-use/aim-summarize` を外す。uv.lock                                                                           |
| `86a55c9` + `cf00ac7`  | aim-summarize / aim-use の言及を削除（docs の例は my-agents・tools/schedule に差し替え）                                                                                                                                        |
| `5c16994`              | 空・残骸フォルダの削除、ai-tools.yaml の readme から antigravity-plugins を外して README 再生成                                                                                                                                 |
| `9427ecf`              | README の `templates/` を削除、`.clinerules/` を「agents-rules の出力先（未生成なら無い）」に、`.agents` の読み込み先を `codex-plugins/` に、`_agents/README.md` の矛盾を解消、AGENTS.md に `.claude/rules/` は任意の入力と追記 |
| `f878ca0` + `f4c2438`  | スキル内の旧パス参照を実在パスへ。vscode-docs・github-copilot-docs の downloader を自己完結版に置き換え                                                                                                                         |
| `14e5597` + 後続 chore | docs の claude_sandbox リンク、cline-plugins/meta → personal-info、cline-skill-writer の事実誤り                                                                                                                                |
| `1b74345` + 後続 chore | メタ欄の修正（上記判断どおり。ms-digest・tav-digest・parallel-agent-worktree・vscode-copilot-docs と aim を任意で使う docs スキル 6 件に repo tools を追記、claude-code-memory、tav-lit、kilo 3 件）                            |
| `9ed55e8`              | cursor の `skills_layout: subdir`。CATALOG は `cursor-plugins/meta/skills/CATALOG.md` へ（旧 `cursor-plugins/meta/CATALOG.md` は削除）                                                                                          |

## 計画との差分

- 前提条件の `git add --renormalize .` は不要だった。インデックスは既に全て LF（CRLF は作業コピーだけで、`git status` には出ない）。
- vscode-docs・github-copilot-docs の `download_*_reference.py` が、存在しない共有モジュール `llms_txt_downloader.py` を import していて実行できなかった。writing-skill-web のテンプレートを標準ライブラリだけで動く形に写して自己完結させた（パス参照修正の一部として同じコミット）。
- `.claude/rules/` は agent-tooling/README.md に「無くてもよい」旨が既にあり、ルート AGENTS.md に 1 文だけ足した。
- `using-kilo-cli` は git 追跡外だったので `rm` で削除。

## 検証

- `uv sync`、`uv run pytest tools/schedule`（54 passed）、writing-skill-web のテスト（91 passed）
- `just --justfile tools/internal/justfile precommit-check` 成功、`check_skill_repo_tools` 成功
- `pnpm -C site/skills-site run build` 成功（`site/skills-site/mise.toml` が未 trust のため、そのフォルダ内からの実行は mise が拒否する。リポジトリルートから `-C` で実行）
- 修正後に旧パス（`claude-plugins/{ai-code-tool,web,other-clis}`、`plugins/vscode/`、`aim-summarize`、`aim-use`、`scheule`）が plans 以外に残っていないことを rg で確認

## 残したもの（03 の対象外）

- copilot 側の `agents/openai.yaml`（2 件）→ 06
- CATALOG.md の位置統一 → 05（cursor は本ステップで `skills/` 配下になった）
- リポジトリ外（`~/.claude/settings.json` の statusLine パス、skill-deploy の editable 残骸）→ ユーザー確認のうえ 05 で
