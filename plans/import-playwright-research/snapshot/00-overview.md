---
type: Plan
status: ready
---

## 実装ステータス

- [ ] [01-research-inventory.md](01-research-inventory.md) — 持ち込む資産の棚卸しと置き場所の確定
- [ ] [02-browser-tools.md](02-browser-tools.md) — `pwq`・`pwdo`・テストサイトを `tools/browser/` へ
- [ ] [03-browser-skills.md](03-browser-skills.md) — ブラウザ操作スキル群を新プラグインと my-tools へ
- [ ] [04-playwright-app.md](04-playwright-app.md) — playwright-app を `workflow/playwright-app/` へ
- [ ] [05-overlap-and-verify.md](05-overlap-and-verify.md) — 既存スキルとの重複の差分取り込みと全体検証

# Playwright 研究クローンから再利用可能な仕組みを取り込む - 概要

## 要件

- `temp/playwright`（→ `C:\C\playwright`。microsoft/playwright のクローンに、自作のスキル・ツール・実験アプリを足したもの）の概要は `temp/playwright/.claude/rules/ROLE.md` にある。
- そこから **Playwright OSS 本体を除いて**、スキル・ツール・テストサイト・実験アプリなどの再利用可能な仕組みをこのリポジトリへ取り込む。
- 取り込み後は、クローン側の `.claude/` やディレクトリ構成に依存せずに動くこと（パス・参照・依存の入れ直し・登録まで含めて完了とする）。

### 取り込み対象と除外（ユーザー確認済み）

| 区分 | クローン側のパス | 扱い |
| --- | --- | --- |
| CLI | `.claude/tools/pwq`（playwright-cli の出力を縮めるラッパー）、`.claude/tools/pwdo`（ブラウザ操作の一区間を安いモデルへ委譲） | 取り込む → [02](02-browser-tools.md) |
| ツール規約 | `.claude/rules/tools/pwq.md`・`pwdo.md`（`paths:` 付きルール） | 各ツールの `AGENTS.md` に移す → [02](02-browser-tools.md) |
| テストサイト | `resources/`（認証不要・ローカル完結の静的サイト 11 種）、`.claude/rules/resources/custom-pages.md` | 取り込む（ツールの隣）→ [02](02-browser-tools.md) |
| スキル | `.claude/skills/using-playwright-cli`・`sharing-browser-with-user`・`searching-playwright-docs`・`authoring-playwright-agents` | 取り込む → [03](03-browser-skills.md) |
| 調査ノート | `.claude/docs/*-notes.md`（5 本。スキル・ツールの実測根拠） | 取り込む → [03](03-browser-skills.md)・[02](02-browser-tools.md) |
| ルーティング | `ROLE.md` の「〜するとき」節 | スキル本文のルーティング表に移す（グローバルルールにはしない）→ [03](03-browser-skills.md) |
| 実験アプリ | `playwright-app/`（自然言語ストーリー → AI がブラウザ操作 → `.spec.ts` 生成。Python サーバー + vertical_slice）、`.claude/rules/playwright-app/*.md`、`playwright-app/.claude/` | 取り込む → [04](04-playwright-app.md) |
| 既存と重複 | `.claude/skills/ai-sdk-docs`・`codegraph-docs`・`web-lookup`・`writing-skill` | 新規には入れず、改善点だけ既存へ反映 → [05](05-overlap-and-verify.md) |
| 除外 | Playwright OSS（`packages/`・`docs/`・`tests/`・`utils/`・`browser_patches/`・`examples/`・`OVERVIEW.md`・`Playwright_README.md` など） | 取り込まない |
| 除外 | `.claude/plans/`（旧版のプランテンプレート。`plans/` に後継がある）、`.claude/history/`（完了プラン）、`.claude/export-portable.mjs`・`.claude/outputs/`（持ち出し用エクスポータ。本プランが置き換える）、`temp/`（このリポジトリのツールのコピー） | 取り込まない。完了プランへのリンクは要約に置き換える |
| 除外 | 生成物・実行時産物（`node_modules/`・`dist/`・`.venv/`・`__pycache__/`・`.playwright-cli/`・`test-results/`・`models.json`・`.env`・スキルの `output/` スナップショット・`playwright-app/uv.lock`・`package-lock.json`） | コピーしない。スナップショットは同梱スクリプトで取り直す |
| 除外 | クローン側 `.kilo/`（worktree のコピー）、`playwright-app/.claude/plan/references/`（旧プランのテンプレート） | 取り込まない |

