---
type: Design Decision
title: repo-tools.yamlによるSKILL.md自作ツール依存の管理
description: Explains how repo-tools.yaml registers which tools/-rooted CLI tools a SKILL.md may declare as an install-time prerequisite (meta.requires_repo_tools / meta.requires_install), how check_skill_repo_tools.py enforces it at commit time, and how skills-site's repo-tools-registry.mjs consumes the same file to render its public tool list. Use when adding a new tools/ CLI that a skill depends on, when a lefthook "repo-tools consistency" check fails, or when deciding whether a tool needs registering here at all.
tags: [tools, repo-meta]
generated: { by: reference_agent/claude-sonnet-5, at: 2026-08-11T00:00:00Z }
status: stable
---

# repo-tools.yamlによるSKILL.md自作ツール依存の管理

## SSOT: `repo-tools.yaml`

リポジトリ直下の[`repo-tools.yaml`](../../repo-tools.yaml)が、「`SKILL.md`の`meta.requires_repo_tools`/`meta.requires_install`が参照してよい、`tools/`配下の自作CLIツール」の単一の情報源（SSOT）。各エントリは`path`（`tools/`配下のディレクトリ）と`install`（インストールコマンド）を持つ。

`ai-tools.yaml`・`meta_field.yaml`と同じ[SSOT+生成パターン](/repo-meta/repo-ssot-pattern.md)を踏襲するが、**このSSOTからは派生ファイルが生成されない**点が異なる。役割は「チェック」と「公開表示への読み込み」の2つだけ。

## 消費側1: コミット時チェック

`tools/internal/skill/check/check_skill_repo_tools.py`が、全`SKILL.md`の`requires_repo_tools`/`requires_install`に含まれる`tools/...`パスを`repo-tools.yaml`の`path`一覧と突き合わせ、未登録のパスがあれば失敗する。読み込みは共有ローダ`tools/internal/skill/util/repo_tools_registry.py`の`load_repo_tools()`経由で行い、スクリプト側にパスをハードコードしない。

以下は対象外（`check_skill_repo_tools.py`冒頭のコメント参照）:

- `repo-meta/**` — このディレクトリの`SKILL.md`は`requires_repo_tools`を「CLI依存」ではなく「このメタスキルが説明するファイル」の意味で流用しているため（[tool-companion-skills](/repo-meta/tool-companion-skills.md)参照）
- `tools/internal/**` — リポジトリ保守用の内部スクリプトで、スキル利用者がインストールする対象ではないため

`repo-tools.yaml`冒頭のコメントにある通り、**どのスキルからもまだ参照されていないツールは登録不要**（例: 執筆時点の`tools/schedule`）。

## 消費側2: skills-siteの公開表示

`skills-site/scripts/repo-tools-registry.mjs`も同じ`repo-tools.yaml`を読む。ただしこちらは検証ではなく、公開サイト上で「インストール可能なツール」をツール名とGitHubフォルダへのリンクとして表示するために使う（インストール手順そのものは載せない）。`skills-site/scripts/build-catalog.mjs`の`resolveRequiresRepoTools`が、SKILL.mdの`requires_repo_tools`値をこの一覧と突き合わせてリンク化するかプレーンテキスト表示に留めるかを決める。

## 実行方法

```bash
just --justfile tools/internal/justfile skill-repo-tools-check
```

`lefthook.yml`のpre-commitに、`**/SKILL.md`または`repo-tools.yaml`の変更をトリガーとして登録済み（`stage_fixed`は使わない — このチェックはファイルを書き換えない）。通常は手動実行不要で、コミット時に任せればよい。

## 新しい`tools/`配下ツールを追加する手順

1. `tools/<name>/`にツール本体を作成する
2. いずれかの`SKILL.md`の`meta.requires_repo_tools`（および必要なら`meta.requires_install`）でそのツールを参照する（[skill-meta-fields](/repo-meta/skill-meta-fields.md)参照）
3. `repo-tools.yaml`の`tools:`に`path`と`install`を追記する（アルファベット順を維持）

手順3を忘れると、次のコミットでlefthookの「check SKILL.md repo-tools consistency」が失敗する。

## 落とし穴

- ツールをリネーム・移動したのに`repo-tools.yaml`の`path`を更新し忘れると、参照側の`SKILL.md`が「未登録」としてチェックに失敗する（typoと区別がつかないので、エラーメッセージに従い両方を疑う）
- `repo-meta/**`配下の`SKILL.md`で`requires_repo_tools`に`justfile`や`lefthook.yml`のようなツール以外のパスを書いても、このチェックの対象外なので失敗しない（[tool-companion-skills](/repo-meta/tool-companion-skills.md)の用法の違いを参照）

## 関連

- [repo-ssot-pattern](/repo-meta/repo-ssot-pattern.md) — `repo-tools.yaml`が従うSSOT+生成パターン全体（このSSOTは「生成なし」の例外形）
- [skill-meta-fields](/repo-meta/skill-meta-fields.md) — `requires_repo_tools`/`requires_install`フィールド自体の意味
- [tool-companion-skills](/repo-meta/tool-companion-skills.md) — `repo-meta/**`が`requires_repo_tools`を別の意味で流用している理由
- [lefthook-automation](/repo-meta/lefthook-automation.md) — コミット時チェックを自動実行する仕組み全体

## このドキュメントの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、この内容を`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](/repo-meta/ai-tools-config.md)参照。
