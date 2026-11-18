# Step 1 調査結果の詳細（2026-11-18）

プラン本文の要約は [../01-research-official-sources.md](../01-research-official-sources.md)「調査結果」。ここは根拠の生データと判断の経緯。

## 取得可否の実測

`curl`（ブラウザ UA）と `web-lookup page` で確認した。

| URL                                                                                       | 結果                                                                                                                                               |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `help.openai.com/sitemap.xml`・`/sitemap_index.xml`・`/en/sitemap.xml`                    | 404                                                                                                                                                |
| `help.openai.com/llms.txt`・`/en/llms.txt`・`openai.com/llms.txt`・`chatgpt.com/llms.txt` | 404                                                                                                                                                |
| `help.openai.com/robots.txt`                                                              | 200。`Crawl-delay: 1`、Sitemap 行なし                                                                                                              |
| `help.openai.com/en/articles/<id>.md`                                                     | `.md` は無視され HTML が返る（Intercom の Markdown 版は無い）                                                                                      |
| `help.openai.com/en/collections/<id>`                                                     | 200。記事・下位コレクションへのリンクが HTML に入っている（SSR）                                                                                   |
| `openai.com/sitemap.xml`                                                                  | 200。マーケティングサイトのみで、ヘルプセンターは含まない                                                                                          |
| `support.claude.com/llms.txt`                                                             | 200。5155 行、言語別（`## English` ほか 12 言語）→ 製品別 `###` 見出し → `- [タイトル](….md)`                                                      |
| `support.claude.com/en/articles/<id>-<slug>.md`                                           | 200。記事本文の Markdown                                                                                                                           |
| `support.claude.com/sitemap.xml`                                                          | 200（9.7 MB）。4767 URL すべてに `<lastmod>`。うち `/en/` は 401                                                                                   |
| `support.anthropic.com/en/`                                                               | `support.claude.com/en/` へリダイレクト（移行済み）                                                                                                |
| `support.google.com/gemini/sitemap`                                                       | 200（2.9 MB、`text/xml`）。517 URL、すべて `hl=en`（他言語は `xhtml:link` の alternate）。`lastmod` なし、タイトルなし。コミュニティスレッドを含む |
| `support.google.com/gemini/sitemap.xml`                                                   | ヘルプセンターのトップへリダイレクト（使えない）                                                                                                   |
| `support.google.com/robots.txt`                                                           | `/*/search`・`/*/api*` を Disallow。Crawl-delay なし                                                                                               |
| `gemini.google/sitemap.xml`                                                               | sitemap index（`sitemap_1`〜`4`）。`sitemap_1` の 29 URL が英語の製品ページ（`/overview/<機能>/` 等）。2〜3 は国別ロケールの複製                   |
| `gemini.google/llms.txt`                                                                  | 404                                                                                                                                                |
| `gemini.google/release-notes/`                                                            | 200。`page` で本文が取れる（73k 文字）。言語指定なしだと日本語 UI だが本文は英語                                                                   |
| `developers.openai.com/llms.txt`                                                          | 200（開発者向け。対象外だが MCP サーバー構築の公式手順はここ）                                                                                     |

### `web-lookup page` の結果

- `help.openai.com` の記事: 取れる（例: custom MCP 15k 文字、release notes 235k 文字）
- `support.claude.com` の記事: 取れる。ただし `.md` を直接取る方が軽くて確実
- `support.google.com/gemini/answer/<id>`: 取れる。ただし言語指定なしだと日本語版になる → `?hl=en` を付ける。`co=GENIE.Platform=Desktop` 等でプラットフォーム別の手順に切り替わる
- 料金ページ（`chatgpt.com/pricing/`・`claude.com/pricing`・`gemini.google/subscriptions/`）: 機能の有無の表は取れるが、**価格の数値は JS 描画で抜けることがある**（ChatGPT は価格欄が空）。いずれも日本語ロケールへリダイレクトされる

### Google のレート制限

`support.google.com/gemini` の 517 URL のタイトルを `xargs -P8` で取ったところ（1 分強）、直後から HTTP 429 → `www.google.com/sorry/`（CAPTCHA）へ 302 になった。数分は解けない。索引作りは直列・間隔を空ける必要がある。代替として `tav extract` は通るが、次の問題がある。

### Tavily の取得結果が古い

`tav extract https://support.google.com/gemini/answer/16275805?hl=en` は「Gemini 3 Flash / Pro」のモデル表を返した。同時期の `gemini.google/subscriptions/`（直取得）は「Gemini 4 Argon / Hydrogen」で、sitemap 経由で直取得したタイトルも「Gemini Apps limits & feature availability」（tav 版は「… upgrades for Google AI subscribers」）。Tavily はキャッシュ版を返すことがあり、**上限・モデル名の確認には使えない**。notebooks の記事（16972047）は tav では本文が空（フッターのみ）。

### 日本語版の鮮度

