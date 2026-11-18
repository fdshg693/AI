---
type: Plan Step
status: implementing-done
---

# Step 1: 3アプリの公式情報源と取得手段の調査

> [00-overview.md](00-overview.md) の続き。このステップではコードは書かない。

## やること

ChatGPT・Gemini・Claude の利用者向けアプリについて、機能・プラン制限・リリース情報の公式情報源を特定し、それぞれをスクリプトで取得できるか（索引の有無、ボット遮断、JS 描画）を確かめる。結果で、ステップ3のスクリプト構成と、ステップ4で機能マップに載せる機能一覧を確定させる。

## 調査観点

### 情報源の所在（アプリごと）

- ヘルプセンター: ChatGPT は `help.openai.com`、Claude は `support.claude.com`（旧 `support.anthropic.com` からの移行状況も）、Gemini は `support.google.com/gemini`（Gemini Apps Help）
- リリースノート: ChatGPT Release Notes、Gemini Apps の更新情報（`gemini.google/release-notes` 等）、Claude のリリースノート（ヘルプセンター内）
- 料金・プラン比較のページ（Free / Plus・Pro / Team・Business / Enterprise、Google AI Pro・Ultra、Claude Pro・Max・Team・Enterprise）
- 開発者向けでも利用者向けアプリの機能に直結するページ（例: ChatGPT のコネクタ／MCP、Claude のカスタムコネクタ）。API ドキュメントは対象外であることを境界として確認する

### 取得手段（情報源ごと）

- `sitemap.xml`・`llms.txt`・記事一覧 API（Intercom 等のヘルプセンター製品の公開エンドポイント）があるか
- `web-lookup` の `page` サブコマンドで本文が取れるか、ボット遮断（Cloudflare 等）や JS 描画で空になるか
- 日本語ページの有無と、英語版との更新差（英語版を正にするかの判断材料）

### WEB 版の機能一覧（機能マップの見出し候補）

- プロジェクト（ChatGPT Projects／Claude Projects／Gemini の相当機能）
- カスタムアシスタント（GPTs／Gems／Claude の相当機能）
- 外部連携（ChatGPT のコネクタ・MCP・開発者モード、Gemini の拡張機能・アプリ連携、Claude のコネクタ・リモート MCP）
- メモリ・パーソナライズ、ファイルアップロード、Deep Research、Canvas／Artifacts、エージェント機能、画像・動画生成、音声、共有・チーム管理
- 上記がプランごとにどう違うか（どのページに書かれているか、までで十分）

## 調査結果（後続ステップから参照する）

2026-11-18 実施。英語版を正にする（ChatGPT の日本語版リリースノートは約4か月遅れていた）。

| アプリ  | ヘルプセンター                                                                        | 索引                                                                                                           | 本文の取り方                                 | リリースノート                                                                                     |
| ------- | ------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Claude  | `support.claude.com`（`support.anthropic.com` は転送済み）                            | `/llms.txt` の `## English` 節（約386本）。更新日は `/sitemap.xml` の `lastmod`                                | 記事 URL に `.md` を付けて Markdown を直取得 | `/en/articles/12138966-release-notes`                                                              |
| ChatGPT | `help.openai.com/en`                                                                  | sitemap・llms.txt は無い。`/en/collections/<id>` が SSR なので直列クロールで約500本（Crawl-delay 1）           | `web-lookup page`（`.md` 版は無い）          | `/en/articles/6825453-chatgpt-release-notes`（235k 文字。他に Business・Enterprise/Edu・agent 版） |
| Gemini  | `support.google.com/gemini`（`?hl=en` 必須、`co=GENIE.Platform=Desktop` で web 手順） | `/gemini/sitemap` に517 URL。タイトル・lastmod は無く、コミュニティスレッドを含む。並列取得で HTTP 429→CAPTCHA | `web-lookup page`（1ページずつなら取れる）   | `gemini.google/release-notes/`                                                                     |

- 料金ページ（`chatgpt.com/pricing/`・`claude.com/pricing`・`gemini.google/subscriptions/`）は機能表は取れるが価格の数値が JS 描画で抜けることがある。プラン別の上限はヘルプの上限記事を正にする
- `tav extract` はキャッシュ版を返すことがある（Gemini の上限記事で旧モデル名が返った）。HTML の本文取得は web-lookup のフロー（`page` → `tav extract` → ブラウザ）に任せ、`tav` 経由の値は上限・モデル名の確認に使わない
- 「新しさの罠」が多い: ChatGPT の custom GPTs は 2026-12-11 に廃止予定で plugins・skills へ移行、Gemini の Gems は 2026-11 から skills へ移行、ChatGPT の custom MCP は Developer Mode の有効化が不要になり、Plugins 画面から追加する（ヘルプ記事は Business・Enterprise/Edu としか書かないが、Plus の実画面でも追加できることをステップ2で確認）、Gemini も custom apps（MCP）を米国・個人アカウント限定で提供、Claude は新版 projects（beta）が展開中
- プラグインの置き場所は `ai-tools-knowledge` のまま（`topics` に変える理由は見つからなかった）

> 上記は要約。取得可否の実測、機能ごとの記事 URL、情報源ごとの採否の理由は [progress/01-research-results.md](progress/01-research-results.md)。Gemini ヘルプの記事タイトル一覧（290本）は [progress/01-gemini-help-index.md](progress/01-gemini-help-index.md)。ステップ2〜4のプラン本文は反映済み。

## 進め方

- **実行主体**: メインエージェント。Web 調査は `web-lookup` スキルで行う。3アプリの調査は互いに独立しているので、アプリごとに読み取り専用のサブエージェント3体へ並行で委任してよい。委任先には「要約＋URL＋取得可否」だけを返させ、採否（スクリプト化するか、`web-lookup` に任せるか）はメインが決める。
- **TODO化**: ステップ全体を1項目。結果をこのファイルに残し、ステップ3・4を更新してから完了にする。
