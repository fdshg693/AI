# 06 実行記録（マルチ AI 対応の分離）

## コミット

| コミット                          | 内容                                                                                                                                                                                                                                                                    |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `c9f3427` + `77936dc` + `22ba1bd` | TODO 1: `agent-tooling/` → `agent-compat/agent-tooling/`。最初のコミットは `git add` が消えたパスで中断し、リネームだけが入った。パスの追従は直後のコミットで入れた（履歴は書き換えていない）。tests の `parents[2]` → `[3]`、uv workspace の members、lefthook の glob |
| `dd6bdb6` + `2d30d3a`             | TODO 2 ＋ 05 バッチ 5: 知識スキル 42 件 → `skills/plugins/ai-tools-knowledge/skills/`、`cline-plugins/personal-info` → `agent-compat/formats/cline/`。配布方式（下記）と生成器                                                                                          |
| `49e1a93`                         | TODO 3: `agent-compat/formats/<tool>/` のサンプル、`agent-compat/` の README・AGENTS.md・CLAUDE.md、`formats/.format-samples`                                                                                                                                           |
| `efd3118`                         | TODO 4: `agent-compat/docs/differences/`（ツール別 6 件と比較表の index）                                                                                                                                                                                               |
| `1222f1d` + `7fc8e8f`             | TODO 5: 知識スキル本文の古いリポジトリ構成の記述を削除、Kilo の壊れた YAML 例を復元、copilot-writing-\* の frontmatter `name` をフォルダ名に合わせた                                                                                                                    |

## 決めたこと（ユーザー回答 2026-11-10）

- **配布方式**: 共有プラグイン＋マニフェスト。`skills/plugins/ai-tools-knowledge` 1 つに `.claude-plugin/`・`.codex-plugin/`・`.cursor-plugin/` とルートの `plugin.json`（Copilot。`"skills": "skills/"`）を同居させる。Codex・Cursor・Copilot は 42 件すべてを入れる（Copilot の skills 配列での絞り込みは、配列の意味が知識スキルから確定できなかったのでやめた）。
- **ワークスペース直下のコピー**: gitignore して生成。`.cline/skills/`・`.kilo/skills/`・`_agents/plugins/antigravity-meta/` を `just agent-compat-sync`（`generate_workspace_copies.py`）で作る。pre-commit も `skills/plugins/ai-tools-knowledge/**` の変更で作り直す。

## 計画との差分

- **スキルルートは 1 ツールにだけ登録する**: skill-tools が同じスキルルートの重複登録を拒否する。そのため `ai-tools-knowledge` は `claude-code` の `plugins` にだけ載せ、他ツールの `plugins` は空にした（Copilot の `.github` workspace だけ残る）。他ツールへの届け先は新しいキーで表す。`marketplace.sources`（Codex・Copilot）と `workspace_copies`（Cline・Kilo・Antigravity）。skills-site では、これらの知識スキルが「Claude Code / ai-tools-knowledge」として表示される。
- **マニフェストは生成物でなく、プラグインと一緒に手で保守する**: 計画は「各ツールのマニフェストは生成物」だった。集約生成物はアンブレラが持ち、サブモジュール内のファイルをアンブレラの生成器が書き換えないという方針（00 の決定事項）を優先した。生成するのはマーケットプレイス（`.agents/plugins/marketplace.json`・`.github/plugin/marketplace.json`）だけ。旧 `copilot-plugins/meta/plugin.json` の生成と ai-tools.yaml の `plugin_json_output_path`・`plugin` ブロックは廃止した。
- **`agent-compat/distribution/` は作らなかった**: 生成設定の正本は `registry/ai-tools.yaml` で、生成器は `maintenance/scripts/plugin_meta/generate/` にある。どちらもアンブレラの持ち物なので、別の置き場を作らなかった。
- **知識スキルの書式説明はリンクに置き換えなかった**: `ai-tools-knowledge` はプラグインとしてインストールされる。プラグインの外（`agent-compat/`）へのリンクはインストール先で切れる。リンクは相違点ドキュメント → 知識スキルの一方向にした。TODO 5 は古い構成の記述の削除と、誤りの修正だけ。
- **Codex の `agents/openai.yaml`（5 件）は移さなかった**: Codex が `ai-tools-knowledge` をインストールすると、そのまま UI メタデータとして効く。サンプルは `formats/codex/skill/codex-sample-skill/agents/openai.yaml` に 1 件だけ作った。Copilot 側に混入していた 2 件は計画どおり削除した。
- **サンプルの走査除外**: 生成コピーには目印 `.agent-compat-copy` を、`agent-compat/formats/` には `.format-samples` を置く。`find_skill_md_files` は、どちらかの目印があるディレクトリを辿らない。サンプルには `AGENTS.md`・`CLAUDE.md`・`GEMINI.md` という名前を付けない（`*.example.md`）。
- **05 の取りこぼし**: 次の 3 件を直した。
  - `agent-tooling` のテスト（`test_skill_enquete.py`）の偽スキルの置き場。
  - `site/skills-site/tests/publication.test.mjs` の agent-tooling URL。
  - `vscode-copilot-docs` の切れリンク。
- **cline-plugins の旧 README・旧 Codex/Cursor マニフェスト**: README は削除した。旧 Codex/Cursor マニフェストは `formats/<tool>/plugin/` のサンプルとして残した（name は旧 `meta` のまま）。

## 検証

- `uv run pytest`（maintenance/scripts、skill-tools、agents-rules、agent-tooling、skills/plugins。doc-transcription は従来どおり別プロジェクト）: 703 passed。新規テスト `maintenance/scripts/tests/test_workspace_copies.py` 6 件。
- `just skills-site-check`（39 passed）、`precommit-check --all`、`just links-check`、`reorg.check_links`（111 件。05 完了時と同じで、増えていない）。
- `claude plugin validate` を `skills/plugins/ai-tools-knowledge` とマーケットプレイスに実行し、通過した（警告は README・LICENSE の位置のみ）。
- `just hooks-update` → `just hooks-installed` でフックを入れ直した。

## 外部への影響

- Codex・Copilot のマーケットプレイスのプラグイン名が `meta` → `ai-tools-knowledge` に変わった。入れていた利用者は入れ直す（`docs/integrations/codex.md`・`claude-code.md` に記載）。`.github/copilot/settings.json` の `enabledPlugins` も直した。
- Codex の sparse checkout 手順は `--sparse skills/plugins/ai-tools-knowledge` になった。

## 残課題（未確認・後続へ）

- 相違点ドキュメントの「未確認」項目（各ドキュメントに記載）。特に Antigravity rules の glob キー: `antigravity-memory` は `globs:`、`tools/agents-rules` は `glob:` を出力していて、食い違っている。
- `cline-skill-writer/SKILL.md:33` が、公式の置き場所一覧に無い `.agents/skills/` を先に確認させている（誤りの疑い）。
- Cursor の `.cursor-plugin/plugin.json`・Copilot のルート `plugin.json` が実際に読み込まれるかは、各ツールで未確認。
