# 05 実行記録（意味的再編）

## コミット

| コミット              | 内容                                                                                                                                                                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `eedb18e`             | バッチ 1: `meta-plugins` → `maintenance/plugin`、`tools/internal` → `maintenance/scripts`、`docs/repo-wide` → `maintenance/docs`、`skill-maintenance` → `maintenance/plugin/skills`、`tools/internal/ai-usage` → `tools/ai-usage`。書き換えツール `maintenance/scripts/reorg/` |
| `7ea846d` + `38a1861` | バッチ 2: SSOT yaml 6 本 → `registry/`。読み手を全部 `registry/` へ。skill-tools は `registry/` 優先・ルートへフォールバック（`skill_tools/registry.py`）。旧 skill-tools 向けのルート生成コピー 4 本                                                                          |
| `c5375e1` + `c6b49f3` | バッチ 3: `claude-plugins/my-tools`・`task-tracker`・`parallel-agent-worktree` → `tools/_plugin/my-tools`。`tav-lit` は `my-tools-no-install` へ（バッチ 4 で web-lookup）。`bump_tool_versions.py` の cp932 デコード不具合を修正                                              |
| `ed9c81a` + `c46aecc` | バッチ 4: `claude-plugins/*` → `skills/plugins/*`。`meta` → `cc-knowledge`、`my-tools-no-install` → `web-lookup`＋`doc-tools`、`claude-plugins/README.md` 削除。REFERENCES.md の相対リンクの深さを修正                                                                         |
| `f5c4a39`             | 置き場所の判定基準を `maintenance/docs/repo-layout.md` に正本化、exploring-this-repo の地図                                                                                                                                                                                    |

バッチ 5 は計画どおり 06 と同じコミットで行う。バッチ 6（CATALOG.md の位置統一）は、Copilot 以外は既に `<plugin>/skills/CATALOG.md` で、残る Copilot（`skills_layout: direct`）はバッチ 5 で移るため 06 へ回した。

## 決めたこと

- **`claude-code` は使えない**: `claude plugin validate` が `claude-` で始まるプラグイン名を予約語として拒否する。ユーザー回答で `cc-knowledge`（フォルダも同名）にした。06 の `ai-tools-knowledge` など新しい名前も validate で確かめる。
- **registry/ の互換**: yaml 内のパスは置き場所によらずリポジトリルート相対と定義し直した（`repo-hooks.yaml` の `catalog` は「このファイルからの相対」だったが、ルートにあったので意味は同じ）。旧 skill-tools 向けにルートへ `ai-tools.yaml`・`repo-tools.yaml`・`repo-workflows.yaml`・`repo-hooks.yaml` の生成コピーを置く（`plugin_meta/generate/generate_registry_compat.py`、pre-commit の `registry-compat` タスク）。`meta_field.yaml`・`skill-tags.yaml` は skill-tools が読まないのでコピーしない。
- **agents-rules・agent-tooling**: agents-rules は `registry/ai-tools.yaml` を先に探す。agent-tooling の `_repo_tool_keys` は固定の深さをやめて親を辿って `registry/repo-tools.yaml` を探す（06 で agent-tooling が 1 段深くなっても直さなくてよい）。
- **書き換えツール**: `maintenance/scripts/reorg/rewrite_moved_paths.py`（移動表 `reorg/tables/*.json`）。相対 Markdown リンクは「移動前の位置で解決 → 表で写像 → 移動後の位置から再計算」、ルート相対の言及は前置きがパス文字でない箇所だけ置換。`links_only` で後者を止められる（バッチ 2 で `ai-tools.yaml` の素の名前を残すのに使用）。内容が変わった SKILL.md は版数を上げる。`reorg/check_links.py` で移動前後の切れリンクを比較した（141 → 111。残りは全て移動前からの既存の切れで、URL のプレースホルダや外部由来の文書）。

## 計画との差分

- バッチ 1 の「深さが変わらないので `parents[N]` はそのまま」は `meta-plugins` には当てはまらなかった（`meta-plugins/skills/x` → `maintenance/plugin/skills/x` で 1 段深い）。`list_repo_meta_docs.py`・`snapshot_indexed_layout.py` を `parents[5]` に直した。`tools/internal` → `maintenance/scripts` は計画どおり同じ深さ。
- `check_skill_version_bump` は frontmatter だけでなく本文の変更でもバンプを要求した（05 の注意書きと違う）。書き換えツールは内容が変わった SKILL.md を全部バンプするようにした。
- `docs/log.md` は履歴なので書き換え対象から外した。OKF の絶対リンク `/repo-wide/x.md`（`docs/` バンドル基準）は `maintenance/docs/` が `docs/` の外へ出たので `./x.md` にした。
- skill-tools のテスト内の偽リポジトリ（`meta-plugins/` を「未登録の領域」として作る）は書き換えずに戻した。
- `doc-transcription` は uv workspace のメンバーではなく自分の uv プロジェクトなので、テストは `uv run --project` で回す（ルートの `uv run pytest` では pypdf が無く収集エラーになる。移動前から同じ）。

## 追跡外ファイル・リポジトリ外

- `git mv` でディレクトリごと動かしたので、追跡外ファイル（`discovering-skills/logs/`、`task-tracker/memo/`、`ona-run/check/local-secrets-template.local.md`、`tav-lit/.env`、`web-lookup/.env`、各 `output/temp/` 等）も一緒に移った。旧フォルダは残っていない。
- `.venv` 2 つ（web-lookup、doc-transcription）は移動後に消し、`uv run --project` で作り直した。
- ユーザー確認のうえ: `~/.claude/settings.json` の `statusLine` を `python C:/C/ai/tools/ai-usage/statusline_hook.py` に、`uv tool install --editable tools/ai-usage --force`、`uv tool uninstall skill-deploy`。

## 検証

- 各バッチで: `uv run pytest`（maintenance/scripts、skill-tools、agents-rules、agent-tooling、skills/plugins。最終 447 + agent-tooling 248 + doc-transcription 37 passed）、`precommit-check --all`、`just skills-site-check`（39 passed）、`just links-check`、`check_links` の差分、lefthook 付きコミット。
- バッチ 4 後に `claude plugin validate` を全プラグインとマーケットプレイスで実行し、すべて通過（警告は author・icon の未設定のみ）。
- tools-site の `generate` が `registry/repo-tools.yaml` から 8 ページを生成することを確認。
