---
type: Plan Step
status: implementing-done
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

- 新規: `maintenance/skill-risk/volatility.yaml` — プラグイン・パス単位の既定値（`rules` の `prefix`。最長一致）と個別の上書き（`overrides`）、規則に当たらないときの `default: medium`
- 新規: `maintenance/skill-risk/dogfood.yaml` — `entries:` の下に canonical ID（`.../SKILL.md`）をキーにした記録。項目は `date`・`verdict`（`ok` / `needs-fix` / `fixed`）・`fb`（fb ファイル名）か `note`・`fix`（`<repo>@<short-hash>`）。今は `entries: {}`
- 変更: `maintenance/README.md`（サブフォルダの一覧に `skill-risk/` を追加）

## 決定事項・注意点／落とし穴

- キーは skill-tools の canonical ID（リポジトリ相対の `.../SKILL.md` パス。例: `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`）にそろえる。同名スキルがプラグイン違いで存在しうるため（`skill-tools --fb` も曖昧な名前を拒否している）。
- 台帳はアンブレラに置く。サブモジュールに置くと、ドッグフーディングのたびに 2 段階コミットが要る。`skills/` 配下や `registry/` に置くと、`lefthook.yml` の `precommit-fix`（glob に `**/skills/**`・`registry/*.yaml`）がコミットのたびに全体を再生成するので避ける。
- 台帳は 1 スキル 1 エントリ（最新だけ）で、キー順に並べて書く。同時作業での衝突を減らすため。履歴は git が持つ。
- 規則 yaml も `registry/` に置かない。読むのは Step3 のスクリプト 1 本だけで、`repo-ssot-pattern` の「複数の生成物・検査が読む手編集 yaml」に当たらない（リポジトリ都合 → `maintenance/`）。台帳と同じ `maintenance/skill-risk/` にまとめる。`**/skills/**` の glob にも当たらないので `precommit-fix` は走らない。`registry/local-configs.yaml` の `deny_patterns` にも当たらない。
- `meta:` にフィールドを足さない理由（全件の `meta.version` を上げることになる）は overview の決定事項にある。Step1 でプラグイン単位の既定値でほぼ分けられることを確かめた。
- 段階は `high` / `medium` / `low` の 3 つ。プラグイン単位の既定値（Step1 の件数つき）:

  | 段階   | プラグイン                                                                                                           | 理由                                                               |
  | ------ | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
  | high   | `ai-tools-knowledge`（48）・`cc-knowledge`（19）・`topics`（12）・`web-lookup`（2）・`browser`（4）                  | 外部ツール・外部サービスの仕様や API が題材                        |
  | medium | `my-tools`（17）・`agent-compat-tools`（1）・`maintenance/plugin`（7）・`cicd`（4）・`doc-tools`（1）・`others`（2） | 自作ツールやリポジトリ構成が題材。変化は「依存先の変化」でも拾える |
  | low    | `coding`（7）・`subagents`（3）・`no-code`（1）・`special`（2）                                                      | 普遍的な手順・見本                                                 |

- 個別の上書きの初期値: `topics/skills/writing-mermaid-diagrams` → low、`coding/skills/gh-pr` → medium（`gh` CLI に依存）。
- 規則に当たらないスキルは `medium` とし、ランキングの出力に「規則なし」と出す（新しいプラグインを足したときに気づけるように）。

## ルール更新ポイント

- `maintenance/README.md`: サブフォルダの一覧に `skill-risk/` を追加した。`registry/` に置かなかったので SSOT yaml の列挙（`AGENTS.md`・`README.md`・`README_EN.md`）は変えない。
- 台帳の書式と更新手順の説明は Step4 の `maintenance/docs/` に書く（ここでは書かない）。

## 進め方

- **実行主体**: メイン単独（2 ファイル + 1 行の変更で、分割する方が高くつく）。
- **TODO化**: 「規則 yaml」「台帳」を 1 項目ずつ、計 2 項目。

## 実行中に判明した変更

- 2026-11-19（Step1）: 変化しやすさの段階・プラグイン単位の既定値・初期の上書きを決定事項に追加した。
- 2026-11-19（Step2 実行）: 置き場所を `maintenance/skill-risk/volatility.yaml`・`maintenance/skill-risk/dogfood.yaml` に確定（候補の `registry/skill-volatility.yaml`・`maintenance/state/skill-dogfood.yaml` から変更）。対象 130 件を規則で引くと high 84 / medium 33 / low 13、規則なし 0 件。台帳の判定値は英語（`ok` / `needs-fix` / `fixed`）にし、fb ファイル名は実在の形式 `YYYYMMDD-HHMMSS-fb.md` に合わせた。
