---
type: Plan Step
status: planning-breakdown
---

# Step2: 変化しやすさの宣言とドッグフーディング台帳の器を作る

## やること

git から計算できない 2 つの入力の置き場所と書式を決めて作る。

- **変化しやすさの規則**: プラグイン・パスの前方一致で既定値を決め、個別スキルの上書きを持てる yaml。
- **ドッグフーディング台帳**: スキルごとに「最後にドッグフーディングした日・判定・fb ファイル名・改善コミット」を持つ yaml。中身は Step4 の周回で書き足すので、ここでは空（または書式の例だけ）で作る。

## 読むべきファイル

- 置き場所の判定（最優先）
  - `maintenance/docs/repo-layout.md` の「置き場所の判定基準」— 規則 yaml を SSOT（`registry/`）とみなすか、リポジトリ都合（`maintenance/`）とみなすか
  - `maintenance/docs/repo-ssot-pattern.md` — `registry/` に置く yaml が満たすべき条件
  - `registry/skill-tags.yaml`・`registry/meta_field.yaml` — 既存のスキル向け registry yaml の書き方
- 書式を合わせる
  - `skill/util/meta_field_registry.py`・`skill/util/skill_meta_tag.py` — registry yaml の読み方の前例
  - `registry/local-configs.yaml` — 台帳がローカル設定と誤認されないことの確認
  - `lefthook.yml` の `precommit-fix` の glob — 置き場所によってコミットのたびに再生成が走らないか
  - `maintenance/README.md` — `maintenance/` のサブフォルダ一覧（`state/` を作る場合）

## 触るファイル

- 新規: 変化しやすさの規則（候補 `registry/skill-volatility.yaml`）— プラグイン・パス単位の既定値と個別の上書き
- 新規: ドッグフーディング台帳（候補 `maintenance/state/skill-dogfood.yaml`）— canonical ID（`.../SKILL.md`）をキーにした記録。項目は日付・判定・fb ファイル名か `note`・改善コミット（リポジトリ名 + ハッシュ）
- 変更: `AGENTS.md`・`README.md`・`README_EN.md`（`registry/` に置いた場合だけ SSOT 一覧に追加）
- 変更: `maintenance/README.md`（`maintenance/state/` を作った場合、サブフォルダの一覧に追加）

## 決定事項・注意点／落とし穴

- キーは skill-tools の canonical ID（リポジトリ相対の `.../SKILL.md` パス。例: `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`）にそろえる。同名スキルがプラグイン違いで存在しうるため（`skill-tools --fb` も曖昧な名前を拒否している）。
- 台帳はアンブレラに置く。サブモジュールに置くと、ドッグフーディングのたびに 2 段階コミットが要る。`skills/` 配下や `registry/` に置くと、`lefthook.yml` の `precommit-fix`（glob に `**/skills/**`・`registry/*.yaml`）がコミットのたびに全体を再生成するので避ける。
- 台帳は 1 スキル 1 エントリ（最新だけ）で、キー順に並べて書く。同時作業での衝突を減らすため。履歴は git が持つ。
- 規則 yaml を `registry/` に置く場合は `lefthook.yml` の `precommit-fix` が走ることを受け入れる（頻繁には変えないので許容できる）。生成コピーは `generate_registry_compat.py` の `COMPAT_FILES` 固定なので対象にならない。
- `meta:` にフィールドを足さない理由（全件の `meta.version` を上げることになる）は overview の決定事項にある。Step1 で「規則では分けきれない」と分かった場合だけ見直す。

## ルール更新ポイント

- `AGENTS.md`（「AIツール/プラグイン設定のSSOT」節）・`README.md`・`README_EN.md`: 規則 yaml を `registry/` に置いた場合、SSOT yaml の列挙に追加する。
- `maintenance/README.md`: `maintenance/state/` を作った場合、サブフォルダの一覧に追加する。
- 台帳の書式と更新手順の説明は Step4 の `maintenance/docs/` に書く（ここでは書かない）。

## 進め方

- **実行主体**: メイン単独（2 ファイル + 1 行の変更で、分割する方が高くつく）。
- **TODO化**: 「規則 yaml」「台帳」を 1 項目ずつ、計 2 項目。
