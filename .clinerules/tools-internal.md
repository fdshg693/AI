---
paths:
  - "tools/internal/**"
---

# 内部ツール

- レポジトリ管理等に使われる、便利ツール群
- 同階層の `justfile` から起動できるようにしておく
- lefthookにも紐づけることで、コミット時に自動実行されるようにする

## フォルダ構成（責務ごと）

- `skill/` — `SKILL.md`そのもの（frontmatterの`meta:`ブロック）を扱うスクリプト。マーケットプレイス登録の有無に関わらずリポジトリ全体を走査する
  - `set/` — フィールドを補完・変更する（`set_skill_versions.py`, `set_skill_descriptions.py`, `bump_skill_versions.py`, `skill_meta_field_fill.py`）
  - `check/` — lefthook等から呼ばれる検査のみのスクリプト（`check_skill_version_bump.py`, `check_skill_repo_tools.py`）
  - `util/` — 上記が共有するヘルパー（frontmatter読み書き、`meta_field.yaml`ローダ、`repo-tools.yaml`ローダ等）
- `plugin_meta/` — `ai-tools.yaml`（SSOT）を起点に、プラグイン・マーケットプレイス・スキルカタログなどの集約メタ情報を生成するスクリプト
  - `generate/` — `marketplace.json`/`skill-catalog.json`/`CATALOG.md`/Cline rules/Copilot instructions/READMEセクションなどを再生成する（すべて`generate_*.py`、丸ごと再生成でマージではない）
  - `util/` — `ai-tools.yaml`ローダ（`ai_tools_config.py`）
- 各スクリプトは`tools/internal`をcwdとして`python -m <package>.<module>`で実行する想定（`justfile`のレシピ、または`uv run --directory tools/internal python -m ...`）。`generate/`配下のスクリプトは`skill/util/`のヘルパーも参照することがある（例: カタログ生成がSKILL.mdのfrontmatterを読む）
- `ai-usage/` — 上記とは独立した自己完結パッケージ（別途`pyproject.toml`を持つ）
