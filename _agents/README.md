# \_agents フォルダ使い方

`.agents` フォルダは Codex にも Antigravity にも使われるため、Antigravity 用プラグインはこの `_agents` に分けて置く（[.agents/README.md](../.agents/README.md) 参照）。

## 使い分け

- Codex は `.agents\plugins\marketplace.json` のマーケットプレイスから、`codex-plugins/` にあるプラグインを読み込む
- Antigravity 用プラグインは `.agents\plugins` でなく `_agents\plugins\<plugin-name>\` に配置する
