# .agents フォルダ使い方

`.agents` フォルダは Codex にも Antigravity にも使われるため、使い分けが必要

- Codex は `.agents\plugins\marketplace.json` のマーケットプレイスから、`codex-plugins/`にあるプラグインを読み込む
- Antigravity は `.agents\plugins` でなく `_agents\plugins` にプラグインを配置
- `.agents\rules\*.md` は Antigravity のワークスペース Rules。リポジトリ各所の `AGENTS.md` から
  `tools/internal/plugin_meta/generate/generate_antigravity_rules.py`（lefthookの`pre-commit`で
  `**/AGENTS.md`変更時に自動実行）が生成する。手編集しない。ルート直下のAGENTS.mdは
  `trigger: always_on`、それ以外は対象ディレクトリにスコープした`trigger: glob`で生成される。
  frontmatterキー名の根拠は
  [_agents/plugins/antigravity-meta/skills/antigravity-memory/SKILL.md](../_agents/plugins/antigravity-meta/skills/antigravity-memory/SKILL.md)
  を参照（公式ドキュメント未記載のため、IDEでの生成結果を確認して採用したもの）。
