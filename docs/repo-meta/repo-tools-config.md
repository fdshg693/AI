---
type: Design Decision
title: repo-tools.yamlによるSKILL.md自作ツール依存の管理
description: Explains how repo-tools.yaml registers which tools/-rooted CLI tools a SKILL.md may declare as an install-time prerequisite (meta.requires_repo_tools / meta.requires_install), how check_skill_repo_tools.py enforces it at commit time, how skills-site's repo-tools-registry.mjs consumes the same file to render its public tool list, and how .github/workflows/tool-release.yml reads its `release` field to determine tag+GitHub Release targets. Use when adding a new tools/ CLI that a skill depends on, when a lefthook "repo-tools consistency" check fails, when deciding whether a tool needs registering here at all, or when deciding whether a tool should be a tag+Release target.
tags: [tools, repo-meta]
generated: { by: reference_agent/claude-sonnet-5, at: 2026-08-11T00:00:00Z }
status: stable
---

# repo-tools.yamlによるSKILL.md自作ツール依存の管理

## SSOT: `repo-tools.yaml`

リポジトリ直下の[`repo-tools.yaml`](../../repo-tools.yaml)が、「`SKILL.md`の`meta.requires_repo_tools`/`meta.requires_install`が参照してよい、`tools/`配下の自作CLIツール」の単一の情報源（SSOT）。各エントリは`path`（`tools/`配下のディレクトリ）と`install`（インストールコマンド）を持つ。

`ai-tools.yaml`・`meta_field.yaml`と同じ[SSOT+生成パターン](/repo-meta/repo-ssot-pattern.md)を踏襲するが、**このSSOTからは派生ファイルが生成されない**点が異なる。役割は「チェック」「公開表示への読み込み」「タグ+Release対象の判定」の3つ。

## 消費側1: コミット時チェック

`tools/internal/skill/check/check_skill_repo_tools.py`が、全`SKILL.md`の`requires_repo_tools`/`requires_install`に含まれる`tools/...`パスを`repo-tools.yaml`の`path`一覧と突き合わせ、未登録のパスがあれば失敗する。読み込みは共有ローダ`tools/internal/skill/util/repo_tools_registry.py`の`load_repo_tools()`経由で行い、スクリプト側にパスをハードコードしない。

以下は対象外（`check_skill_repo_tools.py`冒頭のコメント参照）:

- `repo-meta/**` — このディレクトリの`SKILL.md`は`requires_repo_tools`を「CLI依存」ではなく「このメタスキルが説明するファイル」の意味で流用しているため（[tool-companion-skills](/repo-meta/tool-companion-skills.md)参照）
- `tools/internal/**` — リポジトリ保守用の内部スクリプトで、スキル利用者がインストールする対象ではないため

`repo-tools.yaml`冒頭のコメントにある通り、**どのスキルからもまだ参照されていないツールは登録不要**（例: 執筆時点の`tools/schedule`）。

## 消費側2: skills-siteの公開表示

`skills-site/scripts/repo-tools-registry.mjs`も同じ`repo-tools.yaml`を読む。ただしこちらは検証ではなく、公開サイト上で「インストール可能なツール」をツール名とGitHubフォルダへのリンクとして表示するために使う（インストール手順そのものは載せない）。`skills-site/scripts/build-catalog.mjs`の`resolveRequiresRepoTools`が、SKILL.mdの`requires_repo_tools`値をこの一覧と突き合わせてリンク化するかプレーンテキスト表示に留めるかを決める。

## 消費側3: タグ+Releaseの対象判定

`.github/workflows/tool-release.yml`の`discover`ジョブも同じ`repo-tools.yaml`を読む。各エントリの`release: true`フィールドを見て、値が`true`のエントリの`path`一覧をタグ+GitHub Releaseの対象（`release`ジョブの`strategy.matrix.dir`）として動的に決定する。読み込みは`util/`の共有ローダを使わず、workflow内で完結する独立したPythonスニペット（`uv run --with pyyaml python -c "..."`）で行う——`tools/internal/skill/AGENTS.md`が`util/`モジュールの新規消費者を`set/`・`check/`以外に増やすことを禁じているため。

執筆時点の対象は`aim`/`tav`/`mslearn`/`ctx7`の4エントリ（`tools/aim`・`tools/tav-cli`・`tools/mslearn`・`tools/ctx7`）。`aim-ask`/`aim-summarize`/`my-agents`はworkspace内兄弟パッケージへの依存でdependency confusionを起こすため`release`未設定（対象外）——詳細は[tools/install/AGENTS.md](../../tools/install/AGENTS.md)参照。

