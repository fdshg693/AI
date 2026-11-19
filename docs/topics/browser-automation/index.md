# browser-automation/ — playwright-cli によるブラウザ操作の実測ノート

`playwright-cli` と、その補助ツール `pwq`・`pwdo`（[tools/browser/](../../../tools/README.md)）、ブラウザ操作スキル（プラグイン `browser`、`my-tools` の `browser-context-tools`）の設計の根拠になった実測の記録。数値の正は各ツールの README とスキル本文で、ここはその根拠と、本文に載せない失敗の内訳を持つ。実測はすべて [tools/browser/test-sites](../../../tools/browser/test-sites/README.md)（ローカル）に対して行った。

- [delegation](delegation.md) — `pwdo`（ブラウザ操作の一区間を安いモデルへ委譲）の実測・3 経路のコスト比較・ガードレールの検証。Use when `pwdo` の契約・既定値・ガードレールを変えるとき。
- [site-recon](site-recon.md) — ブラウザを開く前のサイト偵察（`curl` での robots/sitemap/llms.txt・リンク抽出・Tavily `map` のコスト）の実測。Use when `using-playwright-cli` の `site-recon.md` を変えるとき。
- [script-cli-roundtrip](script-cli-roundtrip.md) — 対話コマンドと `run-code` スクリプトの往復（記録・現在地からの再実行・init チャンク）の実測。Use when 往復ワークフローや `pwdo` のスクリプト回収を変えるとき。
- [scripted-automation](scripted-automation.md) — 認証が絡む作業のスクリプト化（storage state・ユーザー待機・ログイン後の再開）の実測。Use when `sharing-browser-with-user` の `scripted-automation.md` を変えるとき。
- [browser-handoff](browser-handoff.md) — ブラウザセッションをユーザーへ渡して戻す（headed Chrome・永続プロファイル・ログイン完了の検知）の実測。Use when `sharing-browser-with-user` の引き渡し手順を変えるとき。
