# 他プロジェクトへのコピー手順

このリポジトリの `.claude/plans/` には2セットのファイルがある。他プロジェクトへ持ち出すときは**汎用セットだけ**をコピーする。

| セット                             | 対象                                                                                                                                                                                                    | 用途                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| 汎用セット（コピー対象）           | `AGENTS_GENERAL.md`（→`AGENTS.md`にリネーム）、`references/skills-general/`（フォルダ名はそのまま）、`references/00-overview-example.md` 等の実例4ファイル、`references/rough/`、`references/progress/` | どのプロジェクトでもそのまま使えるプラン運用ルール             |
| このリポジトリ専用（コピー対象外） | `AGENTS.md`、`README.md`、`CLAUDE.md`、`references/skills/`                                                                                                                                             | このリポジトリのスキル連携・ルール格納先の慣習を前提にした内容 |

## 手順

導入先プロジェクトのルートで実行する。

1. `.claude/plans/` フォルダを作る。
2. このリポジトリの `.claude/plans/AGENTS_GENERAL.md` を、導入先の `.claude/plans/AGENTS.md` としてコピーする（ファイル名を変える）。
3. このリポジトリの `.claude/plans/references/skills-general/` を、導入先の `.claude/plans/references/skills-general/` としてそのままコピーする（フォルダ名は変えない。`AGENTS.md` 側からの相対リンクが `references/skills-general/...` を指しているため、フォルダ名を変えるとリンクが壊れる）。
4. このリポジトリの `.claude/plans/references/00-overview-example.md`・`01-research-step-example.md`・`02-implementation-step-example.md`・`03-single-file-example.md`・`references/rough/`・`references/progress/` をそのまま `references/` 配下にコピーする。
   - サンプル本文中に `claude-plugins/...` へのスキルリンクが残っていることがある。これはこのリポジトリ固有のスキルへの導線なので、導入先に同名のスキルが無ければリンクごと削除してよい（本文の説明自体は流用できる）。
5. Claude Code を使うプロジェクトなら、中身が `@./AGENTS.md` の1行だけの `.claude/plans/CLAUDE.md` を追加する（このリポジトリの `CLAUDE.md` をそのままコピーしてよい）。
6. コピー後、`AGENTS.md`・`references/skills/` の内容を、導入先プロジェクトで実際に使えるサブエージェント・スキル・ルールファイルの格納先（`.claude/rules/`・`AGENTS.md`・`CLAUDE.md`・`.clinerules` 等）に合わせて書き足す。

## 自動化

手動コピーの代わりに [templates/planner/copy_plans_template.py](../../templates/planner/copy_plans_template.py) を使うと速い。オプションは `templates/planner/README.md` を参照。
