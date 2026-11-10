@./README.md

## Behaviour

- `AGENTS.md`の内容に、 `@./...` のような記載があれば、そのパスが差し示すファイルも読みに行くこと。
- `./.../SKILL.md`のような形式であっても、あなたがスキルとして呼び出せるとは限りません。その場合は、ファイルとして直接Readしてください。
- Claude Rule の source は `.claude/rules/`、ネストした `AGENTS.md` の注入は `agent-compat/agent-tooling/agent_tooling/hooks/scenarios/nested_agents_md/` が担当する。両者は独立した入力契約として扱うこと。`.claude/rules/` は現在存在しないが、任意の入力として参照を残している（無ければ Claude Rule の注入が何もしないだけ）。
- エージェントフックの正本は `agent-compat/agent-tooling/agent_tooling/hooks/`。`.claude/hooks/` はインストール先なので直接編集しない。フックの追加・変更は `maintenance/docs/hook-distribution.md` から辿る。
- Junction は各リポジトリのルートの `.links.yaml` で宣言し、`just links-sync` で作る。直接 `mklink /J` しない。Junction を `rm -rf`／`Remove-Item -Recurse` で消さず `just links-clean` を使う。リポジトリを走査するコードは Junction を辿らない。詳細は `maintenance/docs/repo-layout.md`。
- あなた以外のエージェント・ユーザーがこのレポジトリで同時作業することは頻繁に起こります。
  - 自分が行った覚えのない変更を勝手に戻さないように心がけてください。明らかに戻すべき変更である場合のみ、ユーザーの同意の上で、削除を行ってください。

### テクニック

- 複雑なタスクには、積極的にユーザー質問・サブエージェント活用を行って
  - 便利なスキル・関連スキルがたくさんこのレポジトリにあります。複雑なタスクには `maintenance\plugin\skills\discovering-skills\SKILL.md` を積極的に参照してください。
- ツール・スキル変更時は `maintenance\plugin\skills\changing-skills-and-tools\SKILL.md` を参照。
- このレポジトリ全体に関わるようなタスクには `maintenance\plugin\skills\meta\SKILL.md` を参照。
- このリポジトリの全体像・「どこに何があるか」は `maintenance/plugin/skills/exploring-this-repo/SKILL.md`。コードの流れ・定義・呼び出し関係・影響範囲は、grep/Read の前に `codegraph_explore`（MCP）または `codegraph explore`（CLI）。地図は `codegraph status` と `codegraph files` が先。索引が無い／古いときは `codegraph init` または `codegraph sync`。`.codegraph/` はローカル索引で git 管理しない。詳細は `skills/plugins/topics/skills/codegraph-docs/SKILL.md`。

## AIツール/プラグイン設定のSSOT

- AIツール・プラグイン・マーケットプレイス・スキルカタログの所在は `registry/ai-tools.yaml` がSSOT。SSOT yaml（`ai-tools` / `repo-tools` / `meta_field` / `skill-tags` / `repo-workflows` / `repo-hooks`）は `registry/` に置く。ルート直下の同名 yaml 4 本は旧 skill-tools 向けの生成コピーで、手編集しない。
- 新しいプラグインを追加・削除したら、先に `registry/ai-tools.yaml` を更新する。
- `./README.md` の `<!-- BEGIN: ai-tools-section -->`〜`<!-- END: ai-tools-section -->` は `maintenance/scripts/plugin_meta/generate/generate_readme_tools_section.py` が `ai-tools.yaml` の `readme` ブロックから生成する。手編集しない。

## SKILL.md meta フィールドのSSOT

- `SKILL.md`フロントマターの`meta:`サブフィールド（`version`/`description`/`status`/`requires_skills`等）の定義は`registry/meta_field.yaml`がSSOT。
  - 新フィールドを追加・意味を変更する場合は先に`registry/meta_field.yaml`を更新する。
- 新フィールドは全てスカラー文字列（複数値はカンマ区切り、該当なしは`none`）。YAMLリスト値にしない（`maintenance/scripts/skill/util/skill_meta_field.py`の制約）。
- `meta.version`以外のフィールドを変更した場合も、既存の`skill/check/check_skill_version_bump.py`が「frontmatter全体の変更」として検知するため、`meta.version`を1つ上げること。
  - 手動で編集してもよいが、`maintenance/scripts/skill/set/bump_skill_versions.py`（`just --justfile maintenance/scripts/justfile skill-version-bump`）で自動バンプできる（末尾の数値セグメントを+1し、`1.2.3-beta`等の接尾辞は落として`1.2.4`にする）。
- 新7フィールドの初回一括判定・再判定は`maintenance/scripts/skill/set/skill_meta_field_fill.py`（`just --justfile maintenance/scripts/justfile skill-meta-fields-fill`）で行う。
  - 判断結果は必ず`git diff`でレビューしてからコミットする（lefthookには紐づいていない）。
  - 新7フィールドの意味・メンテ手順の詳細は`maintenance/docs/skill-meta-fields.md`を参照。
- コミット時は `maintenance\plugin\skills\committing\SKILL.md` を参照。

## コマンド

- このレポジトリは`mise・uv・pnpm・just`で管理されている。
- `npm, python`は直接使わず、`pnpm`/`just`/`uv`を使うこと。
