---
type: Design Decision
title: skill-toolsが前提とするリポジトリ規約
description: "Explains that tools/skill-tools is the CLI that makes this whole repository searchable and loadable as a skill/tool catalog (list-skills, install-skills/installed-skills/update-skills/remove-skills, build-index/search, list-docs/integrations-tools, workflow list/show), and which repo files and item conventions it reads as its input contract — ai-tools.yaml plugin roots and skills_layout, SKILL.md frontmatter name/description/meta.status, site/skills-site/site-overrides.yaml exclusions, repo-tools.yaml install commands and description locators, repo-workflows.yaml, repo-hooks.yaml and the agent-tooling hook catalog.json, and the bundle copy policy in tools/skill-tools/.gitignore and .skill-tools. Use when adding/moving a plugin, skill, tools/ CLI, workflow, or hook and wanting it to show up in skill-tools, when skill-tools list-skills/search/install-skills fails with a catalog error, or when changing any of those files' shape."
tags: [tools, skills, repo-wide]
generated: { by: reference_agent/claude-opus-5-5, at: 2026-09-27T00:00:00Z }
status: stable
---

# skill-toolsが前提とするリポジトリ規約

## 何のためのツールか

`tools/skill-tools`（CLI名 `skill-tools`）は、このリポジトリ全体を1つのカタログとして扱い、**別のプロジェクトや別の環境から、ここにあるスキル・ツールを探して取り込む**ためのCLIである。

| 目的             | コマンド                                                                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| スキルを一覧する | `skill-tools list-skills`                                                                                                                              |
| スキルを検索する | `skill-tools build-index` → `skill-tools search --query`                                                                                               |
| スキルを配置する | `skill-tools install-skills` / `installed-skills` / `update-skills` / `remove-skills`（`install-skills self` で skill-tools 自身のコンパニオンスキル） |
| CLIツールを扱う  | `skill-tools list-tools` / `install-tools`                                                                                                             |
| 目的別の組合せ   | `skill-tools workflow list` / `workflow show <id>`                                                                                                     |
| フックを扱う     | `skill-tools hooks list` / `install` / `installed` / `update` / `remove`                                                                               |

取得元（source）はローカルclone（`source.type: local`）か GitHub（`source.type: github`、既定は `fdshg693/ai@main`）で、どちらでも同じ規約でリポジトリを読む。CLIの使い方・設定・終了コードの詳細は [tools/skill-tools/README.md](../../tools/skill-tools/README.md) と、コンパニオンスキル `tools/_plugin/my-tools/skills/skill-tools-cli` が正本である。このドキュメントは「**skill-tools が読めるように、リポジトリ側が何をどう置いているか**」だけを扱う。

## 前提: 探索範囲は登録済みのものだけ

skill-tools はディレクトリを総なめして `SKILL.md` を拾うのではない。**SSOTファイルに登録された場所だけ**を読む。したがって「作ったのに `skill-tools list-skills` に出ない」は、ほぼ必ず登録漏れか規約違反である。

- `maintenance/plugin/` のようにSSOTへ意図的に載せていない領域は対象外（[ai-tools-config](./ai-tools-config.md)参照）。
- source・index・配置先をCWDやコード位置から推測しない。どのリポジトリを読むかは設定ファイルで明示する。
- 配置先のルートと、プロジェクトの `skill-tools.yaml` を探す場所は「スコープ」で決まる。既定のスコープは CWD のプロジェクトで、`--project-dir <path>` を付けると指定したディレクトリになる（manifest もそのルートの `.skill-tools/` に置く）。`--project-dir` を付けたときは CWD の `skill-tools.yaml` を読まない。`--config` / `SKILL_TOOLS_CONFIG` を使うとスコープ側の yaml も読まない（単一ファイルの契約のまま）。
- `--global` はユーザー全体のスコープで、ルートはホーム、配置先はホーム相対の `global_destination`（target ごとに上書き可、既定 `.claude/skills`）。プロジェクトの `skill-tools.yaml` は読まない（どこから実行しても同じ結果）。manifest・journal は `~/.skill-tools/` ではなく `SKILL_TOOLS_HOME/global`（無ければ Windows は `%LOCALAPPDATA%\skill-tools\global`、それ以外は `$XDG_STATE_HOME/skill-tools/global`）に置く。キャッシュ領域には置かない。
- ホーム、またはその祖先をプロジェクトのルートにした `install-skills` / `update-skills` は終了コード `2` で止め、`--global` を案内する（同じファイルを2つの manifest が管理するのを防ぐ）。`installed-skills` / `remove-skills` は移行のため止めない。

