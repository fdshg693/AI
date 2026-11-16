---
type: Plan Progress
status: implementing-done
---

# Step 3 実装メモ

- アンブレラ `a2b1910`（`docs(repo):`）: `AGENTS.md`・`README.md`・`README_EN.md`・`CONTRIBUTING.md`・`justfile`・`maintenance/lefthook/submodule.yml`・`maintenance/docs/repo-layout.md`（description・数・サブモジュール表・置き場所の判定基準に「運用テンプレート → `templates/core/<name>/`」）・`gh-actions-lifecycle.md`・保守スキル 3 本（committing 1.1.13・discovering-skills 1.0.13・exploring-this-repo 1.0.10）に `templates/` を登録。生成物 `maintenance/docs/index.md` は `cfb1310` で追従。
- `.github/workflows/*.yml` の `paths:` にサブモジュールを列挙しているのは `skill-site.yml` の `skills` だけで、templates は対象外。`umbrella-check.yml` は `paths:` 無し。
- 検証: `just sub-status`・`branch-status`（templates は `windows`・pointer ok。upstream 未設定＝未 push）、`links-sync`／`links-check`（templates の Junction 4 本 ok。`templates/plans` は履歴で追跡されていた旨の warning。失敗は既知の `.claude/skills/okf-spec` のみ）、`uv lock --check`、`lint_plans --examples`（意図的な warning 2 件）・`link_plans --check`・`check_starters.py`、`plans/lint_plans.py plans` すべて通過。templates の pre-commit は Step 2 のコミット（`f481b94`・`9537540`）で動作済みのため、空でない追加コミットでの再確認は省略。
- `temp/templates` は templates `514e244` と（`temp/` 以外）一致を確認し、ユーザー同意のうえ `temp/web-lookup/` ごと削除。`core/threads/planning` Junction（旧パス `C:\C\templates\core\plans` を指していた）は先に単体で外した。

## 完了記録

このプランは Step 3 で完了。後続（アンブレラの `plans/` を `templates/core/plans` から同期する手順）は、必要になったら新しいプランにスコープと前提を書く。

- **完了範囲**: `fdshg693/AI-templates` を作成して `templates/` サブモジュールとして追加し、定型ファイルを揃え、アンブレラの規約・README・保守スキルに登録した。`temp/templates` を削除した。
- **検証結果**: sub/branch status、links-sync/check（templates 分）、`uv lock --check`、templates の各 lint、プラン lint が通過。
- **計画との差分**: 無し。templates の `windows` ブランチは未 push（push はユーザー指示待ち）。