この`release`フラグは消費側1（チェック対象可否）・消費側2（skills-site公開可否）とは無関係な独立した軸。あるツールがチェック対象・公開対象であっても、タグ+Releaseの対象とは限らない。

## 消費側4: lefthookによるバージョン自動アップ

`lefthook.yml`のpre-commitジョブ「bump release tool pyproject.toml version」（`tools/internal/release/bump_release_versions.py`）も同じ`repo-tools.yaml`を読み、`release: true`の各`path`について、ステージ済みファイルがそのフォルダ配下に1つでもあれば`uv version --bump patch --frozen`でpyproject.tomlのpatchバージョンを1つ上げる。判定はフォルダ単位（そのフォルダ配下の変更ファイル数やdiffの中身は見ない）で、ドキュメントのみの変更でもバージョンが上がる。`--frozen`によりuv.lockの再ロックは行わない。

再ステージは`lefthook.yml`の`stage_fixed`に任せず、スクリプト自身が`git add`でpyproject.tomlを明示的にステージする。`stage_fixed`はジョブ自身の`glob`にマッチし、かつ元々ステージ済みだったファイルしか再ステージしない（例: `tools/aim/README.md`だけをステージしたコミットでは、`tools/aim/pyproject.toml`はそのどちらにも該当せず、`stage_fixed`では拾われない——実機検証済み）。消費側3と同じくworkflow内蔵スニペット方式を踏襲し、`skill/util/repo_tools_registry.py`は使わない（`tools/internal/skill/AGENTS.md`参照）。

これにより、対象4ツールはコミットのたびに（そのフォルダに変更があれば）patchバージョンが上がり、mainへのpush時に消費側3（`tool-release.yml`）が新しいタグ+Releaseを発行する。

## 実行方法

```bash
just --justfile tools/internal/justfile skill-repo-tools-check
```

`lefthook.yml`のpre-commitに、`**/SKILL.md`または`repo-tools.yaml`の変更をトリガーとして登録済み（`stage_fixed`は使わない — このチェックはファイルを書き換えない）。通常は手動実行不要で、コミット時に任せればよい。

## 新しい`tools/`配下ツールを追加する手順

1. `tools/<name>/`にツール本体を作成する
2. いずれかの`SKILL.md`の`meta.requires_repo_tools`（および必要なら`meta.requires_install`）でそのツールを参照する（[skill-meta-fields](/repo-meta/skill-meta-fields.md)参照）
3. `repo-tools.yaml`の`tools:`に`path`と`install`を追記する（アルファベット順を維持）
4. そのツールをタグ+GitHub Releaseの対象にもしたい場合は、同じエントリに`release: true`を追記する（workspace内の兄弟パッケージに依存しないツールのみ——理由は[tools/install/AGENTS.md](../../tools/install/AGENTS.md)参照）

手順3を忘れると、次のコミットでlefthookの「check SKILL.md repo-tools consistency」が失敗する。手順4は任意（省略時は`.github/workflows/tool-release.yml`のタグ+Release対象にならないだけで、他の消費側には影響しない）。

## 落とし穴

- ツールをリネーム・移動したのに`repo-tools.yaml`の`path`を更新し忘れると、参照側の`SKILL.md`が「未登録」としてチェックに失敗する（typoと区別がつかないので、エラーメッセージに従い両方を疑う）
- `repo-meta/**`配下の`SKILL.md`で`requires_repo_tools`に`justfile`や`lefthook.yml`のようなツール以外のパスを書いても、このチェックの対象外なので失敗しない（[tool-companion-skills](/repo-meta/tool-companion-skills.md)の用法の違いを参照）

## 関連

- [repo-ssot-pattern](/repo-meta/repo-ssot-pattern.md) — `repo-tools.yaml`が従うSSOT+生成パターン全体（このSSOTは「生成なし」の例外形）
- [skill-meta-fields](/repo-meta/skill-meta-fields.md) — `requires_repo_tools`/`requires_install`フィールド自体の意味
- [tool-companion-skills](/repo-meta/tool-companion-skills.md) — `repo-meta/**`が`requires_repo_tools`を別の意味で流用している理由
- [lefthook-automation](/repo-meta/lefthook-automation.md) — コミット時チェックを自動実行する仕組み全体
- [tools/install/AGENTS.md](../../tools/install/AGENTS.md) — タグ+Releaseの対象パッケージ表とピン留めインストール手順、workspace内兄弟パッケージ依存による除外理由

## このドキュメントの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、この内容を`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](/repo-meta/ai-tools-config.md)参照。
