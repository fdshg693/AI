---
type: Plan Step
status: implementing-done
---

# Step 5: 既存スキルとの重複の差分取り込みと全体検証

> [00-overview.md](00-overview.md) の続き。02〜04 の完了後に行う。差分の中身は [01](01-research-inventory.md) の調査結果を使う。

## やること

クローン側にもある `ai-sdk-docs`・`codegraph-docs`・`web-lookup`・`writing-skill` について、クローン側にしか無い改善だけを既存スキルへ反映する。そのうえで、リポジトリ全体の生成・検査を通し、クローン側への参照が残っていないことを確かめる。

## 読むべきファイル

**差分の判定**

- 01 の調査結果（各スキルの `diff -r` の要約）
- 既存側 `skills/plugins/topics/skills/ai-sdk-docs/`・`codegraph-docs/`、`skills/plugins/web-lookup/skills/web-lookup/`、`skills/plugins/cc-knowledge/skills/writing-skill/` の SKILL.md・README.md

**検査の手順**

- `maintenance/plugin/skills/committing/SKILL.md` — サブモジュールの 2 段階コミットと pre-commit
- `lefthook.yml` — pre-commit で走る再生成・検査

## 触るファイル

- 変更（改善があった場合のみ）上記 4 スキルの SKILL.md・README.md・スクリプト。SKILL.md を変えたら `meta.version` を上げる
- 生成物（必要なら）各 `CATALOG.md`・`skill-catalog.json`

## 決定事項

- **重複スキルは新しく足さない**。差分の取り込み先は常に既存側。`output/` スナップショット・`output/temp/`・`.venv/`・`.env` の差は無視する。
- **`ai-sdk-docs`・`codegraph-docs`・`writing-skill` は既存が新しく、取り込みなし**（version・meta・記述とも既存が上）。
- **web-lookup は全体では既存が新しいが、`tav.md` の 2 点だけ取り込む**: (a) `map`/`crawl`/`research` を CLI に出していない理由（実測: `map` は 15 クレジットで新規 1 枚・死 URL 5 件、sitemap の部分集合）とサイト偵察は `using-playwright-cli` の `site-recon.md` を使う誘導（別プラグインなのでスキル名で参照）、(b)「`localhost`・社内・非公開・認証壁の向こうの URL は外部サービスに渡さない」。`meta.version` を 1.3.1 に上げる。
- 許可リストに入れる正しい言及: `using-playwright-cli/README.md` の「`install --skills` が `.claude/skills/` に配る」、`authoring-playwright-agents` の `.claude/agents/*.md`、`test-sites` 自身の説明。
- 検査で見る項目: `rg -n "\.claude/(tools|skills|rules|docs)|resources/|ROLE\.md|export-portable"` を新規追加分（`tools/browser/`・`skills/plugins/browser/`・`tools/_plugin/my-tools/skills/browser-context-tools/`・`workflow/playwright-app/`）にかけ、ヒットを目視で「正しい言及（上流の挙動説明、test-sites 自身の説明など）」と「直し漏れ」に分ける。直し漏れ 0 件、リンク切れ 0 件。
- 注意: クローン側（`C:\C\playwright`）は変更しない。取り込み後に削除するかどうかはユーザーが決める。

## ルール更新ポイント

- なし（既存スキルの内容改善のみ）。

## 進め方

- 実行主体: メインのエージェント。
- TODO 化: (1) 重複 4 スキルの差分反映（改善が無ければスキップしてその旨を記録）、(2) 参照の残りの検査、(3) `just` の全体検査と pre-commit、(4) 完了記録を `progress/` に書く。
- 変更対象は実質 `skills/plugins/web-lookup/skills/web-lookup/tav.md`・`SKILL.md`（version）だけ。
- 確認: アンブレラで lefthook の pre-commit が通る、`uv run plans/lint_plans.py plans` が通る、CI の umbrella-check 相当（local-configs 検査を含む）がローカルで通る。

## 実行中に判明した変更

- 2026-11-15（Step 1）: 重複 4 本の差分を確定（取り込みは web-lookup `tav.md` の 2 点のみ）、検査の許可リストを具体化。根拠は [progress/01-research-results.md](progress/01-research-results.md) の 9。
- 2026-11-16（Step 5）: 検査で `workflow/playwright-app/docs/roadmap/01-vertical-slice.md` のリンク切れ 2 件（04 の直し漏れ）を見つけて直した。完了記録は [progress/99-completion.md](progress/99-completion.md)。
