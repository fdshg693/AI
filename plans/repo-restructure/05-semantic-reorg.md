---
type: Plan Step
status: planning-research
---

# Step 5: 単一リポジトリのまま意味的再編（git mv）

> [00-overview.md](00-overview.md) の続き。01 の go/no-go 判定、02 の対応表（ユーザー確認済み）、03 の修正、04 の Junction 安全な走査を前提にする。サブモジュール化はまだしない。

## やること

02 の対応表どおりに、カテゴリ単位のバッチで `git mv` し、そのたびに SSOT・生成器・CI・site・ドキュメントの参照を追従させて、既存の検査が通る状態でコミットする。バッチ順（案）:

1. **repo-meta の集約**: `meta-plugins/` → `maintenance/plugin/`、`tools/internal/` → `maintenance/scripts/`、`docs/repo-wide/` → `maintenance/docs/`。02 で repo-meta と判定された `claude-plugins` 内のスキル（`skill-maintenance` 等）も `maintenance/plugin/skills/` へ移す。
2. **SSOT yaml**: ルートの yaml（`ai-tools.yaml`、`repo-tools.yaml`、`meta_field.yaml`、`skill-tags.yaml`、`repo-workflows.yaml`、`repo-hooks.yaml`）を `registry/` へ移す。外部契約（`skill-tools` の GitHub ソースが読む所在など）の移行措置を同じバッチで入れる。
3. **tools 付属スキル**: `claude-plugins/my-tools/` → `tools/_plugin/my-tools/`。02 で tool-companion と判定された他プラグイン内のスキルもここへ移す。
4. **汎用スキル**: `claude-plugins/*` → `skills/plugins/*`。`claude-plugins/meta` は `skills/plugins/claude-code` に改名する（`meta-plugins`・`meta` スキルとの混同を解消）。`my-tools-no-install` は中身に合わせて改名する（例: `web-lookup`）。
5. **他ツールの知識スキル**: `codex-plugins/meta/skills/*`、`copilot-plugins/meta/*`、`cursor-plugins/meta/skills/*`、`_agents/plugins/antigravity-meta/skills/*`、`.cline/skills/*`、`.kilo/skills/*` → `skills/plugins/ai-tools-knowledge/skills/<tool>-*`。**06 の配布方式（生成器）と同じコミットで行う**。分けると、その間 Cline 等がスキルを見失い、`ai-tools.yaml` の `workspace` 系の生成も壊れる。ツール固有書式のサンプル部分の切り出しは 06 の後半で行う。
6. **CATALOG.md の位置統一**: すべて `<plugin>/skills/CATALOG.md` に揃え、生成器を合わせる。

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
- 02 で作ったパス参照一覧の全件

### 書き換えの道具

- `temp/rewrite_moved_paths.py`（過去の移動で使ったパス書き換えスクリプト。再利用して汎用化を検討）

## 触るファイル

- 移動: 02 の対応表の全行
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
- `claude-plugins/meta/skills/writing-skill-web` と `tools/internal/ai-usage` は uv workspace member。移動後に `pyproject.toml` の members と `uv.lock` を更新する。
- **追跡外ファイル**: `git mv` は ignore 対象（`.env`、`.venv`、`logs/`、`fb/`、`state/`、sqlite 等。02 の一覧）を動かさない。各バッチで旧パスに残ったものを新パスへ手で移し、旧フォルダが本当に空かを確認してから消す。`.venv` は移さず作り直す。
- **リポジトリ外の参照**: `~/.claude/settings.json` の `statusLine`（`tools/internal/ai-usage/statusline_hook.py`）と `extraKnownMarketplaces`、タスクスケジューラ、editable インストールは、該当バッチで直す。ユーザー環境の変更なので確認を取る。

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
