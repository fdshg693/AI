---
paths:
  - "**"
---

@./README.md

## AIツール/プラグイン設定のSSOT

- AIツール・プラグイン・マーケットプレイス・スキルカタログの所在は `ai-tools.yaml` がSSOT。
- `tools/internal/plugin_meta/generate/generate_*.py` にパスやメタデータをハードコードしない。必ず `tools/internal/plugin_meta/util/ai_tools_config.py` 経由で `ai-tools.yaml` から取得する。
- 新しいプラグインを追加・削除したら、先に `ai-tools.yaml` を更新する。
- README.mdの`<!-- BEGIN: ai-tools-section -->`〜`<!-- END: ai-tools-section -->`は`tools/internal/plugin_meta/generate/generate_readme_tools_section.py`が`ai-tools.yaml`の`readme`ブロックから生成する。手編集しない。

## SKILL.md meta フィールドのSSOT

- `SKILL.md`フロントマターの`meta:`サブフィールド（`version`/`description`/`status`/`requires_skills`等）の定義は`meta_field.yaml`がSSOT。新フィールドを追加・意味を変更する場合は先に`meta_field.yaml`を更新する。
- 新フィールドは全てスカラー文字列（複数値はカンマ区切り、該当なしは`none`）。YAMLリスト値にしない（`tools/internal/skill/util/skill_meta_field.py`の制約）。
- `meta.version`以外のフィールドを変更した場合も、既存の`skill/check/check_skill_version_bump.py`が「frontmatter全体の変更」として検知するため、`meta.version`を1つ上げること。手動で編集してもよいが、`tools/internal/skill/set/bump_skill_versions.py`（`just --justfile tools/internal/justfile skill-version-bump`）で自動バンプできる（末尾の数値セグメントを+1し、`1.2.3-beta`等の接尾辞は落として`1.2.4`にする）。
- 新7フィールドの初回一括判定・再判定は`tools/internal/skill/set/skill_meta_field_fill.py`（`just --justfile tools/internal/justfile skill-meta-fields-fill`）で行う。判断結果は必ず`git diff`でレビューしてからコミットする（lefthookには紐づいていない）。
- 新7フィールドの意味・メンテ手順の詳細は`docs/repo-meta/skill-meta-fields.md`を参照。
- `skills-site`は`meta_field.yaml`をフィールドラベルの表示に読み込み（`skills-site/scripts/meta-field-registry.mjs`）、`requires_skills`/`requires_hooks`/`requires_repo_tools`を詳細ページ上でリンク化する。リンク解決規約（一意ヒットのみリンク化、`requires_repo_tools`はGitHub tree URL等）は`skills-site/AGENTS.md`を参照。
- `SKILL.md`をステージしてコミットする際のpre-commitフックの挙動（生成物再生成・defaultsバックフィル・バンプチェック）と落とし穴は`docs/repo-meta/skill-md-commits.md`を参照。