## 入力契約（リポジトリ側が守るもの）

**canonical ID の変更（2026-11 の再編）**: canonical ID はリポジトリ相対パスなので、`claude-plugins/` → `skills/plugins/`・`tools/_plugin/` の移動で全スキルの ID が変わった。他プロジェクトの `.skill-tools/manifest.json` は旧 ID を記録しているため、`update-skills` は「カタログから消えたスキル」として警告し、配置を残したまま更新しない。移行は `remove-skills <旧 ID>` のあと新 ID で `install-skills` し直す。`skill-tools --fb` の保存先はスキル名単位なので、名前を変えたスキル（`copilot-writing-plugins`・`copilot-writing-skills`）以外は影響しない。

SSOT yaml は `registry/` に置く。skill-tools は `registry/<name>` を先に探し、無ければ source ルートの `<name>` を読む（`skill_tools/registry.py`）。yaml 内のパスはどちらに置いてもリポジトリルート相対。`registry/` を知らない旧版 skill-tools のために、`ai-tools.yaml`・`repo-tools.yaml`・`repo-workflows.yaml`・`repo-hooks.yaml` はルートにも生成コピーを置く（`maintenance/scripts/plugin_meta/generate/generate_registry_compat.py`。pre-commit が再生成する）。旧版の利用者がいなくなったら生成器ごと消す。

### 1. `ai-tools.yaml` — スキルの探索ルート

`tools.<tool>.plugins[]` の各エントリがスキルの探索ルートになる（実装: `skill_tools/catalog/`）。

- `path` はリポジトリ相対の安全なパス。
- `skills_layout` は必須で、`subdir`（`<path>/skills/*/SKILL.md`）か `direct`（`<path>/*/SKILL.md`）。
- 同じルートを複数エントリで登録するとエラー。1つの `SKILL.md` が複数ルートに属してもエラー。
- ルート配下の `SKILL.md` がすべてカタログに入る。canonical ID はリポジトリ相対の `SKILL.md` パス（例: `skills/plugins/coding/skills/testing/SKILL.md`）。

新しいプラグインやスキルルートを足すときは、[ai-tools-config](./ai-tools-config.md) の手順どおり先に `ai-tools.yaml` を更新すれば skill-tools にも自動で載る。

### 2. `SKILL.md` frontmatter — カタログ・検索のメタデータ

カタログ化の時点で次を検証し、違反があれば `list-skills` / `install-skills` / `build-index` 全体が終了コード `2` で止まる。1スキルの不備がリポジトリ全体の利用を止める点に注意する。

- frontmatter が YAML mapping として存在すること
- `name`・`description` が空でない文字列であること
- `meta` があるなら mapping であること（`meta.status` は表示・検索結果の `status` に使う）

検索用インデックスの埋め込み入力は `name` と `description` だけで、本文はローカルのlexical検索（BM25）にのみ使う。つまり **`description` の書き方がそのまま意味検索の当たりやすさになる**。書き方は `skills/plugins/cc-knowledge/skills/writing-skill/bestpractices.md`、`meta:` フィールドは [skill-meta-fields](./skill-meta-fields.md) に従う。

### 3. `site/skills-site/site-overrides.yaml` — 公開除外

skills-site と同じ除外設定を skill-tools も尊重する。`exclude.sources`（ソースID単位）と `exclude.skills`（canonical ID単位）に挙げたものはカタログから外れる。ファイルが無ければ何も除外しない。`ai-tools.yaml` に残したまま外部から見せたくないスキルはここに書く。

### 4. `repo-tools.yaml` — CLIツールの一覧とインストール

`list-tools` / `install-tools` は `repo-tools.yaml` の全エントリを対象にする（`release` の値は見ない）。

- `path` は実在するツールフォルダであること。
- `install` はリポジトリルートで実行されるコマンド文字列（`uv tool install --editable tools/...` 等）。リポジトリ相対パスを使うため、`install-tools` は local source でのみ動く。
- `description` は概要の取得元 locator（例: `tools/aim/pyproject.toml#project.description`）。壊れていると `list-tools` がエラーで止まる。

登録ルールと整合チェックは [repo-tools-config](./repo-tools-config.md)、概要・版数のSSOTは [tool-conventions](./tool-conventions.md) を参照。

### 5. `repo-workflows.yaml` — 目的別の組合せ

「この目的ならどのスキル・ツールをどの順で使うか」を読み取り専用で記述するカタログ。`workflow list` / `show` が読み、ステップの `skill`（canonical ID）と `repo-tools.yaml` のキーを解決して、`meta.requires_skills` などの前提も合わせて表示する。何もインストール・実行しない。local source のみ対応。

