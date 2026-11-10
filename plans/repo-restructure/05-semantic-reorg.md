---
type: Plan Step
status: implementing-done
---

# Step 5: 単一リポジトリのまま意味的再編（git mv）

> [00-overview.md](00-overview.md) の続き。01 の go/no-go 判定、02 の対応表（ユーザー確認済み）、03 の修正、04 の Junction 安全な走査を前提にする。サブモジュール化はまだしない。

## やること

02 の対応表どおりに、カテゴリ単位のバッチで `git mv` し、そのたびに SSOT・生成器・CI・site・ドキュメントの参照を追従させて、既存の検査が通る状態でコミットする。バッチ順（案）:

対応表の正本は [progress/02-mapping.md](progress/02-mapping.md)（ユーザー確認済み）。

1. **repo-meta の集約**: `meta-plugins/` → `maintenance/plugin/`、`tools/internal/`（`ai-usage` を除く）→ `maintenance/scripts/`、`docs/repo-wide/` → `maintenance/docs/`。`claude-plugins/meta/skills/skill-maintenance` も `maintenance/plugin/skills/` へ移す。`tools/internal/ai-usage` は `tools/ai-usage` へ移す（ユーザー回答）。どちらの移動も深さが変わらないので、`parents[N]` はそのままでよい。
2. **SSOT yaml**: ルートの yaml（`ai-tools.yaml`、`repo-tools.yaml`、`meta_field.yaml`、`skill-tags.yaml`、`repo-workflows.yaml`、`repo-hooks.yaml`）を `registry/` へ移す。skill-tools は source のルート直下にある `ai-tools.yaml`・`repo-tools.yaml`・`repo-workflows.yaml`・`repo-hooks.yaml` をファイル名固定で読む（`catalog/__init__.py:78`、`repo_tools/load.py:24`、`workflows/__init__.py:17`、`hooks/catalog.py:28`）。このため移行措置を同じバッチで入れる。案は、新版は `registry/` を先に探し、ルートにも当面の互換用ファイルを残す。`tools/agents-rules/agents_rules/generate.py:16` は `ai-tools.yaml` をルート判定にも使っているので、直す。
3. **tools 付属スキル**: `claude-plugins/my-tools/` → `tools/_plugin/my-tools/`。ただし `tav-lit` は除き、バッチ 4 で `web-lookup` へ移す。`coding/skills/task-tracker` と `coding/skills/parallel-agent-worktree` も `tools/_plugin/my-tools/skills/` へ移す（ユーザー回答。名前空間が `coding:` から `my-tools:` に変わる）。`tools/skill-tools/skill_tools/config/__init__.py:23` の `DEFAULT_SELF_SKILL`、`skill-tools.yaml.example`、`tests/test_cli.py` を同時に直す。
4. **汎用スキル**: `claude-plugins/*` → `skills/plugins/*`。`claude-plugins/meta` は `skills/plugins/claude-code` に改名する（`meta-plugins`・`meta` スキルとの混同を解消）。`my-tools-no-install` は 2 つに分ける: `skills/plugins/web-lookup`（web-lookup と、my-tools から移す tav-lit）と `skills/plugins/doc-tools`（doc-transcription）（ユーザー回答）。`special` はそのまま移す。`claude-plugins/README.md` は削除する。
5. **他ツールの知識スキル**: `codex-plugins/meta/skills/*`、`copilot-plugins/meta/*`、`cursor-plugins/meta/skills/*`、`_agents/plugins/antigravity-meta/skills/*`、`.cline/skills/*`、`.kilo/skills/*` → `skills/plugins/ai-tools-knowledge/skills/<tool>-*`。**06 の配布方式（生成器）と同じコミットで行う**。分けると、その間 Cline 等がスキルを見失い、`ai-tools.yaml` の `workspace` 系の生成も壊れる。ツール固有書式のサンプル部分の切り出しは 06 の後半で行う。
6. **CATALOG.md の位置統一**: すべて `<plugin>/skills/CATALOG.md` に揃え、生成器を合わせる（cursor は 03 で `skills_layout: subdir` にし、既に `cursor-plugins/meta/skills/CATALOG.md`）。

## 読むべきファイル

### SSOT と生成器（最優先。移動のたびに追従させる）

- `ai-tools.yaml` と `tools/internal/plugin_meta/util/ai_tools_config.py`（パスはここ経由で読む規約）
- `tools/internal/plugin_meta/generate/*.py`（marketplace、skill-catalog、README 節、Copilot marketplace）
- `repo-tools.yaml` と `tools/internal/skill/check/check_skill_repo_tools.py`（`meta-plugins/**` と `tools/internal/**` を除外するロジックはパス直書き）
- `meta_field.yaml`、`docs/repo-wide/skill-meta-fields.md`（`requires_skills` 等の値は canonical ID＝パス）
- `repo-workflows.yaml`（skill パスを直接参照）

