---
type: Plan Step
status: planning-breakdown
---

# Step 1: 各 SDK の上限・使用量 API の調査

## やること

規約 §3（上限）と §7（ログ）を満たすために、5 つの SDK で「何を指定でき、何が返ってくるか」を確認し、各実装ステップの「決定事項」に反映する。コードは書かない。

## 調査観点

SDK ごとに、次の 4 点を「指定方法 / 取得方法 + 参照 URL」で 1〜2 行ずつまとめる。指定できないものは「不可」と明記する。

| SDK（使っているワークフロー） | 確認先 |
| --- | --- |
| Claude Agent SDK Python（claude-wrapper・issue-agent・sandbox） | `claude-agent-sdk` スキル。`ClaudeAgentOptions` の `max_turns` / `max_budget_usd`、`ResultMessage` の `total_cost_usd` / `usage` / `model_usage` / `session_id` / `num_turns` |
| Cursor Python SDK（cursor-wrapper） | `cursor-sdk-use` スキル。`Agent.create` / `send().wait()` のタイムアウト、ターン上限、結果オブジェクトの使用量・解決後モデル |
| Codex Python SDK `openai-codex`（codex-wrapper） | `codex-sdk-use` スキル。`thread_start` / `run` のタイムアウト・ターン上限、結果の使用量・スレッド ID |
| Cline SDK `@cline/sdk` 0.0.65（cline-wrapper） | `cline-sdk-docs` スキル。`maxIterations` 以外のタイムアウト・予算、結果の `usage` とモデル ID |
| GitHub Copilot SDK `@github/copilot-sdk` 1.0.11（copilot-wrapper） | `github-copilot-sdk-docs` スキル。`session.send` の待ち時間上限（`sendAndWait` の timeout 等）、ターン上限、使用量イベント |

観点:

1. ターン数（反復回数）上限の指定方法
2. タイムアウト（壁時計）の指定方法。SDK に無ければ呼び出し側で `asyncio.wait_for` / `AbortController` 等で包めるか
3. 予算（USD・トークン）上限の指定方法
4. 実行後に取れる値: 解決後モデル ID、セッション（スレッド）ID、ターン数、コスト／トークン数、終了理由

## 調査結果

（実行時に要約 + 参照 URL を書く。詳細は `progress/01-research-results.md`）

## 進め方

- **実行主体**: SDK ごとに独立なので、5 つを並行してサブエージェントへ委任してよい（各スキルを使わせる）。採否は本ステップで判断する。
- **TODO化**: 1 TODO。結果を 02〜08 の「決定事項」に転記し終えたら完了。
