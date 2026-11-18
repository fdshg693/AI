---
type: Plan Step
status: implementing-done
---

# Step 4: WEB 版の機能マップ3本と横断比較表

> [00-overview.md](00-overview.md) の続き。機能一覧はステップ1の調査結果で確定した（下の「機能一覧」）。

## やること

アプリごとに WEB 版の機能マップ（`chatgpt.md`・`gemini.md`・`claude-ai.md`）を書き、機能の対応関係を `comparison.md` にまとめる。機能マップは「機能名 → 公式ページ URL」の索引であり、具体値（上限・料金）は書かずに公式ページへ誘導する。

## 読むべきファイル

- ステップ1の調査結果（[01-research-official-sources.md](01-research-official-sources.md)「調査結果」）— 情報源 URL
- [progress/01-research-results.md](progress/01-research-results.md)「機能の現状」— 機能ごとの記事 ID（ChatGPT・Claude はここから書き始めてよい。最新の一覧は各索引で引き直す）
- [progress/01-gemini-help-index.md](progress/01-gemini-help-index.md) — Gemini Apps Help の記事タイトルと URL の一覧（290本）。`gemini.md` の answer ID はここから拾う
- ステップ2の記録（`.../ai-chat-apps/tests/scenarios.md`）— 機能マップが拾うべき失敗の型
- `skills/plugins/cc-knowledge/skills/writing-skill/bestpractices.md` — 補助ファイルの長さ・目次の作法（100 行を超えるなら冒頭に目次）

## 触るファイル

- `.../ai-chat-apps/chatgpt.md` / `gemini.md` / `claude-ai.md`（新規）— 各ファイルの構成を揃える:
  - 冒頭に最終確認日と、そのアプリの情報源（ヘルプセンター・リリースノート・料金ページ）
  - 機能ごとに: 機能名（UI 上の表記・旧称）、1〜2 行の説明、公式ページ URL、プラン差が書かれているページ、確認時の注意（地域限定・ベータ等）
  - 例: ChatGPT の「Plugins／apps／custom MCP」「Projects」には、設定の入口（UI 上の場所）と対応プランのページを必ず載せる
- `.../ai-chat-apps/comparison.md`（新規）— 機能カテゴリを行、3アプリを列にした対応表（各セルは機能名＋機能マップ内の該当節へのリンク）。「同じ名前でも中身が違う」もの（例: Canvas、Projects）の注意を表の下に書く

## 機能一覧（各機能マップの見出し）

2026-11-18 時点。行は `comparison.md` の行にもなる。

| カテゴリ                               | ChatGPT                                                                                                                                  | Gemini                                                          | Claude                                                              |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------- |
| プロジェクト                           | Projects                                                                                                                                 | notebooks                                                       | Projects（新版 beta あり）                                          |
| カスタムアシスタント／再利用できる指示 | custom GPTs（2026-12-11 廃止予定）→ Plugins・Skills                                                                                      | Gems（2026-11 から skills へ移行）→ skills                      | Skills・Plugins（Projects も兼ねる）                                |
| 外部連携                               | Plugins／apps（旧 connectors）、custom MCP（web。Plus でも追加可〔実画面で確認〕。ヘルプ記事は Business・Enterprise/Edu としか書かない） | Connected Apps（旧 Extensions）、custom apps（MCP。米国・個人） | Connectors、custom connectors（remote MCP）、interactive connectors |
| メモリ・パーソナライズ                 | Memory、personality                                                                                                                      | memory of past chats、personal intelligence                     | memory・chat search、memory の import/export                        |
| 調査                                   | Deep research                                                                                                                            | Deep Research                                                   | Research                                                            |
| 作成物                                 | Canvas、writing/code blocks、Images                                                                                                      | Canvas、画像・動画・音楽生成、Storybook、Audio Overviews        | Artifacts、Claude Docs/Sheets/Slides/Design 等                      |
| エージェント・自動化                   | ChatGPT agent、Scheduled tasks、ChatGPT Work                                                                                             | Tasks in Gemini、schedules、Gemini in Chrome（auto browse）     | Claude Cowork、Claude in Chrome、scheduled tasks                    |
| 音声                                   | Voice、Record                                                                                                                            | Gemini Live                                                     | voice（要確認）                                                     |
| 共有・チーム管理                       | chat の共有、Business/Enterprise の admin                                                                                                | chat・Gem の共有、仕事・学校アカウント                          | chat・artifacts の共有、Team/Enterprise の admin                    |
| プランと上限                           | Free・Go・Plus・Pro・Business・Enterprise/Edu                                                                                            | 無料・Google AI Plus・Pro・Ultra（Gemini Go の記事あり）        | Free・Pro・Max・Ultra・Team・Enterprise                             |
| 廃止・終了                             | group chats、ChatGPT Atlas、Sora                                                                                                         | Gems（skills へ）                                               | —                                                                   |

## 決定事項

