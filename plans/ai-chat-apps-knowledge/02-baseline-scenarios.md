---
type: Plan Step
status: implementing-done
---

# Step 2: 評価シナリオとスキル無しのベースライン（RED）

> [00-overview.md](00-overview.md) の続き。writing-skill-complex の「スキルを書く前に失敗を見る」に当たる。

## やること

スキルが答えられるべき質問を評価シナリオとして 6〜10 個決め、スキル無しのサブエージェントに回答させて、どう間違えるか（古い機能名、存在しない設定、プラン制限の誤り、出典なし、Web を調べずに記憶で答える等）を記録する。ステップ3・4はこの記録で見つかった失敗を潰すように書く。

## 読むべきファイル

- テストの型を確認する
  - `skills/plugins/cc-knowledge/skills/writing-skill-complex/SKILL.md` — RED/GREEN/REFACTOR の手順。このスキルは規律を強制するスキルではなく参照スキルなので、「プレッシャーシナリオ」ではなく「取り出し・適用シナリオ」の節を使う
  - `skills/plugins/cc-knowledge/skills/writing-skill-complex/testing-skills-with-subagents.md` — シナリオの書き方・記録の仕方

## 触るファイル

- `skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/tests/scenarios.md`（新規）— シナリオ一覧と、各シナリオの RED の結果（要点と失敗の型）。ステップ5で GREEN の結果を同じ表に足す

## 決定事項

- シナリオは少なくとも次の型を1つ以上含める
  - 手順: 「ChatGPT の WEB 版で自作の MCP サーバーを繋ぐ手順と必要なプラン」
  - 上限・条件: 「Claude の Projects に入れられるファイルの上限」「Gemini の Gems を共有できるか」
  - 横断比較: 「3アプリのプロジェクト機能の違い」「カスタムアシスタント機能の対応表」
  - 新しさの罠: ベースライン時点の直近リリースノートに載っている変更。ステップ1で拾った候補（2026-11-18 時点。詳細は [progress/01-research-results.md](progress/01-research-results.md)「機能の現状」）:
    - 「ChatGPT Plus で GPT を新しく作る手順」→ 個人プランでは新規作成不可。custom GPTs は 2026-12-11 に廃止予定で、移行先は plugins
    - 「Gemini の Gem を作って共有したい」→ 個人アカウントは 2026-11 から skills へ移行中（共有自体は今も可能）
    - 「ChatGPT Plus で自作の MCP サーバーを繋ぐ（開発者モード）」→ Developer Mode の有効化は不要になった。ヘルプ記事は Business・Enterprise/Edu（Pro は read/fetch）としか書かないが、Plus の実画面でも追加できる。RED 実施後にユーザー指摘と画面で確認（[tests/scenarios.md](../../skills/plugins/ai-tools-knowledge/skills/ai-chat-apps/tests/scenarios.md) の補足）
    - 「Gemini で MCP サーバーを繋げるか」→ custom apps として可能だが、米国・18歳以上・個人アカウント・英語のみ
    - 「Claude の Projects の上限」→ Free は5個まで。新版 projects（beta）が展開中で挙動が違う
  - 範囲外: API・Claude Code の質問（既存の `claude-api`・`claude-code-docs` 等へ渡すべきもの）
- 正解は回答時点の公式ページで判定する。正解そのものを scenarios.md に固定値として書かない（すぐ古くなる）。書くのは「判定に使う公式ページ」と「失敗の型」。
- 注意: ベースラインのサブエージェントは Web 検索を使えると記憶ではなく検索で答えることがある。それ自体は正しい挙動なので、「検索したか」「公式ページに辿り着いたか」「手数」も記録する。

## ルール更新ポイント

- なし。

## 進め方

- **実行主体**: シナリオ設計はメイン。回答は `general-purpose` サブエージェントにシナリオ1つずつ（または数個まとめて）並行で投げ、スキルを読ませない指示を明示する。判定はメインが行う。
- **TODO化**: 「シナリオ確定」「RED 実行と記録」の2項目。
