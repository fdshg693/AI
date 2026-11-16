---
type: Plan Progress
status: implementing-done
---

# Step 2 実装メモ

- templates `f481b94`（定型ファイル）: `infra/` から `lefthook.yml`・`.gitattributes`・`LICENSE`・`.claude/skill-tools.hooks.example.yaml` を写し、`.links.yaml`（`plans`・`.claude/skills/committing`・`_umbrella/maintenance-docs`・`core/threads/planning` → `templates/core/plans`）と `AGENTS.md`（「このフォルダだけを開いたとき」節）を追加。`CLAUDE.md` の本文は `git mv` で `README.md` へ移し、`CLAUDE.md` は `@./AGENTS.md` だけに。`.gitignore` に infra の共通部分を足した。templates 自身の `plans/` を削除。
- `template-create/SKILL.md` の「ルートの CLAUDE.md の core の中身に 1 行足す」リンクを `README.md` に直し、`meta.version` を 1.0.1 に。
- templates `9537540`（`style:`）: Prettier・ruff を tracked ファイルに一括適用（`git ls-files` で渡し、Junction を辿らせない）。`template-review/SKILL.md` も整形されたので 1.0.1 にバンプ。
- Prettier で壊れるものが 2 種類あったので、アンブレラ `.prettierignore` で除外（アンブレラ `a1aff5d`、ポインタ更新と同じコミット）:
  - `templates/starter/*/STARTER.md` — frontmatter の `[a, b]` を折り返し、`check_starters.py` の 1 行パーサが読めなくなる
  - 生成物 `**/docs/vault-schema.md`（`gen_schema_doc.py --check` が失敗）・`**/vault/scopes/*/dashboard.md`・`core/practice-review/references/index.md`
- `just links-sync` で templates の Junction 4 本を作成し、`links-check` で 4 本とも ok。`links-check` 全体はアンブレラの `.claude/skills/okf-spec`（skill-tools sync-skills が作った外部への Junction）で失敗するが、本プランと無関係。
- 整形後に README 記載の lint を全部実行し通過: decisions・plans（2 種）・practice-review・repo-plans（2 種）・threads・link_plans `--check`・learning-template・`check_starters.py`（starter の lint 込み）・knowledge-vault `gen_schema_doc.py --check`／`validate.py --strict`。`lint_plans` の `notification-preferences` 参照の warning は記入例の意図的なもの。
- Junction の rglob 問題: 各 lint の走査起点は対象テンプレートのフォルダで、`core/threads/planning` を含む `core/` 全体を走査するものは無い（`check_starters.py` は decisions・knowledge-vault だけ）。従来の `link_plans.py` と同じ Junction なので新しいリスクは無い。
- サブモジュール内 `.claude/skills/template-*/SKILL.md` は pre-commit の version バンプ検査の対象になる（バンプで通過）。
