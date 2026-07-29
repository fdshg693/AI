---
# 既存SSOT: ai-tools.yaml（ai-tools-configスキル）, meta_field.yaml（skill-meta-fieldsスキル）
name: repo-ssot-pattern
description: Explains this repository's habit of designating one explicitly-edited file as the single source of truth for a cross-cutting concern (which AI-tool plugins exist, what a SKILL.md meta field means) and regenerating every derived file from it via a script, rather than letting the same fact live in multiple hand-maintained places. Use when introducing a new fact that needs to stay consistent across several files, wondering which file is authoritative when two disagree, or deciding whether to hand-edit a file marked "DO NOT EDIT MANUALLY".
meta:
  requires_repo_tools: ai-tools.yaml, meta_field.yaml, tools/internal/plugin_meta/util/ai_tools_config.py
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: lefthook
  requires_skills: ai-tools-config, skill-meta-fields, lefthook-automation
  status: stable
  description: no description
  version: 1.0.0
---

# SSOT+生成によるドリフト防止パターン

このリポジトリは、複数ファイルにまたがって一致していてほしい事実（どのAIツールがどのプラグインを持つか、`SKILL.md`の`meta:`各フィールドの意味）を、**1つの手編集ファイルをSSOTとし、そこから派生ファイルをスクリプトで再生成する**という形で扱う。同じ事実を複数箇所に手で書き写さない。

## 現在の2つのSSOT

| SSOT                                          | 扱う事実                                                                                         | 詳細スキル                                         |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------- |
| [`ai-tools.yaml`](../../../ai-tools.yaml)     | どのツールがどのプラグインを持つか、各ツールのマーケットプレイス/スキルカタログ/README節の生成元 | [ai-tools-config](../ai-tools-config/SKILL.md)     |
| [`meta_field.yaml`](../../../meta_field.yaml) | `SKILL.md`frontmatterの`meta:`各サブフィールドの意味・書式・デフォルト値                         | [skill-meta-fields](../skill-meta-fields/SKILL.md) |

## 共通の形

1. **1つの手編集ファイル**をレビュー対象のdiffに残す。`rglob`等の自動検出ではなく明示列挙にするのは、追加・削除のドリフトをdiff上で見えるようにするため
2. **1本以上の`generate_*.py`**が、共有のロード経路（`ai_tools_config.py`の`load_tool`/`load_config`、`meta_field.yaml`を読むコード）だけを通してSSOTを読む。パスやメタ情報をスクリプト側にハードコードしない
3. 派生ファイルには`DO NOT EDIT MANUALLY`の注記を入れ、**マージではなく丸ごと再生成**する
4. 再生成は`lefthook.yml`のpre-commitに組み込み、コミットを跨いで派生ファイルが古くなることを防ぐ（[lefthook-automation](../lefthook-automation/SKILL.md)参照）

## 気づいたときにやること

- `DO NOT EDIT MANUALLY`と書かれたファイルを手で直そうとしている、または同じ事実（プラグイン名、フィールドの意味）を2箇所以上に手で書き足そうとしている、と気づいたら手を止める。その事実のSSOTを探し、そちらを直してから再生成する
- 2つのファイルの内容が食い違っている場合、SSOT側を正とする

## 新しい横断的な事実を導入するとき

新たに「複数の生成ファイルにまたがって一貫していてほしい事実」が出てきたら、新しい仕組みを考えるのではなく、この形を踏襲する。1つの手編集ソースファイル＋1本の生成スクリプト＋対応するlefthookジョブ、という組み合わせにする。

## 関連

- [ai-tools-config](../ai-tools-config/SKILL.md) — `ai-tools.yaml`というSSOTの詳細
- [skill-meta-fields](../skill-meta-fields/SKILL.md) — `meta_field.yaml`というSSOTの詳細
- [lefthook-automation](../lefthook-automation/SKILL.md) — 再生成をコミット時に強制する仕組み
- [skill-improving-meta-skills](../skill-improving-meta-skills/SKILL.md) — 同じ「ドリフト防止」の発想をスキルの品質側に適用したもの

## このスキルの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、このスキルを`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](../ai-tools-config/SKILL.md)参照。
