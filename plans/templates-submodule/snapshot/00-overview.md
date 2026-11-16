---
type: Plan
status: ready
---

## 実装ステータス

- [ ] [01-create-repo-and-add.md](01-create-repo-and-add.md) — `temp/templates` を git 化して `fdshg693/AI-templates` を作り、`templates/` としてサブモジュール追加
- [ ] [02-scaffold-submodule.md](02-scaffold-submodule.md) — サブモジュールの定型ファイル（lefthook・`.links.yaml`・指示ファイル・gitignore 等）を揃える
- [ ] [03-register-in-umbrella.md](03-register-in-umbrella.md) — アンブレラの規約・README・スキルにサブモジュールとして登録し、検証する

# `temp/templates` を新サブモジュール `templates/` として取り込む - 概要

## 要件

- `temp/templates`（AI エージェントと使う運用テンプレート集。`core/`・`starter/`・`.claude/skills/template-*`）を、新しいリポジトリ `fdshg693/AI-templates` にし、アンブレラ直下の `templates/` にサブモジュールとして取り込む。
- 既存の 6 サブモジュール（直近の前例は `infra/`: c3cb74a・579bb43）と同じ形にそろえる。単体で開ける（Junction・フック・lefthook）、2 段階コミット、`just sub-*`／`branch-*` の対象になる。
- 取り込み後、`temp/templates` は削除する（`temp/` は gitignore 済み）。

## 実装ステップ

1. [01-create-repo-and-add.md](01-create-repo-and-add.md) — 初回コミット・GitHub リポジトリ作成・`git submodule add`
2. [02-scaffold-submodule.md](02-scaffold-submodule.md) — サブモジュール側の定型ファイル
3. [03-register-in-umbrella.md](03-register-in-umbrella.md) — アンブレラ側の文書・スキル・コメントへの登録と検証

## 主要な決定事項

| 決定 | 理由 |
| ---- | ---- |
| リポジトリ名 `fdshg693/AI-templates`、PUBLIC、パス `templates/`（ユーザー確認済み） | 既存サブモジュールの命名（`AI-<path>`・すべて PUBLIC）に合わせる |
| 履歴は新規の初回コミットから始める | `temp/templates` は git 管理外（`.git` 無し、アンブレラでも `temp/` が gitignore）で、引き継ぐ履歴が無い |
| templates 自身の `plans/` は廃止し、他のサブモジュールと同じくアンブレラの `plans/` への Junction にする（ユーザー確認済み） | [repo-layout「plans/ は全サブモジュールで共有」](../../maintenance/docs/repo-layout.md#サブモジュールを単体で開く)。中身は `core/plans` を導入したコピーと、完了済み（`implementing-done`）のプラン `threads-template/` だけ |
| 完了済みプラン `plans/threads-template/` は初回コミットに含め、Step 2 で削除する | 完了プランは削除する運用だが、他に履歴が無いので一度コミットして git 履歴に残す |
| `core/threads/planning`（`core/plans` への Junction）は `templates/.links.yaml` で宣言する | AGENTS.md の規約「Junction は `.links.yaml` で宣言し `just links-sync` で作る」。単体 clone では従来どおり `link_plans.py` |
| `.claude/skills/template-create`・`template-review` はサブモジュールの中に置いたままにする | このリポジトリの作業にしか使わないスキルで、配布対象（`ai-tools.yaml`・marketplace）にしない |
| Python は標準ライブラリのみのスクリプトなので uv workspace のメンバーにしない | サブモジュール直下に `pyproject.toml` を置かない規約。`uv run <script>` でそのまま動く |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `templates/`（サブモジュール。中の `lefthook.yml`・`.links.yaml`・`AGENTS.md`・`README.md`・`LICENSE`・`.gitattributes`・`.claude/skill-tools.hooks.example.yaml`）

### 変更

- `.gitmodules`
- `README.md`・`README_EN.md`・`AGENTS.md`・`CONTRIBUTING.md`
- `justfile`・`maintenance/lefthook/submodule.yml`（コメントのサブモジュール一覧）
- `maintenance/docs/repo-layout.md`・`maintenance/docs/index.md`・`maintenance/docs/gh-actions-lifecycle.md`
- `maintenance/plugin/skills/committing/SKILL.md`・`exploring-this-repo/SKILL.md`・`discovering-skills/SKILL.md`（該当箇所があるもの）

## ルール更新ポイント

- `AGENTS.md`（Step 3）: サブモジュール一覧に `templates/` を足す。
- `maintenance/docs/repo-layout.md`（Step 3）: サブモジュール表・数・description、「置き場所の判定基準」に「運用テンプレート → `templates/core/<name>/`」の行を足す。
- `templates/AGENTS.md`（Step 2）: 単体で開いたときの注意（`plans/` はアンブレラ側、`core/threads/planning` は `just links-sync` で作る）。

## 進め方

- **TODO化**: ステップ一覧の各項目を 1 TODO にする。外向きの操作（GitHub リポジトリ作成・push）は Step 1 の中でユーザーに確認してから行う。
- 上の確認事項 2 点はユーザー確認済み（2026-11-16）。`ready` にして `snapshot_plan.py` で凍結した。

## 後続（このプランの範囲外）

- アンブレラの `plans/` は `templates/core/plans` の導入コピーで、`README.md` に 1 行差分がある（threads との境界の記述が無い）。取り込み後に、アンブレラの `plans/` を `core/plans` から同期する手順を決めるかは別途。
