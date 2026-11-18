---
type: Plan Step
status: implementing-done
---

# Step 5: GREEN 検証・メタ・カタログ・登録

> [00-overview.md](00-overview.md) の続き。writing-skill-complex の GREEN／REFACTOR に当たる。

## やること

ステップ2と同じシナリオをスキルありのサブエージェントで解かせ、全シナリオで公式ページに基づく正しい回答（URL・確認日つき）になることを確かめる。外れたシナリオは原因（振り分けの誤り、機能マップの漏れ、取得失敗）を潰して再検証する。そのうえで meta・カタログ・プラグイン説明を整え、サブモジュールとアンブレラで2段階コミットする。

## 読むべきファイル

### 優先度高: 登録手順を確認する

- `maintenance/plugin/skills/changing-skills-and-tools/SKILL.md` — スキル追加時に更新が要るもの（カタログ生成、`ai-tools.yaml` の要否）
- `registry/meta_field.yaml` と `maintenance/docs/skill-meta-fields.md` — `meta:` の各フィールドの書き方（スカラー文字列、複数値はカンマ区切り）
- `maintenance/plugin/skills/committing/SKILL.md` — サブモジュールの2段階コミット

### 優先度中: 検証の型

- `skills/plugins/cc-knowledge/skills/writing-skill-complex/testing-skills-with-subagents.md` — GREEN・REFACTOR の記録の仕方

## 触るファイル

- `.../ai-chat-apps/tests/scenarios.md`（変更）— GREEN の結果を追記
- `.../ai-chat-apps/SKILL.md`・機能マップ（変更）— 検証で見つかった漏れの修正
- `skills/plugins/ai-tools-knowledge/plugin.json`（変更）— description と keywords に ChatGPT・Gemini・Claude のアプリを足す
- `skills/plugins/ai-tools-knowledge/skills/CATALOG.md` ほか生成物（再生成。手編集しない）

## 決定事項

- `meta.status` は最初 `beta` 相当にし、GREEN を通してから `stable` にするかを決める（値の選択肢は `meta_field.yaml` に従う）。
- `meta.version` は新規なので初期値で作る。以降の変更では必ず上げる。
- `meta.requires_skills` には `web-lookup` を書く見込み（ステップ3の決定による）。
- 検証のサブエージェントには「スキルを使って答える」ことだけを指示し、正解の手がかりを与えない。

## ルール更新ポイント

- なし。`ai-tools.yaml` の更新が要ると判明したら、このステップで更新してこの節を書き直す。

## 進め方

- **実行主体**: GREEN の回答は `general-purpose` サブエージェントに並行で投げ、判定と修正はメイン。登録・コミットはメイン。
- **TODO化**: 「GREEN 実行と修正」「meta・カタログ・plugin.json」「2段階コミット」の3項目。
