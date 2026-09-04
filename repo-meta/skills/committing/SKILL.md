---
# 前提: リポジトリルートで lefthook が有効（`lefthook install`済み）であること。
# 衛生処理（再生成・整形・バンプチェック・secretlint）は lefthook に任せる。
# 方針の正本は docs/repo-meta/lefthook-automation.md。このスキルはコミット操作の手順だけを書く。
name: committing
description: Makes a git commit in this repository under leftover pre-commit/commit-msg (Conventional Commits, secretlint, generated-file sync). Use when the user asks to commit, when leftover or commitlint rejects a commit, or when deciding what to stage versus leave to hooks.
meta:
  tag: []
  requires_repo_tools: leftover.yml
  requires_env: none
  dependencies: none
  requires_install: leftover
  requires_hooks: leftover.yml pre-commit, leftover.yml commit-msg
  requires_skills: none
  status: experimental
  description: このリポジトリ固有のgit commit手順（lefthook前提）
  version: 1.0.0
---

# このリポジトリでのコミット

ユーザーが明示的にコミットを依頼したときだけ実行する。衛生処理（生成物の再生成、Markdown/Python整形、`SKILL.md`デフォルト補完、releaseツールのpatchバンプ）は[`lefthook.yml`](../../../lefthook.yml)の`pre-commit`がやる。同じコマンドをコミット前に手で叩かない。

## 手順

1. **現状を読む** — 次を並列で取る。自分が覚えていない変更はステージしない（[AGENTS.md](../../../AGENTS.md)）。
   - `git status`
   - `git diff` と `git diff --staged`
   - `git log -15 --oneline`（件名の型・scopeを揃える）
2. **含めるファイルを決める** — 今回の依頼に属する変更だけを`git add`する。`git add -A`は使わない。含めないもの:
   - `.env` / `credentials.json` 等の秘密
   - `temp/` や作業メモ、自分以外のエージェントが残した無関係な差分
   - 「DO NOT EDIT MANUALLY」の生成物を手で直しただけの差分（次のコミットでlefthookが上書きする）
