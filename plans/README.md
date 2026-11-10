# plans

既存コードベースに機能を追加する前に、AIコーディングエージェントと一緒に「実装プラン」を書き、実行し、片付けるための運用テンプレート。1機能 = 1サブフォルダ（または小さい機能なら1ファイル）。

- **対象**: AGENTS.md / CLAUDE.md を読むコーディングエージェントと作業するリポジトリ。言語・フレームワークは問わない。
- **含まれるもの**: プランの書式（5点フォーマット・OKF準拠frontmatter・`status`・依存関係）、実行中の更新ルールと progress（進捗記録）、初版の凍結（`snapshot/`）、整合性チェックのスクリプト。

## 導入手順

1. 次を導入先リポジトリの `plans/` にコピーする。

   | コピーするもの                         | 内容                                                       |
   | -------------------------------------- | ---------------------------------------------------------- |
   | [AGENTS.md](AGENTS.md)                 | エージェント向けの運用ルール（入口）                       |
   | [CLAUDE.md](CLAUDE.md)                 | `@./AGENTS.md` を読み込むだけ（Claude Code 用）            |
   | [guides/](guides)                      | 場面別ガイド（共通ルールの正本）                           |
   | [references/](references)              | サンプル（導入先の `plans/` と同じ構造）                   |
   | [lint_plans.py](lint_plans.py)         | frontmatter・依存関係・チェックボックス・節構成の整合チェック |
   | [snapshot_plan.py](snapshot_plan.py)   | 初版プランを `snapshot/` に凍結                             |

   この README はコピーしない。

2. （任意）Claude Code でサブエージェント・スキルを使って進めるなら、[guides/claude-code-execution.md](guides/claude-code-execution.md) を参考に、導入先にあるスキル・サブエージェントに合わせて `plans/AGENTS.md` の「導入先固有の運用」節へ書き写す。Claude Code を使わないなら、このファイルは削除してよい。
3. ルートの `AGENTS.md`（または `CLAUDE.md`）に「機能実装前のプランは `plans/AGENTS.md` に従う」と1行足す（Claude Code ならルート `CLAUDE.md` に `@plans/AGENTS.md` でもよい）。サブフォルダの AGENTS.md はルートで作業するエージェントに自動では読まれないため。
4. リポジトリルートで lint を実行し、エラーが出ないことを確認する（標準ライブラリのみ。`uv` が無ければ `python` でよい）。

   ```bash
   uv run plans/lint_plans.py plans
   ```

## 同梱スクリプト

リポジトリルートで実行する。

```bash
uv run plans/snapshot_plan.py plans/{plan-name}           # 初版を snapshot/ に凍結（実行着手前に1回）
uv run plans/lint_plans.py plans                          # 整合チェック（エラーは path:line: 形式、非0終了）
uv run plans/lint_plans.py --examples plans/references    # テンプレート編集時: サンプル自体を検査
```

使い方の詳細は [guides/plan-writing.md](guides/plan-writing.md) の「初版の凍結スナップショット」「整合性チェック」節。
