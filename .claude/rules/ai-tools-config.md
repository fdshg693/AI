---
paths:
  - "ai-tools.yaml"
  - "tools/internal/**"
  - "README.md"
---

## AIツール/プラグイン設定のSSOT

- AIツール・プラグイン・マーケットプレイス・スキルカタログの所在は `ai-tools.yaml` がSSOT。
- `tools/internal/plugin_meta/generate/generate_*.py` にパスやメタデータをハードコードしない。必ず `tools/internal/plugin_meta/util/ai_tools_config.py` 経由で `ai-tools.yaml` から取得する。
- 新しいプラグインを追加・削除したら、先に `ai-tools.yaml` を更新する。
- README.mdの`<!-- BEGIN: ai-tools-section -->`〜`<!-- END: ai-tools-section -->`は`tools/internal/plugin_meta/generate/generate_readme_tools_section.py`が`ai-tools.yaml`の`readme`ブロックから生成する。手編集しない。