3. **`SKILL.md`を含むなら`meta.version`を確認する** — `meta.version`以外が変わっているのにバンプしていなければ、`pre-commit`のバンプチェックがコミットを拒否する。直すときは[skill-md-commits](../../../docs/repo-meta/skill-md-commits.md)に従う。
4. **コミットする** — フックを飛ばさない。失敗したら`--no-verify`で再実行しない。

   ```text
   git commit -m "type(scope): subject"
   ```

   本文が要るときだけ2行目以降に「なぜ」を書く。件名は1行、[Conventional Commits](https://www.conventionalcommits.org/)（`@commitlint/config-conventional`）。このリポジトリの追加ルールは`commitlint.config.js`のみ: `subject-case`は`start-case` / `pascal-case` / `upper-case`を禁止する（sentence-caseや日本語、固有名詞の先頭大文字は可）。

5. **成功後に`git status`を見る** — leftoverが`stage_fixed: true`で再生成・整形を同じコミットへ再ステージしていることがある。想定内なら追加コミットしない。
6. **pushしない** — ユーザーが明示したときだけ。`main`/`master`への`--force`はしない。

## 件名

`type(scope): subject`。`type`は変更の種類、`scope`は触った領域（`tools` / `skills` / `hooks` / `repo-tools` 等）。`subject`は「なぜ」に寄せ、末尾ピリオドは付けない。

| type       | 使うとき                     |
| ---------- | ---------------------------- |
| `feat`     | 機能・スキル・ツールの追加   |
| `fix`      | バグ修正                     |
| `docs`     | ドキュメントのみ             |
| `chore`    | 生成物同期、依存、メンテ作業 |
| `refactor` | 挙動を変えない再構成         |
| `test`     | テストのみ                   |
| `ci`       | GitHub Actions 等            |
| `revert`   | 取り消し                     |

既存ログの例:

```text
feat(tools): add grepapp CLI + grep-app skill wrapping the grep.app MCP server
fix(hooks): stop_alertポップアップが表示されずPowerShellが前面に出る問題を修正
docs(antigravity): Rules frontmatterのtrigger/globsキーを反映してantigravity-memoryを更新
chore(tools): sync generated files for the grepapp addition
```

## leftoverが既にやること

ジョブ一覧と方針の正本は[lefthook-automation](../../../docs/repo-meta/lefthook-automation.md)。コミット時に（ステージしたファイルの`glob`に当たったものだけ）走る。

- `ai-tools.yaml`由来の生成物再生成（marketplace / skill-catalog / CATALOG.md / Cline rules / Copilot instructions / Antigravity rules / READMEのAIツール節）
- `.github/workflows/*.md`のgh-awコンパイル
- `SKILL.md`の`meta.version` / `meta.description` / `meta.tag`デフォルト補完（リポジトリ全体を走査する）
- 未バンプ`SKILL.md`のブロック、`repo-tools.yaml`との整合チェック
- `repo-tools.yaml`の`release: true`ツールフォルダ変更時の`pyproject.toml` patchバンプ
- ステージ済みMarkdownのPrettier、ステージ済みPythonの`ruff format`
- secretlint
- `commit-msg`のcommitlint

再生成・整形結果は同じコミットに入る。失敗しても作業ツリーへの書き込みが残ることがあるので、再試行前に必ず`git status`を見る。

次はlefthookに入っていない。コミットのたびに走らせない。

- `skill_meta_field_fill.py`（有料API。[skill-meta-fields](../../../docs/repo-meta/skill-meta-fields.md)）

## フックが失敗したとき

`--no-verify`は使わない。エラーを読んで直し、必要なら再ステージして**新しい**`git commit`を行う。失敗したコミットを`--amend`しない。

| 症状                                         | 直し方                                                                             |
| -------------------------------------------- | ---------------------------------------------------------------------------------- |
| `meta.version`バンプチェックで拒否           | [skill-md-commits](../../../docs/repo-meta/skill-md-commits.md)                    |
| `repo-tools` consistency で拒否              | [repo-tools-config](../../../docs/repo-meta/repo-tools-config.md)                  |
| commitlintが件名を拒否                       | 上の「件名」に合わせて書き直す。`Start Case` / `PascalCase` / 全大文字件名は不可   |
| secretlintがヒット                           | 秘密をファイルから除き、履歴に載せない。フックを飛ばして通さない                   |
| 生成物やフォーマットで差分が増えただけ       | leftoverが直している。`git status`で確認し、意図しないファイルだけ戻す             |
| バックフィルが自分の触っていない`SKILL.md`へ | 想定内（全体走査）。意図しない変更は`git checkout -- <path>`で戻してから再コミット |

## やってはいけないこと

- `git commit --no-verify` / `--no-gpg-sign`、`git config`の変更
- 破壊的操作（`push --force`、hard reset）をユーザーが書いていないのに行う
- leftoverが既にやる再生成・整形・バンプを「念のため」先に手実行する
- 失敗したコミットを`--amend`する。`--amend`してよいのは、ユーザーが明示した、または**成功した**コミットのフックが同コミットへファイルを足したあと、まだpushしておらず、そのHEADを自分が作った場合だけ
- 自分以外が残した差分を同意なく捨てる

## 関連

- [lefthook-automation](../../../docs/repo-meta/lefthook-automation.md) — 衛生をフックへ寄せる方針
- [skill-md-commits](../../../docs/repo-meta/skill-md-commits.md) — `SKILL.md`コミット時のフックと直し方
- [repo-tools-config](../../../docs/repo-meta/repo-tools-config.md) — releaseツールの自動バンプとrepo-toolsチェック

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。`ai-tools.yaml`へ登録しないこと。
