# templates/planner

実装前に「プラン」を書く運用を、他プロジェクトに導入するための解説と補助スクリプト。

## 正（SSOT）は `.claude/plans/`

**このリポジトリの `.claude/plans/` が唯一の正**。運用ルールの本文・実例を変更したいときは、必ず
[`.claude/plans/README.md`](../../.claude/plans/README.md) 側を直接編集する。このフォルダには実体を置かない。

## 他プロジェクトへの導入方法

導入先プロジェクトの `.claude/plans/` に、このリポジトリの `.claude/plans/` から次の4点をそのままコピーする。

```
.claude/plans/
  AGENTS.md      # ルール要約。プランを書く/読む前に必ず参照するよう誘導する文言
  CLAUDE.md      # Claude Code 用。中身は `@./AGENTS.md` の1行（AGENTS.md を読み込ませるだけ）
  README.md      # 本体。プランに書くべき項目・ステップ分割の目安・進め方の推奨を定義
  references/    # 実例一式（overview / 調査ステップ / 実装ステップ / 単一ファイル完結 / rough / progress）
```

- コピーしたら、`README.md` 内の「ルール更新ポイント」節・`AGENTS.md` の文言を、導入先プロジェクトのルール格納先の慣習
  （`.claude/rules/` + `paths:` フロントマター、`AGENTS.md`、`CLAUDE.md`、`.clinerules` 等）に合わせて書き換える。
  このリポジトリでは `.claude/rules` を採用せず `AGENTS.md` に統一しているが、それは一例であり導入先の慣習を優先する。
- 導入先が Claude Code を使わない場合は `CLAUDE.md` は不要（コピー対象から外してよい）。
- `.claude/plans/**` にパススコープするルール（`.claude/rules/plans.md` 相当）を導入先で別途持たせたい場合は、
  `AGENTS.md` の要点を踏まえて手書きする（本フォルダはそのファイルの雛形を保持しない）。

## 自動化: コピー用スクリプト

手動コピーの代わりに、同階層の [`copy_plans_template.py`](copy_plans_template.py) を使うと速い。

```bash
# 導入したいプロジェクトのディレクトリで実行する
cd /path/to/target-project
python /path/to/ai/templates/planner/copy_plans_template.py
```

- 実行すると、このスクリプト自身の場所からリポジトリルートを逆算し、`.claude/plans/`（AGENTS.md・CLAUDE.md・README.md・references/）
  を CWD 配下の `.claude/plans/` にコピーする。
- コピー先に4点のいずれかが既にある場合、デフォルトでは**何もコピーせず**エラーになる（事前に全項目の衝突をチェックしてから実行するため、途中まで一部だけコピーされる、という状態にはならない）。上書きしたい場合は `--force` を付ける。
- `--force` 時、`references/` はマージコピーされる。コピー先にだけ存在する余分なファイルは削除されない点に注意。
- コピー後、上記「他プロジェクトへの導入方法」に従ってルール格納先の記述を導入先の慣習に合わせて調整すること（スクリプトはファイルコピーのみ行い、内容の書き換えは行わない）。

オプション一覧は `python copy_plans_template.py --help` を参照。
