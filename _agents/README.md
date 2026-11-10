# \_agents フォルダ使い方

`.agents` フォルダは Codex にも Antigravity にも使われるため、Antigravity 用プラグインはこの `_agents` に分けて置く（[.agents/README.md](../.agents/README.md) 参照）。

## 使い分け

- Codex は `.agents\plugins\marketplace.json` のマーケットプレイスから、`skills/plugins/ai-tools-knowledge`（`.codex-plugin/plugin.json` を同梱）を読み込む
- Antigravity 用プラグインは `.agents\plugins` でなく `_agents\plugins\<plugin-name>\` に配置する
- `_agents/plugins/antigravity-meta/` は `skills/plugins/ai-tools-knowledge` の Antigravity 関連スキルのコピー。gitignore 済みで、`just agent-compat-sync` で作る（`registry/ai-tools.yaml` の `workspace_copies`）。手編集しない