### 利用側

- `site/skills-site/scripts/*.mjs`（収集元・URL 生成）、`site/skills-site/AGENTS.md`
- `.github/workflows/skill-site.yml`（`paths:` フィルタ）、`tool-release.yml`
- `tools/skill-tools/skill_tools/config/__init__.py`（`DEFAULT_SELF_SKILL`）、`tools/skill-tools/skill_tools/` の source 解決
- `lefthook.yml`、`tools/internal/precommit/__main__.py`、ルート `justfile`、`tools/internal/justfile`
- `pyproject.toml`（`claude-plugins/meta/skills/writing-skill-web` が uv member）、`pnpm-workspace.yaml`
- `.claude/workflows/audit-skills.js`（`claude-plugins/meta/skills/writing-skill/bestpractices.md` を直書き）
- [progress/02-mapping.md](progress/02-mapping.md) の「3. パス参照の棚卸し」全件（252 ファイル）。動作に効く参照は「種類別」の箇条に列挙済み

### 書き換えの道具

- `temp/rewrite_moved_paths.py`（過去の移動で使ったパス書き換えスクリプト）。走査・改行保持・SKILL.md の版数バンプはそのまま使う。`transform()` を対応表から作る「旧プレフィクス → 新プレフィクス」表（長い順、`/` と `\` の両表記）に置き換え、`rglob` を `git ls-files` に替えて `maintenance/scripts/` に置く

## 触るファイル

- 移動: [progress/02-mapping.md](progress/02-mapping.md) の対応表の全行（他ツールの知識スキルは 06 と同じコミット）
- 変更: 上の「読むべきファイル」の全ファイル、全 SKILL.md の本文リンク・`meta.requires_skills`、`docs/**`、ルート `AGENTS.md`（パス参照のみ暫定更新）
- 変更: 移動した SKILL.md の `meta.version`（frontmatter を触ったものは `just --justfile tools/internal/justfile skill-version-bump`）
- 再生成: `.claude-plugin/marketplace.json`、`skill-catalog.json`、`.agents/plugins/marketplace.json`、`.github/plugin/marketplace.json`、各 CATALOG.md、README の ai-tools 節
- 削除: 空になった旧ルートフォルダ（`claude-plugins/`、`meta-plugins/`、`codex-plugins/` ほか）

## 決定事項・注意点／落とし穴

- **外部契約**: 次は旧パスで使っている外部利用者がいる。各バッチで移行措置を決める。
  - Claude marketplace（`fdshg693/AI` の `.claude-plugin/marketplace.json`）: プラグイン名は変えず `source` だけ変える。名前を変えるもの（`meta` → `claude-code`）は、インストール済み利用者への影響を README に書く。
  - `skill-tools` の GitHub ソース: 既定パスとカタログの所在をまとめて更新し、新旧両方を一定期間読めるかを検討する。
  - skills-site の URL: canonical ID が変わる。URL の変更は許容し、リダイレクトは作らない（ユーザー回答）。
  - `skill-tools --fb` の既存保存ディレクトリ（スキル名単位）はパスではなく名前なので影響なし。改名したスキルだけ確認する。
- **版数バンプ**: パス書き換えで frontmatter を触ったスキルは `meta.version` を上げないと `check_skill_version_bump.py` が落ちる。本文だけの変更は対象外。一括バンプ後に `git diff` で確認する。
- **バッチは小さく**: 1 バッチ = 1 コミット。各バッチ後に、pre-commit の fix／check、`uv run pytest`（影響範囲）、`just skills-site-check`、`claude plugin validate`（各プラグイン）を通す。
- **並行作業**: 移動中に他のエージェントが旧パスへ書き込むと衝突する。バッチ前にユーザーへ告知し、短時間で終える。
- `.claude/hooks/` はインストール先なので直接編集しない。フックのソースパスが変わる場合は `agent-tooling` 側を直して `just hooks-install` で反映する（06 で `agent-tooling` 自体が動く）。
- `claude-plugins/meta/skills/writing-skill-web`（→ `skills/plugins/claude-code/skills/`）と `tools/internal/ai-usage`（→ `tools/ai-usage`）は uv workspace member。移動後に `pyproject.toml` の members と `uv.lock` を更新する。
- **名前空間の変更**: `meta:` → `claude-code:`、`my-tools-no-install:` → `web-lookup:`／`doc-tools:`、`coding:task-tracker`・`coding:parallel-agent-worktree` → `my-tools:`、`my-tools:tav-lit` → `web-lookup:`。インストール済み利用者は再インストールが要るので、README と `docs/integrations/claude-code.md` に書く。`issue-triage`（`/github-action:issue-triage`）の名前は変えない。
- **他スキルの output をパスで読む設定**: `claude-plugins/topics/skills/ona-cli-docs/config.yml:10`、`copilot-plugins/meta/vscode-copilot-docs/config.yml:10`。プラグインが分かれても相対関係が保たれるよう、移動のたびに直す。
- **追跡外ファイル**: `git mv` は ignore 対象（`.env`、`.venv`、`logs/`、`fb/`、`state/`、sqlite 等。02 の一覧）を動かさない。移す対象の一覧は [progress/02-mapping.md](progress/02-mapping.md) の「追跡外ファイル」節にある。各バッチで旧パスに残ったものを新パスへ手で移し、旧フォルダが本当に空かを確認してから消す。`.venv` は移さず作り直す。
- **リポジトリ外の参照**（バッチ 1）: `~/.claude/settings.json` の `statusLine` は既に存在しないパス（`C:/CodeRoot/AI/tools/internal/ai-usage/statusline_hook.py`）を指しているので、`tools/ai-usage` へ移した後に直す。`ai-usage-cli` は `uv tool install --editable tools/ai-usage --force` で入れ直す。`skill-deploy`（editable 先の `tools/skill-deploy` が実在しない）はアンインストールを提案する。`extraKnownMarketplaces`（`C:\C\ai`）とタスクスケジューラ（登録なし）は影響しない。いずれもユーザー環境の変更なので確認を取る。

## ルール更新ポイント

- ルート `AGENTS.md`（各バッチ）: `meta-plugins\skills\...` などの直書きパスを新パスへ。
- `maintenance/docs/ai-tools-config.md`・`tool-companion-skills.md`・`claude-code-first-skills.md`・`tools-directory-layout.md`・`uv-workspace.md`（該当バッチ）: 置き場所の記述を新構成へ。
- `maintenance/docs/skill-tools-contract.md`・`skill-meta-fields.md`（バッチ 4・5）: 外部契約の変更点と移行措置、canonical ID の変化。
- `maintenance/docs/repo-ssot-pattern.md`・`repo-tools-config.md`（バッチ 2）: SSOT yaml の新しい所在。
- 移動したネストの `AGENTS.md`／`CLAUDE.md`（`tools/internal/`、`docs/`、`agent-tooling/`、`.claude/hooks/` 等）（該当バッチ）: 中のパス参照。
- `maintenance/plugin/skills/exploring-this-repo`、`changing-skills-and-tools`、`discovering-skills`（最終バッチ）: リポジトリ地図とスキル置き場の説明。
- `maintenance/docs/repo-layout.md`（最終バッチ）: カテゴリの判定基準（02 の基準を正本化）。

## 進め方

- **実行主体**: `git mv` と SSOT・生成器の修正はメイン。パス書き換えはスクリプトで一括、Markdown の文脈依存の書き換え（説明文の言い回し）だけをサブエージェントへ委任してよい。各バッチの検査結果はメインが確認する。
- **TODO 化**: バッチ 1〜6 をそれぞれ 1 TODO・1 コミット。各 TODO の完了条件は「全検査が通り、旧パスの `rg` 結果が意図した残存（履歴・changelog 等）だけ」。
- **コミット**: 各バッチの完了条件を満たした時点で、`git mv` と参照の追従を同じ 1 コミットにする（`refactor(repo): move ...`。移動と追従を分けると、間のコミットで検査が壊れる）。バッチ 5 は 06 の配布方式と同じコミット。追跡外ファイルの移設はコミットに現れないので、progress に記録する。ステップ完了時にプラン更新を 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（02 完了時）: 02 の対応表（ユーザー確認済み）を反映した。変えたのは、バッチ 1〜4 の移動先、skill-tools の SSOT ファイル名固定への移行措置、名前空間の変更、追跡外ファイルとリポジトリ外参照の具体名、書き換えスクリプトの方針。
- 2026-11-10（04 完了時）: 04 の成果物も移動対象に入る。`tools/internal/links/` → `maintenance/scripts/links/`（`skill/util/skill_frontmatter.py` と生成器 3 本が `from links.fs import ...` するので、tools/internal と一緒に動かせば import はそのまま）、`docs/repo-wide/repo-layout.md` → `maintenance/docs/repo-layout.md`。ルート `justfile` の `links-*`・`lefthook.yml` の `post-checkout` ジョブ・ルート `AGENTS.md`・`conftest.py` の docstring にあるパスを追従させる。実ディレクトリだったパスを Junction にするバッチでは、`links-check` が「過去に追跡されていたパス」を警告する（想定どおり）。
- 2026-11-10（05 完了時）: バッチ 1〜4 を実施（記録は [progress/05-reorg-results.md](progress/05-reorg-results.md)）。`claude-code` は予約語でプラグイン名に使えず `cc-knowledge` に変更（ユーザー回答）。バッチ 1 の `meta-plugins` は深さが 1 段増えた。本文だけの変更でも SKILL.md のバンプが要る。registry/ はルートに旧 skill-tools 向けの生成コピーを置く方式にした。バッチ 6 は Copilot 以外が既に揃っており、残りは 06 へ回した。
