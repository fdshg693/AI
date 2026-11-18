---
type: Plan Step
status: planning-research
---

# Step 4: WEB 版の機能マップ3本と横断比較表

> [00-overview.md](00-overview.md) の続き。機能一覧はステップ1の調査結果で確定させる。

## やること

アプリごとに WEB 版の機能マップ（`chatgpt.md`・`gemini.md`・`claude.md`）を書き、機能の対応関係を `comparison.md` にまとめる。機能マップは「機能名 → 公式ページ URL」の索引であり、具体値（上限・料金）は書かずに公式ページへ誘導する。

## 読むべきファイル

- ステップ1の調査結果（[01-research-official-sources.md](01-research-official-sources.md)「調査結果」）— 機能一覧と情報源 URL
- ステップ2の記録（`.../ai-chat-apps/tests/scenarios.md`）— 機能マップが拾うべき失敗の型
- `skills/plugins/cc-knowledge/skills/writing-skill/bestpractices.md` — 補助ファイルの長さ・目次の作法（100 行を超えるなら冒頭に目次）

## 触るファイル

- `.../ai-chat-apps/chatgpt.md` / `gemini.md` / `claude.md`（新規）— 各ファイルの構成を揃える:
  - 冒頭に最終確認日と、そのアプリの情報源（ヘルプセンター・リリースノート・料金ページ）
  - 機能ごとに: 機能名（UI 上の表記・旧称）、1〜2 行の説明、公式ページ URL、プラン差が書かれているページ、確認時の注意（地域限定・ベータ等）
  - 例: ChatGPT の「コネクタ／MCP（開発者モード）」「Projects」には、設定の入口（UI 上の場所）と対応プランのページを必ず載せる
- `.../ai-chat-apps/comparison.md`（新規）— 機能カテゴリを行、3アプリを列にした対応表（各セルは機能名＋機能マップ内の該当節へのリンク）。「同じ名前でも中身が違う」もの（例: Canvas、Projects）の注意を表の下に書く

## 決定事項

- 具体値（ファイル数上限、メッセージ上限、料金）は機能マップに書かない。変わりやすく、古い値が残ると誤答の原因になる。どうしても載せる値は確認日を併記する。
- 機能名は UI の英語表記を正にし、日本語 UI の表記を併記する（ユーザーが日本語で質問するため）。
- SKILL.md には機能マップの内容を重複させない（ハブはファイル名と使い分けだけ）。
- 落とし穴: Gemini は「Gemini アプリ」と「Google Workspace の Gemini」「Google AI Studio」で機能・ヘルプが分かれている。対象は Gemini アプリ（gemini.google.com）に絞り、境界を `gemini.md` の冒頭に書く。Claude も claude.ai と Claude Code・API を分ける。

## ルール更新ポイント

- なし。

## 進め方

- **実行主体**: アプリ別の3ファイルは互いに独立しているので、`general-purpose` サブエージェント3体に並行で書かせてよい（ファイルが別なので worktree 分離は不要）。共通の構成テンプレートをメインが先に1つ書いて渡す。`comparison.md` は3本が揃ってからメインが書く。
- **TODO化**: 「構成テンプレート」「3アプリの機能マップ」「comparison.md」の3項目。