参照先のスキルを移動・リネームしたら、このファイルの canonical ID も直す。

### 6. `repo-hooks.yaml` と `catalog.json` — エージェントフック

`hooks` サブコマンドは`registry/repo-hooks.yaml`（`version: 1` と `catalog`）が指すフックカタログを読む。カタログは `agent-compat/agent-tooling/agent_tooling/hooks/generated/catalog.json` で、agent-tooling のビルドが各 `scenarios/<id>/hook.yaml` と生成ファイル一覧から作る（手編集しない）。流れと設計判断は [hook-distribution](./hook-distribution.md)。

- `repo-hooks.yaml` の `catalog` はこのファイル相対、カタログ内のパスはカタログのディレクトリ相対。カタログが参照するファイルはすべてコミット済みの生成物であること（GitHub source はツリー上のファイルしか取れない）。
- `repo-hooks.yaml` が無い source は「フック0件」でエラーにしない。形式違反・参照切れは終了コード `2`。
- `hook.yaml` の `distributable: false` は外部配布しない（`hooks list --all` でだけ見える）。`requires_tools` は `repo-tools.yaml` のキー。
- カタログの形（`schemaVersion`）を変えたら、`tools/skill-tools/skill_tools/hooks/catalog.py` とテストも同時に直す。

フックの記録は manifest schema v2 の `hooks` 配列に入る（スキルは `entries`）。v1 manifest はそのまま読めて次の書き込みで v2 になる。v2 manifest を知らない古い skill-tools は「unsupported」として変更を拒否するので、利用者側で skill-tools を更新してもらう。

### 7. バンドルコピーの除外/包含ポリシー

`install-skills` はスキルフォルダを丸ごとコピーするため、何を同梱するかをリポジトリ側で決めている。

1. 組み込み既定除外（`.venv/`・`node_modules/`・`__pycache__/`・`.env` など）
2. `tools/skill-tools/.gitignore` による除外
3. `tools/skill-tools/.skill-tools` の `include:` による復帰（出荷時は `uv.lock` のみ）

スキルに同梱物を足すときは、「git管理されているか」「このポリシーで落ちないか」を確認する。`uv run --project` で同梱CLIを動かすスキルが `uv.lock` をコミットしているのはこのためである。

## 変更時のチェック

| 変更内容                                 | 確認すること                                                                                     |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------ |
| プラグイン・スキルルートの追加/移動      | `ai-tools.yaml` の `path` / `skills_layout`、`skill-tools list-skills`                           |
| スキルの追加/移動/リネーム               | frontmatter の `name`/`description`、`repo-workflows.yaml` の参照                                |
| スキルを外部に見せたくない               | `site/skills-site/site-overrides.yaml`                                                           |
| `tools/` にCLIを追加                     | `repo-tools.yaml` の `path`/`install`/`description`、`list-tools`                                |
| スキルに同梱ファイル（lockfile等）を足す | `tools/skill-tools/.gitignore` と `.skill-tools` の `include:`                                   |
| フックの追加/変更                        | `hook.yaml` と `build.py` の `ENTRIES`、`generate` 後の `catalog.json`、`skill-tools hooks list` |
| これらのファイルの**形**を変える         | `tools/skill-tools/skill_tools/` の読み取り実装とテストも同時に直す                              |

ローカルで確かめるには、source を local にした設定で次を流す。

```powershell
skill-tools list-skills --source local --repo C:\C\ai
skill-tools list-tools --source local --repo C:\C\ai
skill-tools workflow list --source local --repo C:\C\ai
skill-tools hooks list --source local --repo C:\C\ai --all
uv run pytest tools/skill-tools/tests
```

GitHub source の利用者は main に push された内容を読むため、規約違反を push すると外部の `skill-tools` 利用が止まる。

## 関連

- [ai-tools-config](./ai-tools-config.md) — `ai-tools.yaml` と生成物
- [repo-tools-config](./repo-tools-config.md) — `repo-tools.yaml` の登録と検査
- [tool-conventions](./tool-conventions.md) — ツールの版数・概要・`--version`規約
- [skill-meta-fields](./skill-meta-fields.md) — `SKILL.md` の `meta:` フィールド
- [skill-tool-relations](./skill-tool-relations.md) — スキル↔ツールの依存グラフ
- [repo-ssot-pattern](./repo-ssot-pattern.md) — SSOT+再生成の方針
- [hook-distribution](./hook-distribution.md) — フックの正本・生成・配布と自己インストール
- `docs/integrations/cli-tools.md` — 利用者側から見た skill-tools の導入手順
