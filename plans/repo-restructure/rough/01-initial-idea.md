---
type: Rough Plan
status: promoted
---

# リポジトリ再編 ラフプラン

## 元の依頼（要約）

- 肥大化したモノレポを、主にフォルダ構造の整理・移動で解決したい。
- モノレポは維持するが Git サブモジュールで区切り、サブフォルダ単位のコミットを容易にする。
- 巨大モノレポを毎回開かず、サブフォルダだけを開いて作業できるようにする。
  - Claude Code 限定で、スキル・ルールをサブフォルダへ Junction で紐づける。
  - 強く結びついた同階層以上の別フォルダ／ファイルも Junction で参照し、サブフォルダ単体で開いても関連ファイルが見えなくならないようにする。
  - サブモジュール単体を clone した場合に Junction の参照先が存在しないのは、利用者の責任として許容する。
- 意味的な分割:
  - レポジトリ都合のスキル（meta-plugins）と汎用スキルを混ぜない。
  - tools に強く紐づくスキルと tools に依存しないスキルを分ける。
  - このレポジトリの都合で行っているマルチ AI エージェント対応と、サンプルとしてのスキルを分ける（例: `_agents/plugins/antigravity-meta/skills` は Claude Code スキルとしても問題なく使える。Antigravity 固有の書き方を示すサンプルは別に切り出す）。
  - Claude Code スキルを主軸にし、他ツールでの書き方の注意点・相違点は別軸でまとめる。
- その他の不一致・混乱もきれいに直す。

## 調査時点で見えた現状（2026-11-10）

- 作業ディレクトリ `c:\C\ai` に `.git` が無い（`git rev-parse` 失敗）。履歴付きの clone が別にあるのか要確認。
- Junction・シンボリックリンクは現状ゼロ。
- スキルの置き場が 9 系統に散っている: `claude-plugins/*`（10プラグイン）、`meta-plugins/`、`codex-plugins/meta`、`copilot-plugins/meta`（direct レイアウト）、`cursor-plugins/meta`、`_agents/plugins/antigravity-meta`、`.cline/skills`、`.kilo/skills`、`.github/skills`（README のみ）。
- 他ツール向けスキルの中身は「そのツールの使い方の知識」で、書式自体は Claude Code でも普通に読める。
- `claude-plugins/my-tools` は tools/ のコンパニオンスキル群。`claude-plugins/meta` は「Claude Code の知識」で、名前が `meta-plugins`・`meta` スキルと紛らわしい。
- 既存の不整合（一部）:
  - `tools/scheule/`（綴り誤り）。`pyproject.toml` の members `tools/schedule`・`tools/issue-agent`・`tools/aim-use/aim-summarize` は実在しない。
  - README が `templates/`・`.clinerules/`・`tools/aim-use/`・`tools/issue-agent/` に言及するが、どれも実在しない。
  - AGENTS.md と lefthook が `.claude/rules/` を参照するが、実在しない。
  - `.agents/README.md` と `_agents/README.md` で Antigravity のプラグイン配置の説明が食い違う。`antigravity-plugins/` は README 1枚だけの空フォルダ。
  - CATALOG.md の位置がプラグインごとに異なる（`skills/CATALOG.md` と `<plugin>/CATALOG.md`）。
  - `.kilo/skills/kilo-test-guide`（空）、`.kilo/skills/using-kilo-cli`（`output` と `__pycache__` だけ）。
  - `.claude/test.json` など、目的不明のファイル。

## 検討した案

| 案 | 内容 | 評価 |
| --- | --- | --- |
| A. 先にサブモジュール化し、後から中身を整理 | 現在のフォルダ単位でそのまま切り出す | × 境界が意味的に間違ったまま固定され、後の移動がリポジトリをまたぐ |
| B. 単一リポジトリ内で意味的再編を済ませ、最後にサブモジュール化 | `git mv` で移動し、既存の生成・検査で確認してから `git filter-repo` で切り出す | ◎ 採用。移動と検証が 1 リポジトリ内で完結する |
| C. サブモジュールではなく sparse-checkout / 複数 worktree | Git 機能だけでサブフォルダ作業を実現 | △ 要件の「サブフォルダ単位のコミット」を満たさない |

| Junction の管理 | 評価 |
| --- | --- |
| Junction 自体をコミット | Git は Junction を追跡できない（実体として追跡されるか無視されるか。要調査） → 不可 |
| マニフェスト（宣言ファイル）をコミットし、スクリプトで作成・検証・除去 | ◎ 採用。Junction パスは `.git/info/exclude` へ自動登録する |

## 迷っている点（詳細プランの「未決事項」へ移した）

- SSOT の yaml（`ai-tools.yaml` 等）をルートに残すか、Junction できるようにディレクトリへ集めるか。Junction はディレクトリ専用なので、ファイル単体はリンクできない。
- 外部契約の破壊: marketplace の source パス、`skill-tools` の GitHub ソースが読むパス、skills-site の URL（canonical ID はパス由来）、README のインストール手順。
- 他ツール向けマニフェスト（`.codex-plugin` 等）を Claude プラグインと同じディレクトリに同居させられるか。
