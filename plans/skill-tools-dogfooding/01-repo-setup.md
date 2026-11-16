---
type: Plan Step
status: done
---

# Step 1: アンブレラにプロジェクト用 skill-tools.yaml の受け皿を作る

> [00-overview.md](00-overview.md) の続き。

## やること

アンブレラ直下に、このリポジトリで入れるスキルを書くためのプロジェクト設定 `skill-tools.yaml` の example をコミットし、実体と配置先を gitignore する。clone 後のセットアップ手順に 1 行足す。

## 読むべきファイル・実行推奨Grep

**既存の同種の仕組みに合わせるため（優先度: 高）**

- 読む: `.claude/skill-tools.hooks.example.yaml` と `.gitignore` の 44〜52 行付近 — フック側で同じ「example をコミット・実体は gitignore」をどう書いているか。プロジェクトの `skill-tools.yaml` との関係（フック設定は別ファイルを読ませているのか）を確認する
- 読む: `tools/skill-tools/skill-tools.yaml.example` — プロジェクト用 example の雛形
- 読む: `registry/local-configs.yaml` — `local_configs` の書式と `deny_patterns`

**規約を確認するため（優先度: 中）**

- 読む: `maintenance/docs/repo-layout.md` の「ローカル設定ファイル」節
- 実行: `skill-tools config show` — 現状は `config.project: C:\C\ai\skill-tools.yaml (missing)`。グローバル設定（`%APPDATA%/skill-tools/skill-tools.yaml`）に source・targets が既にあることを確認済み

## 触るファイル

- 新規: `skill-tools.example.yaml` — プロジェクト固有の上書きだけを書く example。入れるスキルの一覧はこの時点では書けない（宣言的な一覧を持つ機能が無い。下記）ので、コメントで「install-skills で入れたものは `.skill-tools/manifest.json` に記録される」と案内する程度にとどめる
- 変更: `.gitignore` — `/skill-tools.yaml` と `/.claude/skills/` を追加
- 変更: `registry/local-configs.yaml` — `skill-tools.yaml` ↔ `skill-tools.example.yaml` を宣言
- 変更: `README.md` の「取得」節 — `cp skill-tools.example.yaml skill-tools.yaml` と `skill-tools install-skills ...` の手順（Step2 で入れるスキルが決まってから書く）

## 決定事項・注意点／落とし穴

- **フック設定との関係**: フックは `.claude/skill-tools.hooks.yaml` を使っている。プロジェクトの `skill-tools.yaml` を新設すると `hooks` 設定もマージ対象になり得るので、`just hooks-install` の挙動が変わらないことを `skill-tools hooks sync --dry-run` で確かめる。
- **example の名前**: `skill-tools.example.yaml` は `X.example.Y` 形式で `deny_patterns` に当たらない。example を CLI がそのまま読まないこと（`config show` で `config.project` が missing のまま）を確認する。
- **`.claude/skills/` の gitignore と他ツール**: `just agent-compat-sync` やカタログ生成が `.claude/skills/` を走査していないか `rg "\.claude/skills"` で確認する。走査していたら、入れたスキルがカタログに二重に載る。
- 宣言的なスキル一覧（フックの `hooks.install` に相当するもの）は今は無い。必要かどうかは Step2 で判断し、作るなら Step3。この Step では example に一覧を書かない。

## ルール更新ポイント

- `registry/local-configs.yaml` への宣言で足りるので、`AGENTS.md` には書かない。

## 進め方

- **実行主体**: メインエージェント（数ファイルの小さな変更）。
- **TODO化**: ステップ全体を 1 項目・1 コミット（アンブレラのみ。サブモジュールは触らない）。

## 実施結果

- example は `source: {type: local, path: .}` と `targets.claude` だけ。`hooks:` は書かない（フックは `just hooks-install` が `--config .claude/skill-tools.hooks.yaml` で別に読む）。
- 確認: example だけでは `config.project` は missing のまま。コピー後は found になり、`source.path`・`index.path` はグローバル設定と同じ値。`hooks sync --dry-run` の出力はコピー前後で同じ（`(no changes)`）。
- `.claude/skills/` を走査する生成スクリプト・カタログは無い（`rg "\.claude/skills"` は `.links.yaml` とテストだけ）。
- README「取得」節への追記は、入れるスキルが決まる Step2 の後に回した。
