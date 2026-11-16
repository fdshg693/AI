---
type: Plan Step
status: ready
---

# Step 3: ブラウザ操作スキル群を新プラグインと my-tools へ

> [00-overview.md](00-overview.md) の続き。[02](02-browser-tools.md) の完了（コマンド名・パスの確定）を待って着手する。プラグイン名・ノートの置き場所は [01](01-research-inventory.md) で確定したものを使う（以下では仮に `browser`・`browser-context-tools` と書く）。

## やること

クローン側の 4 スキルを skills サブモジュールの新プラグイン `skills/plugins/browser/` に移し、`pwq`/`pwdo` を必須とする手順だけを `tools/_plugin/my-tools/skills/browser-context-tools/` に分ける。ROLE.md のルーティングを `using-playwright-cli` の本文へ移し、プラグインを `ai-tools.yaml` に登録して生成物を更新する。

## 読むべきファイル

**スキルの書き方・meta の規約（最優先）**

- `skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md` と `bestpractices.md` — description・本文の書き方
- `registry/meta_field.yaml`・`maintenance/docs/skill-meta-fields.md` — `meta:` の必須フィールドと値
- `maintenance/plugin/skills/changing-skills-and-tools/SKILL.md` — スキル追加時の手順

**プラグイン追加の前例**

- `skills/plugins/web-lookup/`（`.claude-plugin/plugin.json`・`README.md`・`skills/CATALOG.md`）— 小さいプラグインの形
- `registry/ai-tools.yaml` — プラグインのエントリと `readme` ブロック
- `tools/_plugin/my-tools/skills/` の既存スキル 1 本 — tools 付属スキルの書き方（`requires_repo_tools`）

**移す元（クローン側）**

- `.claude/skills/*/SKILL.md`・`README.md`・`references/` — 4 スキル
- `.claude/rules/ROLE.md` — 「〜するとき」節
- `.claude/docs/site-recon-notes.md`・`script-cli-roundtrip-notes.md`・`browser-handoff-notes.md`・`scripted-automation-notes.md`

## 触るファイル

- 新規 `skills/plugins/browser/.claude-plugin/plugin.json`・`README.md`・`skills/CATALOG.md`（CATALOG は生成）
- 新規 `skills/plugins/browser/skills/using-playwright-cli/` — SKILL.md・README.md・`download_playwright_cli_skill.py`・`references/site-recon.md`・`references/script-cli-roundtrip.md`。`output/` はスクリプトで取り直す
- 新規 `skills/plugins/browser/skills/sharing-browser-with-user/` — SKILL.md・README.md・`references/`・`scripts/profiles.mjs`・`scripts/notify-user.ps1`・`.env.example`
- 新規 `skills/plugins/browser/skills/searching-playwright-docs/` — SKILL.md・README.md・`search_playwright_docs.py`・`sync_playwright_docs.py`（GitHub から取る形に改修）
- 新規 `skills/plugins/browser/skills/authoring-playwright-agents/` — SKILL.md・README.md・`agent-definition-format.md`・`download_playwright_agents.py`
- 新規 調査ノート 4 本 — 01 で決めた場所（プラグイン直下 `docs/` か `docs/topics/browser-automation/`）
- 新規 `tools/_plugin/my-tools/skills/browser-context-tools/` — SKILL.md と `references/context-saving-explore.md`・`references/delegating-browser-tasks.md`
- 変更 `registry/ai-tools.yaml` — 新プラグインを追加（生成より先に）
- 変更 `registry/local-configs.yaml` — `sharing-browser-with-user/.env`（`.env` は deny_patterns に掛かるので、実体を置く想定なら `local_configs` に宣言）
- 変更（必要なら）`registry/skill-tags.yaml` — 新しいタグが要る場合
- 生成 `.claude-plugin/marketplace.json`・`skill-catalog.json`・`skills/README.md`（`skills_plugin_index`）・README のツール節・`tools/_plugin/my-tools/skills/CATALOG.md`。`.agents/plugins/marketplace.json`・`.github/plugin/marketplace.json` は `marketplace.sources` に載せたときだけ変わる（載せない）

## 決定事項

