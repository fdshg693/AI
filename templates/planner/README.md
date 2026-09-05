# templates/planner

実装前に「プラン」を書く運用を、他プロジェクトに導入するための解説と補助スクリプト。

## 正（SSOT）は `.claude/plans/`

**このリポジトリの `.claude/plans/` が唯一の正**。運用ルールの本文・実例を変更したいときは、必ず
[`.claude/plans/README.md`](../../.claude/plans/README.md)・[`.claude/plans/AGENTS_GENERAL.md`](../../.claude/plans/AGENTS_GENERAL.md) 側を直接編集する。このフォルダには実体を置かない。

## 他プロジェクトへの導入方法

`.claude/plans/` にはこのリポジトリ専用のセットと、他プロジェクトへそのまま持ち出せる汎用セットの2つがある。導入先には**汎用セットだけ**をコピーする。手順・対象ファイルの詳細は [`.claude/plans/COPYING.md`](../../.claude/plans/COPYING.md) を参照（本ファイルでは要点のみ）。

```
.claude/plans/                            （このリポジトリ側）
  AGENTS_GENERAL.md                       → コピー先で AGENTS.md にリネーム
  CLAUDE.md                               → Claude Code を使う場合のみコピー（中身は `@./AGENTS.md` の1行）
  references/skills-general/              → フォルダ名はそのままコピー（AGENTS.md からの相対リンク先のため）
  references/00〜03-*-example.md          → そのままコピー
  references/rough/, references/progress/ → そのままコピー

  AGENTS.md・README.md・references/skills/  ← このリポジトリ専用。コピー対象外
```

- コピー後、`AGENTS.md`（旧 `AGENTS_GENERAL.md`）・`references/skills-general/` の内容を、導入先プロジェクトの
  ルール格納先の慣習（`.claude/rules/` + `paths:` フロントマター、`AGENTS.md`、`CLAUDE.md`、`.clinerules` 等）や、実際に使える
  サブエージェント・スキルに合わせて書き足す。
- サンプル（`references/00〜03-*-example.md`）本文中にこのリポジトリ固有のスキルへのリンクが残っている場合は、導入先に同名のスキルが無ければ削除してよい。
- 導入先が Claude Code を使わない場合は `CLAUDE.md` は不要（コピー対象から外してよい。自動化スクリプトなら `--no-claude`）。

## 自動化: コピー用スクリプト

手動コピーの代わりに、同階層の [`copy_plans_template.py`](copy_plans_template.py) を使うと速い。

```bash
# 導入したいプロジェクトのディレクトリで実行する
cd /path/to/target-project
python /path/to/ai/templates/planner/copy_plans_template.py
```

- 実行すると、このスクリプト自身の場所からリポジトリルートを逆算し、上記の汎用セットをリネームしつつ CWD 配下の `.claude/plans/` にコピーする。
- コピー先に対象のいずれかが既にある場合、デフォルトでは**何もコピーせず**エラーになる（事前に全項目の衝突をチェックしてから実行するため、途中まで一部だけコピーされる、という状態にはならない）。上書きしたい場合は `--force` を付ける。
- `--force` 時、フォルダ系の項目（`references/skills-general` 等）はマージコピーされる。コピー先にだけ存在する余分なファイルは削除されない点に注意。
- `--no-claude` を付けると `CLAUDE.md` をコピー対象から外す。
- コピー後、上記「他プロジェクトへの導入方法」に従って内容を導入先の慣習に合わせて調整すること（スクリプトはファイルコピー・リネームのみ行い、内容の書き換えは行わない）。

オプション一覧は `python copy_plans_template.py --help` を参照。
