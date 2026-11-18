---
type: Plan Step
status: planning-research
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

## 調査結果

（実行時に要約＋参照 URL で書く。読んだページの全文は書かない。後続ステップに影響する事実は、ステップ3・4のプラン本文へ直接反映する）

## 進め方

- **実行主体**: メインエージェント。Web 調査は `web-lookup` スキルで行う。3アプリの調査は互いに独立しているので、アプリごとに読み取り専用のサブエージェント3体へ並行で委任してよい。委任先には「要約＋URL＋取得可否」だけを返させ、採否（スクリプト化するか、`web-lookup` に任せるか）はメインが決める。
- **TODO化**: ステップ全体を1項目。結果をこのファイルに残し、ステップ3・4を更新してから完了にする。