- **`using-playwright-cli` の SKILL.md に ROLE.md のルーティング表を入れる**（初見サイトの偵察 → `site-recon.md`、スクリプト化 → `script-cli-roundtrip.md`、認証が絡む → `sharing-browser-with-user`、大きいページ・委譲 → `browser-context-tools`（`pwq`/`pwdo` が入っていれば））。`.claude/rules/ROLE.md` への参照は消す。
- **`pwq`/`pwdo` の起動は `pwq`・`pwdo` のコマンド名で書く**。`node .claude/tools/.../dist/cli.js` を残さない。
- **「実験用サイトが要るとき」の節**は `browser-context-tools` ではなく `using-playwright-cli` の references に置き、`tools/browser/test-sites/` はリポジトリ内で作業するときだけ使える任意の資源として書く（スキルは配布先で test-sites が無くても動く）。
- **`searching-playwright-docs`** は「playwright チェックアウト内に置かれていること」という前提を外し、`gh` で microsoft/playwright の `docs/src/**/*.md` を取る形にする。`allowed-tools` と `meta.dependencies`（`gh`。`requires_repo_tools` は `repo-tools.yaml` 登録ツール専用なので書かない）を合わせて直す。`!` の同期は読み込みのたびに走るので、鮮度内なら取りに行かないキャッシュを必ず持たせる。
- **`!` の起動は `python` 直呼びから `uv run` に揃える**（AGENTS.md の「python は直接使わない」。既存 `codegraph-docs` は両方を `allowed-tools` に許可している）。
- **`sharing-browser-with-user`** の `node .claude/skills/sharing-browser-with-user/scripts/profiles.mjs`（SKILL.md・references・`.env.example`）は `${CLAUDE_SKILL_DIR}` 基準に直し、`allowed-tools: Bash(node:*)` を `profiles.mjs` に絞る。
- **配布先でも `.playwright-cli/` を gitignore する**旨を `using-playwright-cli` の本文に書く（認証情報を含みうる）。
- **`sharing-browser-with-user/scripts/notify-user.ps1`** は Windows 専用。SKILL.md に「失敗しても exit 0、他 OS では通知なし」を残す。
- **調査ノートへのリンク**はスキル本文（エージェントが読む側）からは張らず、メンテナ向けの README からだけ張る。スキルの読み込み量を増やさないため。
- 注意: `site-recon.md` の `../../web-lookup/tav.md` は別プラグイン（`skills/plugins/web-lookup`）を指すことになる。相対リンクではなくスキル名（`web-lookup` スキル）で参照する。
- 注意: 各 SKILL.md の `meta:` は全スカラー文字列。新規なので `version` は初期値、`requires_skills` には動作前提のスキルだけを一方向に書く（`sharing-browser-with-user` → `using-playwright-cli`、my-tools スキル → `using-playwright-cli`）。my-tools スキルの `requires_repo_tools` は `pwq, pwdo`。`meta.tag` が `registry/skill-tags.yaml` の既存タグに収まらなければ同ファイルにタグを足す。
- 注意: `agent-compat-sync` のコピー対象に新プラグインが入るかは `ai-tools.yaml` の設定で決まる。Playwright のスキルは Claude Code 以外でも使えるので、`workspace_copies` に入れるかを 01 の結果で判断する。

## ルール更新ポイント

- `registry/ai-tools.yaml` を先に更新する（SSOT）。
- 新プラグインの `README.md` に、4 スキルの責務分担（`using-playwright-cli` = 認証不要の操作、`sharing-browser-with-user` = 認証が要る区間、docs 2 本 = 公式情報の参照）を書く。
- `maintenance/docs/repo-layout.md` は変えない（置き場所の判定基準どおりに置くため）。

## 進め方

- 実行主体: メインのエージェント。スキル本文の書き換えが終わったら、`audit-skills` スキルで新プラグインを監査してよい（任意）。
- TODO 化: スキル 1 本 = 1 TODO、my-tools スキルで 1 TODO、登録と生成で 1 TODO。skills・tools サブモジュールでそれぞれコミット → アンブレラでポインタと registry・生成物を 1 コミット。
- 確認: 各スキルの download/sync スクリプトが `output/` を作れること、`skill-tools` でスキル一覧に出ること、pre-commit の meta 検査が通ること。
