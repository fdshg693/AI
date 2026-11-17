---
type: Plan Step
status: planning-breakdown
---

# Step 3: ログ仕様の知識スキル

> [02-research-log-formats.md](02-research-log-formats.md) の続き。Step2 の調査結果を、ツールに依存しない知識として残す。

## やること

各 AI コーディングツールのローカルログ仕様（所在・形式・レコード構造・注意点）を知識スキルとして書く。Claude Code は既存の `claude-logs-investigate` に参照ファイルを足し、他ツールは `ai-tools-knowledge` にツールごとの新スキルを作る。Step4 の CLI はここを仕様の正本として参照する。

## 読むべきファイル・実行推奨Grep

**書き方の基準（優先度: 高）**

- 読む: `skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md` と `bestpractices.md` — SKILL.md の書き方
- 読む: `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md`・`otel-reference.md` — 追記先の既存構成と参照ファイルの粒度
- 読む: `skills/plugins/ai-tools-knowledge/skills/cursor-memory/`・`kilo-memory-guide/` — 他ツール知識スキルの命名・frontmatter・`requires_skills` の付け方
- 読む: `registry/meta_field.yaml`・`maintenance/docs/skill-meta-fields.md` — meta フィールド

**配布への影響（優先度: 中）**

- 読む: `registry/ai-tools.yaml` の `workspace_copies`（`include: ["cline-*"]` 等）— 新スキル名が Cline・Kilo・Antigravity 向けコピーに入るか
- 読む: `skills/plugins/ai-tools-knowledge/skills/CATALOG.md`・`skills/plugins/cc-knowledge/skills/CATALOG.md` — 生成カタログ（手編集しない）

## 触るファイル

### 新規

- `skills/plugins/ai-tools-knowledge/skills/cursor-logs/SKILL.md`（＋必要なら `format.md`）
- `skills/plugins/ai-tools-knowledge/skills/cline-logs/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/kilo-logs/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/antigravity-logs/SKILL.md`
- `skills/plugins/ai-tools-knowledge/skills/codex-logs/SKILL.md`
- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/log-format.md` — ローカルログのファイル別仕様

### 変更

- `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md` — `log-format.md` への導線、`meta.version` を上げる
- 生成物（各 `CATALOG.md`・`.claude-plugin/skill-catalog.json` 等）は pre-commit・生成スクリプトに任せる

## 決定事項・注意点／落とし穴

| 決定・注意 | 理由 |
| ---------- | ---- |
| 他ツールはツールごとに `<tool>-logs` スキルを新設し、既存の `*-docs`（公式ドキュメント全般）には混ぜない | 既存の `*-memory`・`*-cli-use` と同じ「関心ごとに 1 スキル」の粒度。ログ調査で発火させやすい description にできる |
| Claude Code は新スキルを作らず `claude-logs-investigate` に参照ファイルを足す | 既にローカルログの所在を扱っており、スキルが重複する |
| 各スキルは「公式に記載あり」と「実データからの推定（バージョン依存・未保証）」を節で分け、確認したバージョンと日付を書く | 非公開形式は予告なく変わる。CLI が壊れたときの切り分けに使う |
| 会話本文・秘密情報を含む実ログをサンプルとして貼らない。構造は架空値で示す | スキルは公開サイト・マーケットプレイスで配布される |
| スキル本文に agent-logs CLI の使い方は書かない（`requires_skills` にも入れない）。CLI 側スキルから知識スキルを参照する一方向 | 知識スキルはツール非依存に保つ（[tool-companion-skills](../../maintenance/docs/tool-companion-skills.md)） |
| `cline-logs` は `workspace_copies` の `cline-*` に入って `.cline/skills/` へコピーされる。Kilo・Antigravity の include パターンも確認し、必要なら `ai-tools.yaml` に足す | 各ツールで自分のログを調べる場面がある |

## ルール更新ポイント

- 新規ルールは不要。`ai-tools-knowledge` の README・カタログに一覧があれば生成に任せる。
- `agent-compat/.links.yaml` に `_umbrella/cc-knowledge`（→ `skills/plugins/cc-knowledge`）を足すかは Step5 で判断（agent-compat を単体で開いて CLI を直すとき Claude Code の仕様を参照できるように）。

## 進め方

- **実行主体**: メインエージェント。スキル 1 本ずつの下書きはサブエージェントに委任してよいが、Step2 の要約だけを渡し、実データを読み直させない。
- **TODO化**: スキル 1 本 = 1 項目（計 6）。skills サブモジュールでまとめて 1 コミット、アンブレラでポインタ更新。
