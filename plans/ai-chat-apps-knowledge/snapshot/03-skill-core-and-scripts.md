---
type: Plan Step
status: planning-research
---

# Step 3: SKILL.md（ハブ）と取得・検索スクリプト

> [00-overview.md](00-overview.md) の続き。スクリプト構成はステップ1の調査結果で確定させる（現時点では候補）。

## やること

スキル `ai-chat-apps` の骨格を作る。SKILL.md は「どのアプリのどの機能か → どの補助ファイル・どの取得手段を使うか」を振り分けるハブにし、詳細はアプリ別の機能マップ（ステップ4）と公式ページの都度取得に任せる。索引が取れる情報源には、writing-skill-web のテンプレートで索引ダウンロード・検索・ページ取得のスクリプトを用意する。

## 読むべきファイル

### 優先度高: 型を決めるために読む

- `skills/plugins/cc-knowledge/skills/writing-skill-web/SKILL.md` — 静的スナップショット型と動的取得型の選び方、鮮度判定
- `skills/plugins/cc-knowledge/skills/writing-skill-web/scripts/`（`webref_cli.py`・`download_url_index.py`・`select_url_index.py`・`fetch_selected_pages.py`）— コピー元のテンプレート
- `skills/plugins/cc-knowledge/skills/writing-skill/SKILL.md` と同階層の `bestpractices.md` — name・description・段階的開示の作法

### 優先度中: 似た実例を見る

- `skills/plugins/topics/skills/litellm-docs/` — URL 索引のダウンロード＋選択取得の実例
- `skills/plugins/ai-tools-knowledge/skills/github-copilot-docs/` — 同じプラグイン内の docs スキルの書きぶり
- `skills/plugins/web-lookup/` — 索引を持たない情報源の取得手段（`page` サブコマンド）

## 触るファイル

- `.../ai-chat-apps/SKILL.md`（新規）— ハブ。含めるもの:
  - description: ChatGPT・Gemini・Claude の利用者向けアプリ（WEB 版）の機能・設定・プラン差を、学習データではなく最新の公式情報で答えるときに使う、と書く。API・Claude Code・Codex 等は対象外で、既存スキルへ渡すことも書く
  - 手順: (1) アプリと機能を特定 → (2) 機能マップで公式ページを引く（比較なら comparison.md）→ (3) 公式ページを取得して具体値を確認 → (4) 必要ならリリースノートで直近の変更を確認 → (5) URL と確認日を添えて回答
  - 機能マップの最終確認日が古いとき（目安を決める）の扱い
- `.../ai-chat-apps/README.md`（新規）— メンテナ向け。情報源一覧、スクリプトの出自（writing-skill-web のどのテンプレートか）、索引の更新手順
- `.../ai-chat-apps/webref_cli.py` ほか（新規）— 索引が取れる情報源ごとに `download`・`search`・`fetch` を持つ。情報源は設定（アプリ名 → 索引 URL）で切り替える
- `.../ai-chat-apps/output/`（新規）— 索引スナップショット。コミットするかは既存例（`cursor-docs`・`vercel-docs` は `output/llms.txt` 等をコミット）に合わせ、ページ本文の一時取得先 `output/temp/` はコミットしない

## 決定事項

- スクリプトは `${CLAUDE_SKILL_DIR}` 相対で呼ぶ。実行方法（`python` 直か `uv run` か）は writing-skill-web の現行テンプレートに合わせる。
- 索引が取れない情報源（Google のヘルプセンターは取得が難しい見込み）はスクリプト化せず、SKILL.md から `web-lookup` を使う指示にする。この場合 `meta.requires_skills` に `web-lookup` を書く。
- 鮮度: 索引は writing-skill-web の鮮度判定（一定期間を過ぎたら再取得）を使う。期間は情報源の更新頻度から決める。
- 落とし穴: ヘルプセンターは地域・言語でリダイレクトされることがある。取得 URL には言語を明示する（英語版を正にするかはステップ1の結果で決める）。
- 落とし穴: SKILL.md の `!` コマンドで起動時に毎回ダウンロードさせると、3情報源分の通信が毎回走る。起動時はやらず、必要になった情報源だけ取りに行かせる。

## ルール更新ポイント

- なし（スキル内の README.md に情報源と更新手順を書く）。

## 進め方

- **実行主体**: メインエージェント。スクリプトのコピーと情報源ごとの設定は1体で足りる。
- **TODO化**: 「SKILL.md・README.md」「スクリプトと output」の2項目（各1コミット）。