- Claude: `ja` の release notes は英語版と同じ 2026-11-17 まである。llms.txt の `## 日本語` 節も英語とほぼ同数（en 386 / ja 382 行）
- ChatGPT: `ja-jp` の release notes の最新項目は 2026-07-08（英語版は 2026-11-16）。**約 4 か月遅れ**
- Gemini: 未確認（429 のため）。ヘルプは `hl=ja` で翻訳版がある

→ 英語版を正にする。

## 記事数・索引の作り方

- ChatGPT: トップ（`/en`）から 26 コレクション、そこから下位コレクション 37・記事 499 本（重複除去後）を、1 秒間隔の直列で 30 秒程度で集められた。記事の「更新日」は `Updated: 21 days ago` の相対表記だけで、機械可読の日付は見当たらない
- Claude: llms.txt の `## English` 節（約 386 本）がそのまま索引。更新日は sitemap の `lastmod`
- Gemini: sitemap 517 URL → コミュニティ除外・プラットフォーム重複除外で 290 本。タイトル一覧は [01-gemini-help-index.md](01-gemini-help-index.md)

## 機能の現状（2026-11-18 時点。ステップ2の「新しさの罠」・ステップ4の見出し候補）

### ChatGPT

- **custom GPTs は廃止予定**。個人プラン（Free/Go/Plus/Pro）では新規作成・公開が不可。標準の廃止日 2026-12-11（FedRAMP・延期承認は 2027-02-11）。移行先は **plugins**（指示・参照ファイル・connected apps をまとめたもの）。`8554407-gpts-in-chatgpt`、`20001519-custom-gpt-retirement-and-migration-faq`
- **Skills in ChatGPT**: Business/Enterprise/Healthcare/Edu。サイドバー **Plugins** → Plugin Directory → Skills タブ。`20001066-skills-in-chatgpt`
- **Plugins**: `20001256-plugins-in-chatgpt`。apps（旧 connectors）と skills を束ねる単位。設定は **Settings > Plugins**（古いモバイル版は Apps）。`11487775-connected-apps-in-chatgpt`
- **custom MCP server**: ヘルプ記事では Business と Enterprise/Edu の **ChatGPT web**（FAQ で Pro は read/fetch 権限のみ可、Plus は言及なし）。ただし開発者ドキュメントはプラン制限を書かず「personal plugins に出る」とする（ステップ2で判明。2026-11-18 に Plus の実画面でサイドバー「プラグイン」→「追加」→「カスタム MCP サーバーを追加」を確認。Plus で書き込みツールが使えるかは未確認）。workspace では管理者・オーナー（Enterprise/Edu は RBAC で許可された開発者）が作成・テストして workspace に公開。Admin console → Plugins → **Manage Legacy Apps**。Developer Mode を先に有効にする必要は無くなり、サーバーごとのリスク警告の承認になった。`12584461-connecting-custom-mcp-servers-in-chatgpt`。構築側は `developers.openai.com/api/docs/guides/custom-mcp-server`（旧 developer-mode ガイドの URL がここへリダイレクト）
- **Projects**: サインインユーザー全員（プラン・workspace 設定次第）。ファイル数上限はプラン依存で「Plans and limits」ページへ誘導。`10169521-projects-in-chatgpt`
- 上限の記事: `20001625-understanding-chatgpt-and-codex-usage-limits`、`12003714-chatgpt-business-models-and-limits`、`11165333-chatgpt-enterprise-and-edu-models-and-limits`、`9275245-chatgpt-free-tier-faq`
- その他の見出し候補: Memory（`8590148`）、Deep research（`10500283`）、ChatGPT agent（`11752874`）、Scheduled tasks（`10291617`）、Images（`11084440`）、Voice（`20001274`）、Record（`11487532`）、ChatGPT Work、ChatGPT Wallet（2026-11-13）、ChatGPT Sites、group chats は廃止（`12703475-retiring-group-chats-in-chatgpt`）、ChatGPT Atlas は廃止（`20001371-chatgpt-atlas-retirement`）、Sora は終了（`20001152`）
- release notes: `6825453-chatgpt-release-notes`（全プラン）、`11391654-chatgpt-business-release-notes`、`10128477-chatgpt-enterprise-and-edu-release-notes`、`11794368-chatgpt-agent-release-notes`

### Gemini（Gemini Apps）

