---
type: Plan Step
status: implementing-done
---

# Step 3: SKILL.md（ハブ）と取得・検索スクリプト

> [00-overview.md](00-overview.md) の続き。スクリプト構成はステップ1の調査結果（[01-research-official-sources.md](01-research-official-sources.md)「調査結果」）で確定した。

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
- `.../ai-chat-apps/webref_cli.py` ほか（新規）— 情報源 `claude`・`chatgpt` の2つに `download`・`search`・`fetch` を持つ。情報源は設定（アプリ名 → 索引の取り方）で切り替える
  - `claude`: `https://support.claude.com/llms.txt` を取り、`## English` 節だけを索引にする（テンプレートの llms.txt 型）。`fetch` は記事 URL の `.md` を直取得
  - `chatgpt`: `https://help.openai.com/en` から `/en/collections/<id>` を直列（1秒間隔、robots の Crawl-delay）で辿り、`/en/articles/<id>-<slug>` のタイトル＋URL を索引にする（約500本・30秒程度）。テンプレートに無い取得方法なので、この索引ダウンロードだけ新しく書く。`fetch` は持たない（本文は `web-lookup` で取る。決定事項参照）
  - `gemini` はスクリプト化しない（決定事項参照）
- `.../ai-chat-apps/output/`（新規）— 索引スナップショット（`claude` の llms.txt 英語節、`chatgpt` のクロール結果）。コミットするかは既存例（`cursor-docs`・`vercel-docs` は `output/llms.txt` 等をコミット）に合わせ、ページ本文の一時取得先 `output/temp/` はコミットしない

## 決定事項

- スクリプトは `${CLAUDE_SKILL_DIR}` 相対で呼ぶ。実行方法（`python` 直か `uv run` か）は writing-skill-web の現行テンプレートに合わせる。
- Gemini Apps Help はスクリプト化しない。`/gemini/sitemap` にはタイトルが無く、タイトルを取るには全ページ取得が要り、並列取得で HTTP 429→CAPTCHA になったため。記事の特定は機能マップ `gemini.md` に手書きした answer ID で行い、本文は SKILL.md から `web-lookup page` で取る指示にする。リリースノート3本と ChatGPT の記事本文も `web-lookup page` を使うので、`meta.requires_skills` に `web-lookup` を書く。索引を作り直す手順（sitemap → 直列でタイトル取得）は README.md に書く
- HTML ページの本文取得は、スクリプトで書かず `web-lookup` スキルに任せる。SKILL.md には「`web-lookup` の page.md の判断フローに従う」とだけ書き、取得失敗・JS 描画による値の欠落・ログイン壁の判定や `page` → `tav extract` → ブラウザの切り替えを重複して書かない（web-lookup 側の方が欠落の目安や代替経路が整っている）。スクリプトが本文を取るのは Claude の `.md`（静的な Markdown で JS が絡まない。`page` は HTML 以外を content-type で弾く）だけにする
- このスキル固有の注意として SKILL.md に足すのは1点だけ: web-lookup のフローで `tav extract` に切り替わった結果はキャッシュ版のことがある（ステップ1で Gemini の上限記事が旧モデル名で返った）ので、上限・モデル名・対応プランは `page` で取れた版かブラウザで確かめる。`tav search` は記事を探す用途には使ってよい
- 鮮度: 索引は writing-skill-web の鮮度判定（一定期間を過ぎたら再取得）を使う。期間は情報源の更新頻度から決める。Claude は sitemap の `lastmod` が使える。ChatGPT の記事には相対表記（`Updated: 21 days ago`）しか無いので、索引の取得日だけで判定する
- 言語: 英語版を正にする（ChatGPT の日本語版リリースノートは約4か月遅れていた）。取得 URL に言語を明示する: Claude は `/en/`、ChatGPT は `/en/`、Gemini は `?hl=en`。Gemini の web 版手順は `&co=GENIE.Platform%3DDesktop` を付ける
- 料金ページは価格の数値が JS 描画で抜けることがある（`page` での実測）。これの扱いも web-lookup のフロー（値の欠落 → ブラウザ）に任せる。プラン別の上限はヘルプの上限記事（ChatGPT `20001625`・`12003714`・`11165333`、Gemini `answer/16275805`、Claude は Pro/Max/Ultra・Team/Enterprise 節）を正にする
- 落とし穴: SKILL.md の `!` コマンドで起動時に毎回ダウンロードさせると、3情報源分の通信が毎回走る。起動時はやらず、必要になった情報源だけ取りに行かせる。

## 実行中に判明した変更

- 2026-11-18（ステップ1完了時）: スクリプトの対象を `claude`（llms.txt）・`chatgpt`（コレクションのクロール）に確定し、Gemini は `web-lookup page` に任せることにした。言語・鮮度・`tav` の扱いを決定事項に追記した。
- 2026-11-18（ユーザー指示）: HTML の本文取得はスクリプトに持たせず、すべて `web-lookup` のフローに任せることにした（`chatgpt` の `fetch` を削除）。スクリプトの `fetch` は Claude の `.md` だけ。

- 2026-11-18（実装時）: 実装の確定事項。
  - サブコマンドは `download <claude|chatgpt|all>`・`search <語...>`・`fetch <URL...>`（Claude のみ）。`select-urls`／manifest は使わず、`search` が標準出力に結果を出す。古い索引は `search` がその情報源だけ取り直す（起動時の `!` ダウンロードはしない）
  - 鮮度は両方 3 日。Claude の `lastmod` は鮮度判定ではなく、各記事の更新日として索引に載せた（記事 ID で sitemap と突き合わせ）
  - help.openai.com は既定の python-requests の User-Agent に 403 を返すので、ブラウザの UA を送る
  - 実行は `uv run webref_cli.py`。PEP 723 ヘッダーで `requests`・`typer` を宣言し、他プロジェクトからでも動くようにした
  - 索引は `output/claude-index.md`（386 本）・`output/chatgpt-index.md`（499 本）としてコミット。`output/temp/` は gitignore
  - SKILL.md は機能マップ（ステップ4）へのリンクを先に張った。機能マップの最終確認日の目安は 30 日

## ルール更新ポイント

- なし（スキル内の README.md に情報源と更新手順を書く）。

## 進め方

- **実行主体**: メインエージェント。スクリプトのコピーと情報源ごとの設定は1体で足りる。
- **TODO化**: 「SKILL.md・README.md」「スクリプトと output」の2項目（各1コミット）。
