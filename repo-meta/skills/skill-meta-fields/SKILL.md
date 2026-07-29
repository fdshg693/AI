---
# AI呼び出しとファイル変更を伴うため、ユーザーが明示的に呼び出した場合だけ使う。
name: skill-meta-fields
description: Maintains the meta fields in this repository's SKILL.md frontmatter by using an aim-ask script to inspect skill directories and fill missing values. Use when a skill is added or its dependencies, hooks, installation requirements, environment requirements, or repository-tool usage changes.
disable-model-invocation: true
allowed-tools: Bash(uv run --directory tools/internal python -m skill.set.skill_meta_field_fill *) Bash(just --justfile tools/internal/justfile skill-meta-fields-fill)
meta:
  requires_repo_tools: tools/internal/skill/set/skill_meta_field_fill.py, tools/internal/justfile
  requires_env: OPENROUTER_API_KEY
  dependencies: none
  requires_install: uv, just, aim-ask
  requires_hooks: none
  requires_skills: none
  status: experimental
  description: no description
  version: 1.0.2
---

# SKILL.md metaフィールドのメンテナンス

このリポジトリの各`SKILL.md`にある`meta:`ブロックを、スキルの実態に合わせて保守する。新しいスキルの追加、他スキル・フック・外部ツール・環境変数・このリポジトリの自作ツールへの依存関係の変更を確認したときに、明示的に呼び出す。

## フィールドの参照先

フィールドの意味、値の形式、既定値、例は、リポジトリ直下の[`meta_field.yaml`](../../../meta_field.yaml)を正とする。ここでは一覧と用途だけを要約し、詳細な定義を重複させない。

| フィールド            | 用途の要約                         |
| --------------------- | ---------------------------------- |
| `version`             | スキルのバージョン                 |
| `description`         | 人間向けの管理メモ                 |
| `status`              | 完成度・成熟度                     |
| `requires_skills`     | 動作前提となる他スキル             |
| `requires_hooks`      | 紐づくフックの要否                 |
| `requires_install`    | 事前インストールが必要な外部ツール |
| `dependencies`        | スキル内スクリプトのライブラリ依存 |
| `requires_env`        | 必要な環境変数・`.env`設定         |
| `requires_repo_tools` | このリポジトリの自作ツールへの依存 |

既存値を変更するときも、まず`meta_field.yaml`を確認する。新しいフィールドや意味の変更が必要なら、SSOTを先に更新する。

## スクリプトの実行

リポジトリ全体を対象にする通常の実行は、`tools/internal/justfile`のレシピを使う。

```bash
just --justfile tools/internal/justfile skill-meta-fields-fill
```

対象を絞る、または実行前に件数だけ確認する場合は、スクリプトを直接実行する。

```bash
uv run --directory tools/internal python -m skill.set.skill_meta_field_fill --dry-run repo-meta/skills/<skill-name>
uv run --directory tools/internal python -m skill.set.skill_meta_field_fill repo-meta/skills/<skill-name>
```

スクリプトはスキルディレクトリを1回の`aim-ask`呼び出しに渡し、ディレクトリツリーと各ファイル内容をもとに新7フィールドを判定する。既存の空でない値は保持し、不足している値だけを`SKILL.md`へ補完する。実行には`aim-ask`と`OPENROUTER_API_KEY`が必要である。

## レビュー観点

実行後は必ず`git diff`を確認し、次をレビューしてから次の作業へ進む。

- 変更対象が意図したスキルだけで、説明文や本文など無関係な箇所が書き換わっていない。
- 各値が対象スキルの`SKILL.md`、README、参照スクリプト、設定を根拠としている。AIが推測した依存関係をそのまま採用しない。
- `meta_field.yaml`の形式に従い、複数値はスカラーのカンマ区切り、該当なしは`none`になっている。
- 既存の`meta:`値を不必要に上書きしていない。`meta.version`以外を変更した場合も、必要なバージョン更新を確認する。
- **AI判断は誤りうるため、レビュー無しで一括コミットしない。**

## 関連

- [skill-md-commits](../skill-md-commits/SKILL.md) — `SKILL.md`をコミットする際のpre-commitフックの挙動（生成物再生成・defaultsバックフィル・meta.versionバンプチェック）と落とし穴

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、このスキルを`ai-tools.yaml`へ登録しないこと。登録しなければマーケットプレイスおよび`skills-site`の公開対象にもならない。新しいスキルをこの配下に追加する場合も同様に扱う。
