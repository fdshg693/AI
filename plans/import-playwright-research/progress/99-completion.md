# 完了記録

完了日: 2026-11-16。

## 完了範囲

- 02〜04: `tools/browser/`（`pwq`・`pwdo`・`test-sites`）、`skills/plugins/browser/`（4 スキル）、`tools/_plugin/my-tools/skills/browser-context-tools/`、`workflow/playwright-app/`、`docs/topics/browser-automation/` を取り込み済み（各ステップのコミット）。
- 05: 重複 4 スキルの差分反映と全体検証。
  - `ai-sdk-docs`・`codegraph-docs`・`writing-skill`: 既存が新しく、取り込みなし（01 の判定どおり）。
  - `web-lookup`: `tav.md` に 2 点を反映。(a) `map`/`crawl`/`research` を CLI に出していない理由（実測）と、サイト偵察は `browser` プラグインの `using-playwright-cli` スキル `references/site-recon.md` を使う誘導（別プラグインなのでスキル名で参照）。(b)「`localhost`・社内・非公開・認証壁の向こうの URL は外部サービスに渡さない」。`meta.version` を 1.3.0 → 1.3.1。`CATALOG.md` を再生成。

## 検証結果

- 参照の残り: `rg -n "\.claude/(tools|skills|rules|docs)|resources/|ROLE\.md|export-portable"` を新規追加分にかけ 5 件。すべて正しい言及（`using-playwright-cli` の README・download スクリプトの `install --skills` の説明、README の「旧クローンの ROLE.md」の由来説明、`sharing-browser-with-user` README の常時ルール一般論、上流スナップショット `output/.../tracing.md`）。直し漏れ 0 件。`C:\C\playwright`・`temp/playwright`・`job_hunt` などの絶対パスも 0 件。
- リンク切れ: 新規追加分と web-lookup の Markdown 相対リンクを走査し 2 件検出 → 修正して 0 件。いずれも `workflow/playwright-app/docs/roadmap/01-vertical-slice.md`（`big_plans/` → `docs/roadmap/` の移設で 1 段ずれた `../scripts/...`、持ち込んでいない旧 HOW プラン `detail/...` へのリンク → 文言に置換）。
- CI umbrella-check 相当（ローカル）: `uv lock --check` OK、`test_check_local_configs.py`・`test_repo_git.py` 18 passed、`check.check_local_configs` OK、`precommit fix --all` 後の生成物差分は web-lookup `CATALOG.md` のみ（コミットに含めた）。
- `test_skills_plugin_index*.py` は Windows で 5 件失敗（`UnicodeDecodeError` 0x83 = cp932）。本ステップの変更を退避しても同じく失敗するため既存の Windows 固有問題で、本プランとは無関係（CI は Linux）。
- `uv run plans/lint_plans.py plans`: OK（03・04 の status が規約外の `done` だったのを `implementing-done` に直した）。

## 計画との差分

- 05 の「触るファイル」に無い `workflow/playwright-app/docs/roadmap/01-vertical-slice.md` のリンク修正を追加した（04 の取り込み時の直し漏れ）。それ以外は差分なし。