## 実装ステップ

1. [01-research-inventory.md](01-research-inventory.md) — 参照グラフ・重複差分・置き場所の未決事項を確定する（コードは書かない）
2. [02-browser-tools.md](02-browser-tools.md) — `tools/browser/` カテゴリを新設し、`pwq`・`pwdo`・`test-sites` を移して登録する
3. [03-browser-skills.md](03-browser-skills.md) — 汎用スキル 4 本を新プラグインへ、`pwq`/`pwdo` 前提の手順を my-tools のスキルへ分けて入れる
4. [04-playwright-app.md](04-playwright-app.md) — playwright-app を workflow サブモジュールへ移し、uv/pnpm ワークスペースと just に載せ替える
5. [05-overlap-and-verify.md](05-overlap-and-verify.md) — 重複 4 スキルの差分を既存へ反映し、生成・検査・動作確認を通す

依存: 02 → 03（スキルがツールのコマンド名・パスを参照する）、02 → 04（playwright-app がテストサイトを使う）。03 と 04 は互いに独立。

## 主要な決定事項

| 決定 | 理由 |
| --- | --- |
| CLI は新カテゴリ `tools/browser/` に置く（`pwq`・`pwdo`・`test-sites`） | 同じ性質（ブラウザ操作）のツールが複数そろうので、[tools-directory-layout](../../maintenance/docs/tools-directory-layout.md) の「新しいカテゴリを作ってよい」に当たる。テストサイトは両ツールの実測根拠でもあるので隣に置く |
| テストサイトは CLI ではないので `repo-tools.yaml` に登録しない | `openrouter/` や `ai-usage` と同じく、登録しないディレクトリの前例がある。`tools/README.md` の索引には載せる |
| 汎用スキル 4 本は新プラグイン `skills/plugins/browser/` にまとめる（名前は 01 で確定） | 4 本とも「CLI は任意」で動く汎用スキル（[repo-layout の置き場所の判定基準](../../maintenance/docs/repo-layout.md#置き場所の判定基準)）。Playwright という 1 つの話題で相互参照が密なので、`topics` に散らさず 1 プラグインにする |
| `pwq`/`pwdo` を前提にした手順（`context-saving-explore.md`・`delegating-browser-tasks.md`）は `tools/_plugin/my-tools/skills/` の新スキルへ分ける | 本文が `tools/` の CLI のインストールを必須にしているので「tools 付属スキル」に当たる。`using-playwright-cli` からは「入っていれば」の任意リンクにする |
| ツールの呼び出しは `node .claude/tools/pwq/dist/cli.js` ではなくコマンド名 `pwq`/`pwdo`（`package.json` の `bin` を `pnpm add -g` で入れる）に統一する | [tool-conventions](../../maintenance/docs/tool-conventions.md) の配布 CLI の形に揃える。`.claude/tools/` はこのリポジトリでは使わない |
| playwright-app は `workflow/playwright-app/` に置く | 「AI の SDK/CLI を組み合わせ、手元でカスタマイズして使う実行フロー」で、付属スキルを持たず配布 CLI でもない（ワークフロー区分）。ユーザー確認済み |
| スキルの `output/` スナップショットはコピーせず、同梱の download/sync スクリプトで取り直す | クローン側のスナップショットは古い。`searching-playwright-docs` はローカルの `docs/src` を読む前提なので、GitHub から取る形に作り替える（OSS 本体を持ち込まないため） |
| ROLE.md のルーティング（「初見のサイトを調べるとき」等）はグローバルルールにせず、`using-playwright-cli` の SKILL.md 本文に移す | このリポジトリはブラウザ操作が主目的ではない。常時注入するルールにするとコンテキストを無駄に使う |
| 完了プラン（`.claude/history/`）は持ち込まず、そこへのリンクは README 内の短い要約に置き換える | `plans/` は完了後に削除する運用（[plan-execution.md](../guides/plan-execution.md#完了後の後片付け)）なので、完了プランを置く場所が無い |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

- 新規: `tools/browser/pwq/`、`tools/browser/pwdo/`、`tools/browser/test-sites/`（tools サブモジュール）
- 新規: `skills/plugins/browser/`（プラグイン本体と 4 スキル。skills サブモジュール）
- 新規: `tools/_plugin/my-tools/skills/<pwq/pwdo 用スキル>/`（tools サブモジュール）
- 新規: `workflow/playwright-app/`（workflow サブモジュール）
- 変更: `registry/ai-tools.yaml`・`registry/repo-tools.yaml`・`registry/local-configs.yaml`
- 変更: `pnpm-workspace.yaml`・`pyproject.toml`・`justfile`（テストサイト起動のレシピ）
- 変更: `tools/README.md`・`workflow/README.md`・`maintenance/docs/tools-directory-layout.md`
- 変更: `.gitignore`（アンブレラ。`.playwright-cli/`・`test-results/`・`playwright-report/`）
- 変更（ノートを `docs/` に置く場合）: `docs/index.md`・`docs/log.md`
- 生成物の更新: `.claude-plugin/marketplace.json`・`skill-catalog.json`・`skills/README.md`・README のツール節・各 `CATALOG.md`・`pnpm-lock.yaml`・`uv.lock`
- 変更（差分反映のみ）: `skills/plugins/topics/skills/ai-sdk-docs`・`codegraph-docs`、`skills/plugins/web-lookup/skills/web-lookup`、`skills/plugins/cc-knowledge/skills/writing-skill`

## ルール更新ポイント

- `maintenance/docs/tools-directory-layout.md` の「現行のカテゴリと振り分け基準」に `browser/` を 1 行足す（02 の完了時）。
- `tools/browser/pwq/AGENTS.md`・`pwdo/AGENTS.md`・`test-sites/AGENTS.md` を新設し、クローン側の `paths:` 付きルールの中身を移す（ネストした AGENTS.md の注入で同じ効果になる）。`tools-directory-layout.md` は「AGENTS.md は `@./README.md` の 1 行のみ」としているので、規約を持つツールの例外（前例 `tools/llm/my-agents/AGENTS.md`）を同文書に 1 行足す。
- `workflow/playwright-app/AGENTS.md` に `.claude/rules/playwright-app/*.md` の規約を集約する（04）。
- 新プラグインを足すので `registry/ai-tools.yaml` を先に更新する（AGENTS.md の SSOT 規約）。
- `AGENTS.md`（ルート）は変えない。ブラウザ操作の入口はスキルの description とする。

## 進め方

- 実行主体: 01 はメインのエージェントが行う（棚卸しは Explore サブエージェントに委任してよいが、置き場所の採否はメインが決める）。02〜05 はメインが順に実装する。
- TODO 化: 各ステップの「やること」1 行を 1 TODO、サブモジュールごとに 1 コミット（中でコミット → アンブレラでポインタ更新の 2 段階）。
- 着手前: このプランのレビューをサブエージェントに 1 回依頼し（[plan-writing.md「プランレビュー」](../guides/plan-writing.md#プランレビューサブエージェントに1回依頼する必須)）、反映後に `uv run plans/snapshot_plan.py plans/import-playwright-research` で初版を凍結する。