- 具体値（ファイル数上限、メッセージ上限、料金）は機能マップに書かない。変わりやすく、古い値が残ると誤答の原因になる。どうしても載せる値は確認日を併記する。
- 機能名は UI の英語表記を正にし、日本語 UI の表記を併記する（ユーザーが日本語で質問するため）。
- SKILL.md には機能マップの内容を重複させない（ハブはファイル名と使い分けだけ）。
- 旧名（GPTs・Gems・Extensions・connectors・Developer Mode）は機能マップの見出しか別名欄に必ず残し、新しい名前・移行先・廃止日へつなぐ。3アプリともカスタムアシスタントが skills・plugins へ寄っており、旧名での質問が多いと見込むため。
- Gemini の記事 URL は `?hl=en` を付け、web 版の手順が要る記事には `&co=GENIE.Platform%3DDesktop` も付けて書く。
- 落とし穴: Gemini は「Gemini アプリ」と「Google Workspace の Gemini」「Google AI Studio」で機能・ヘルプが分かれている。対象は Gemini アプリ（gemini.google.com）に絞り、境界を `gemini.md` の冒頭に書く。Claude も claude.ai と Claude Code・API を分ける。

## 実行中に判明した変更

- 2026-11-18（ステップ1完了時）: 「機能一覧」節を追加し、旧名の扱いと Gemini の URL 形式を決定事項に追記した。ChatGPT の例を「コネクタ／MCP（開発者モード）」から現行の名前に直した。
- 2026-11-18（実装時）: 実装の確定事項と、上の「機能一覧」から変わった点。
  - Claude の機能マップは `claude.md` ではなく **`claude-ai.md`**。Windows ではファイル名の大小文字を区別しないため、`claude.md` がフォルダの `CLAUDE.md` として Claude Code に読み込まれてしまった。SKILL.md・README.md・00-overview.md のリンクも直した
  - テンプレートは H2 を固定 11 カテゴリ、H3 を UI の英語表記の機能名にした。`comparison.md` はカテゴリを細かくして 17 行（外部連携を「外部サービス連携」と「自作 MCP サーバー」に、メモリを「常設の指示」と「メモリ」に、作成物を文書系と生成系に、エージェントから「ブラウザ操作」「定期実行」を分けた）。下に「同じ名前でも中身が違うもの」「カスタムアシスタントの移行」「自作 MCP サーバーの接続」の 3 節を置いた。リンク先の見出しはすべて存在することをスクリプトで確かめた
  - 各ファイルは 260〜300 行（目標の 250 行を少し超えた）。どれも冒頭に目次がある
  - 機能一覧からの変更（本文で確認）:
    - ChatGPT: **ChatGPT agent は提供終了**（後継は ChatGPT Work・cloud browser）。**Canvas は 2026-05-28 から新しいモデルで使えない**（後継は writing blocks・code blocks）。Pulse は終了（2026-06-17。Scheduled tasks で代わりを作る）。Advanced・Standard Voice は 2026-12-11 に終了。新機能: Space（Library の後継）・dots・workspace agents・Wallet。connectors は 2025-12-18 に apps へ呼び替え
    - Gemini: **個人アカウントの Gems は 2026-11-17 に読み取り専用（新規作成も不可）、2026-12-17 に削除**。S3 の正解が「共有できる」から「個人アカウントではもう作れない、skills を使う」に変わる。Gems from Google Labs・Opal も終了。Past chats は Memory に改名。notebooks は別アプリ Gemini Notebook（support.google.com/gemininotebook）と同期する。Tasks の提供条件はヘルプ本文（Pro・Ultra）とリリースノート（米国・日本ほかで無料化）が食い違う
    - Claude: **Customize メニューは Plugins に改名**（2026-11）。plugins は有料プラン、skills・custom connectors は Free を含む全プラン。単独版 Claude Design は 2026-12-14 に終了。voice mode は web にもある（beta）。Cloud browser・Sheets・Whiteboards・Motion など新機能あり
  - 未確認で残したもの: Gemini の記事は support.google.com が最初から HTTP 429 を返したため、`page` ではなく `tav extract` で本文を取った（キャッシュが古い恐れ。gemini.md の冒頭に明記）。上限記事 16275805 や生成系の記事は「本文未確認」と書いた。ChatGPT Record の対象プランは記事内で食い違う。Claude の日本語 UI 名は日本語ヘルプの表記で、実画面では未確認
  - ステップ5へ: GREEN の判定前に、S3 の正解（Gems は読み取り専用）と、gemini.md の「本文未確認」を `page` で取り直せるか（429 が解けていれば）を確かめる

## ルール更新ポイント

- なし。

## 進め方

- **実行主体**: アプリ別の3ファイルは互いに独立しているので、`general-purpose` サブエージェント3体に並行で書かせてよい（ファイルが別なので worktree 分離は不要）。共通の構成テンプレートをメインが先に1つ書いて渡す。`comparison.md` は3本が揃ってからメインが書く。
- **TODO化**: 「構成テンプレート」「3アプリの機能マップ」「comparison.md」の3項目。
