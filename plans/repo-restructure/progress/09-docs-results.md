# 09 実行記録（README・AGENTS.md・docs・探索スキルの最終更新）

## コミット

| リポジトリ | コミット  | 内容                                                                                                                                                      |
| ---------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| アンブレラ | `467a8b4` | (1) README（「取得」にフック・agent-compat-sync、フォルダ構成をサブモジュール／アンブレラ本体に再編）、README_EN（全訳し直し）、AGENTS.md、repo-layout    |
| アンブレラ | `de44e74` | (2) `docs/index.md` を利用者向けバンドルに再定義、`docs/log.md` に再編の記録、`maintenance/docs/index.md` の説明を各 frontmatter に同期（7 件ずれていた） |
| アンブレラ | `41a5d20` | (3) repo-meta スキル（exploring-this-repo・meta・discovering-skills・changing-skills-and-tools）、`maintenance/plugin/README.md`                          |
| AI-skills  | `400fb22` | (4) 旧パスのコメント（writing-skill-web・tav-lit・cursor-docs）、otel-reference のサブモジュール越えリンク                                                |
| AI-skills  | `68d1f6c` | フック後の生成物同期（下記の不具合で CATALOG.md が prettier 整形された版になった）                                                                        |
| AI-skills  | `2cd089f` | cc-knowledge の CATALOG.md を生成器の出力に戻す                                                                                                           |
| AI-tools   | `a2dc161` | (4) issue-agent の AGENTS.md の消えたプランへのリンクを `plans/guides/plan-execution.md` へ                                                               |
| AI-site    | `1711ebc` | (4) tools-site のトップが指す `repo-tools.yaml` を `registry/repo-tools.yaml` に、生成スクリプトのコメント例                                              |
| アンブレラ | `0456694` | `maintenance/lefthook/submodule.yml` の prettier に `--ignore-path ../.prettierignore`                                                                    |
| アンブレラ | `2c48c4c` | (4) `docs/topics/claude_sandbox` の `tools/sandbox` へのリンク、skill-maintenance の docstring、3 サブモジュールのポインタ                                |

## 決めたこと

- **README の生成部分**: 境界は変えない（ai-tools 節だけ生成）。サブモジュール・アンブレラ本体の節は `ai-tools.yaml` の責務（AI ツールごとの設定）と違うので、生成元を増やさなかった。README_EN の ai-tools 節は従来どおり日本語の生成結果の手訳。
- **`docs/` の位置づけ**: 保守の規約は `maintenance/docs` に移ったので、`docs/` は利用者向け（`integrations`・`topics`）だけのバンドルとし、`maintenance/docs`・`agent-compat/docs/differences` は「関連（バンドル外）」に置いた。
- **site の `repo-tools.yaml` リンク**: 公開ページなので互換コピーではなく SSOT の `registry/repo-tools.yaml` を指す。
- **`agents-rules` の再生成はしなかった**: `.clinerules/`・`.github/instructions/`・`.agents/rules/` はこのリポジトリの履歴で一度もコミットされておらず、旧パス向けの生成物は残っていない。`--dry-run` は 48 ソース × 3 ターゲットがすべて新規。ツールの方針（必要なときだけ手動で実行）どおり、生成はしない。
  - `--list-sources` はサブモジュールの `AGENTS.md`（`skills/`・`site/` の新規分を含む）を拾い、`_umbrella/` の Junction の中は拾わない。

## 計画との差分

- サブモジュールの lefthook で prettier がアンブレラの `.prettierignore` を読まず、生成物の `CATALOG.md` を整形する不具合を見つけて直した（`0456694`）。07・08 で入った他の `CATALOG.md` は崩れていないことを `rg` で確認した。
- `agents-rules` は再生成しなかった（上記）。

## 意図して残した旧パス

- 再編の記録: `docs/log.md` の過去エントリ、`plans/`、`maintenance/scripts/reorg/tables/`・`rewrite_moved_paths.py`、利用者向けの対応表（README・`docs/integrations/{claude-code,codex}.md`）、`agent-compat/formats/*/README.md` の出自、`web-lookup`・`doc-tools` の README の「旧 `my-tools-no-install`」。
- 生成物・ビルド出力: `site/skills-site/{public,dist}/ai-index.json`（スキル本文由来、次のビルドで更新）。
- `maintenance/lefthook/submodule.yml` の `agent-tooling/...`（agent-compat サブモジュールのルートからの相対で正しい）。
- `tools/skill-tools/tests` の `meta-plugins` フィクスチャ（カタログ外のディレクトリの例）、`copilot-writing-plugins` の `security-checks@copilot-plugins`（外部のマーケットプレイス名）、`tools/mslearn/memo` の調査メモ。
- 既存のリンク切れで再編と無関係なもの: `tools/_plugin/my-tools/skills/{linear-cli,parallel-agent-worktree}` の `.claude/plans/...`（参照先のプランはこのリポジトリの履歴に無い）、`writing-skill-complex/anthropic-best-practices.md` などの例示リンク。

## 検証

- `maintenance/scripts/reorg/check_links.py` をアンブレラと各サブモジュールで実行。再編由来のリンク切れは 0（残りは上の「既存のリンク切れ」と、未生成の `.agents/rules/`・`.clinerules/` への README のリンク）。
- 各コミットの lefthook（アンブレラ・サブモジュール）が通過。全リポジトリの `git status` がクリーン。
- `codegraph sync` 完了。

## 完了記録

- 01〜09 の全ステップを完了した。09 の 5 TODO（ルートの文書、docs の索引、repo-meta スキル、旧パスの掃除と生成物の確認、完了記録）を実施。
- 計画との差分: 上の「計画との差分」の 2 点。
- 未完了の残課題（後続へ）: 06・07 の progress の「残課題」（相違点ドキュメントの未確認項目、gitlink 更新で `paths:` が発火するか、AI-tools の Tool release の再実行、アンブレラの Actions シークレットと Pages、skill-tools の blob URL、退避フォルダ `C:/C/ai-split-backup/` の削除、`registry/` 互換コピーの撤去時期）。いずれも外部操作か別作業で、本プランの範囲外。
- サブモジュール（AI-skills・AI-tools・AI-site・AI-agent-compat）とアンブレラは未 push。