- **Gems → skills へ移行**: 個人アカウントは 2026-11 から、仕事・学校アカウントは 2027。Gem は自動で skill に再作成される。skills は `/`（今後 `@`）で呼ぶ・自動適用・複数併用可。`answer/18560919`、skills は `answer/17094296`
- **Share a Gem**: 共有可（Viewer/Editor、期限設定可、NotebookLM のノートブックは共有 Gem のソースにできない）。`answer/16504957`
- **custom apps（MCP）**: 「Connected Apps」に MCP サーバー URL を追加。条件は 18 歳以上・米国・個人アカウント・Keep Activity オン・英語のみ。追加は web からのみ（追加後はモバイルでも使える）。開発者向けに Connected Apps Platform と Gemini Developer Mode。`answer/17209137`
- **Connected Apps**（旧 Extensions）: `answer/13695044`、提供条件の表 `table/17434654`
- **notebooks**（プロジェクト相当）: `answer/16972047`（tav では本文が取れなかった。直取得で要確認）
- 上限・機能の提供範囲: `answer/16275805`「Gemini Apps limits & feature availability」（プラン別の倍率・コンテキスト長・機能表）。プランは Google AI Plus / Pro / Ultra（Ultra は 5x/20x）、無料に加え Gemini Go の記事もある
- 製品ページ `gemini.google/overview/<機能>/`（canvas・deep-research・gemini-live・personal-intelligence・video-generation 等）は機能の概要。手順はヘルプ側
- release notes: `gemini.google/release-notes/`（2026-11-17: Tasks in Gemini の無料化 等）

### Claude（claude.ai）

- llms.txt の製品別見出し: Claude / Pro, Max, and Ultra plans / Team and Enterprise plans / Identity management / Claude Cowork / Claude Code / Claude Desktop / Claude Mobile apps / Claude API and Console / Connectors / Claude in Chrome / Claude for Education / Privacy and legal / Safeguards / Amazon Bedrock。プランは Free・Pro・Max・**Ultra**・Team・Enterprise
- **Projects**: 全ユーザー（Free は 5 個まで）。**新版の projects（beta）** が Claude Code から段階展開中（1 プロジェクト = 1 会話、並列スレッドがクラウドで動く）。`9517075-what-are-projects`、RAG `11473015`
- **Connectors / custom connectors（remote MCP）**: `11176164`、`11175166-get-started-with-custom-connectors-using-remote-mcp`、desktop と web の使い分け `11725091`、interactive connectors `13454812`
- **Skills**（カスタムアシスタントの相当機能の一つ）: `12512176`・`12512180`・`12512198`。Plugins ページで plugins・skills・connectors を一元管理 `17740565`
- その他: Artifacts（`17153992`）、Research（`11088861`）、Memory と chat search（`11817273`）、Claude Cowork（`13345190`、web/desktop/mobile `15520349`）、Claude in Chrome、Claude Meetings（2026-11-12、Team/Enterprise beta）、Personal Finance（2026-11-05、米国のみ）、Claude Duet（2026-10-21、research preview）、Claude Docs/Sheets/Slides/Design 等（料金ページの機能表）
- release notes: `12138966-release-notes`

### 横断で見える傾向

3 アプリとも「カスタムアシスタント」が **skills / plugins** へ寄っている（ChatGPT: GPTs → plugins・skills、Gemini: Gems → skills、Claude: projects + skills + plugins）。旧名（GPTs・Gems・Extensions・connectors）での質問を新しい名前に結び付けるのが機能マップの重要な役目になる。

## 採否の判断

| 情報源              | 判断                                                                                                                                             | 理由                                                                                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Help Center  | llms.txt（`## English` 節）を索引としてスクリプト化。本文は `.md` を直取得                                                                       | 公式の索引と Markdown 版があり、writing-skill-web の llms.txt 型にそのまま乗る                                                                                              |
| OpenAI Help Center  | コレクションを直列クロールして索引（タイトル＋URL）を作るスクリプト。本文は `web-lookup page`                                                    | sitemap・llms.txt が無い。コレクションページは SSR で、30 秒程度で 500 本集まる。writing-skill-web のテンプレートに無い取得方法なので、索引ダウンロードの部分だけ追加で書く |
| Gemini Apps Help    | スクリプト化しない。機能マップ（`gemini.md`）に answer ID を手書きし、本文は `web-lookup page`（`?hl=en`）。索引の再作成は README に手順だけ書く | sitemap にタイトルが無く、タイトルを取るには全ページ取得が要る。並列だと CAPTCHA になる。1 ページずつの取得なら問題ない                                                     |
| リリースノート 3 本 | 都度 `web-lookup page`（Claude は `.md`）                                                                                                        | 1 ページなので索引不要。ChatGPT 版は 235k 文字と大きいので、先頭（最新）から読む                                                                                            |
| 料金ページ          | 機能の有無だけ参照。価格の数値はヘルプの上限記事・料金ページの再確認を促す                                                                       | 価格が JS 描画で抜ける                                                                                                                                                      |
| `tav`               | 記事を探す補助のみ。上限・モデル名は直取得で確認                                                                                                 | キャッシュが古いことがある                                                                                                                                                  |
| HTML 本文の取得全般 | スクリプトでは取らず web-lookup のフローに任せる（調査後のユーザー指示で決定）                                                                   | JS 描画による欠落の検知と代替経路（`tav extract`・ブラウザ）は web-lookup 側に揃っている                                                                                    |
