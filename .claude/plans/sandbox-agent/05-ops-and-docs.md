# Step 5: ブランチ保護Runbook・ドキュメント整備・`.claude/rules`新設

[04-orchestrator.md](04-orchestrator.md) の続き（最終ステップ）。コードの新規実装は最小限で、主にドキュメント化と安全設定の適用手順の明文化を行う。

## やること

1. ブランチ保護ルールの設定手順をRunbook化する（[01-research.md](01-research.md)で確定済みのAPI仕様を、実際に適用する手順として書く。GitHub UIまたは`gh api`コマンドのどちらで適用するかを決める）。
2. `tools/sandbox/README.md`を「ラフプラン」のままではなく、実装後の使い方（前提条件・起動方法・停止方法）を追記する形に更新する。
3. `tools/sandbox/AGENTS.md`（`tools/claude-wrapper/AGENTS.md`と同様の構成）を新設し、`tools/sandbox/`配下のファイル構成を一覧化する。
4. `.claude/rules/sandbox-agent.md`を新設し、`tools/sandbox/**`を触る際の注意点（Bypass Permission運用・ネットワークサンドボックス設定・GitHub Appトークン更新）を記録する。

## 読むべきファイル・実行推奨Grep

**ドキュメント構成の前例を揃えるため（優先度: 高）**

- 読む: `tools/infra/ai-logs/README.md` — 「背景・目的」「スコープ」「アーキテクチャ」「運用」「オープン課題」という節構成の前例。本ステップの`tools/sandbox/README.md`更新もこれに準じる
- 読む: `tools/claude-wrapper/AGENTS.md` — `CLAUDE.md`が`@./AGENTS.md`で本体を委譲する、このリポジトリの命名規約

**ルールファイルのフォーマットを確認するため（優先度: 高）**

- 読む: `.claude/skills/writing-rules/writing.md` — `paths:`フロントマターの書き方、本文は10〜30行程度に収める指針

**ルートREADMEへの追記要否を判断するため（優先度: 中）**

- 読む: `README.md`（リポジトリ直下）42-47行目 — `tools/`配下の主要サブフォルダ一覧の現在の記載粒度（`aim/`, `claude-wrapper/`等は列挙されているが全サブフォルダを網羅してはいない）。`sandbox/`を追記するかはこの粒度感に合わせて判断する

## 触るファイル

### 新規

- `tools/sandbox/docs/branch-protection.md` — [01-research.md](01-research.md)のブランチ保護API仕様を元にした適用手順（`gh api`コマンド例、または手動UI手順）
- `tools/sandbox/AGENTS.md` / `tools/sandbox/CLAUDE.md`（`@./AGENTS.md`委譲）
- `.claude/rules/sandbox-agent.md` — 新規ルールファイル（フロントマターは後述）

### 変更

- `tools/sandbox/README.md` — 冒頭に「ラフプラン」節を残しつつ、末尾に実装後の使い方（前提条件・起動/停止コマンド）を追記
- `README.md`（リポジトリ直下） — 42-47行目の`tools/`一覧に`sandbox/`の1行を追記するか、既存の粒度（主要サブフォルダのみ列挙）と照らして判断する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                              | 理由                                                                                                                                                  |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| ブランチ保護は`gh api`コマンドで適用する手順として書く（Terraform等のIaC化はしない）                                                              | 個人リポジトリの一度きりの設定であり、`tools/infra/ai-logs/terraform/`のような繰り返し適用が必要なインフラではないためIaC化はオーバーエンジニアリング |
| ルートREADMEへの追記は「他の`tools/`配下サブフォルダと同程度の粒度で1行追記する」を基本方針とし、詳細は実装時にREADMEの既存記載を見て最終判断する | プラン時点でルートREADMEの厳密な追記位置まで決め切るより、実装時に周辺文脈を見て自然な形に収める方が良い                                              |

## `.claude/rules` 更新ポイント

新規ルールファイル `.claude/rules/sandbox-agent.md` を作成する。フロントマターで対象パスを列挙する:

```markdown
---
paths:
  - "tools/sandbox/**"
---

## サンドボックスエージェント運用の注意点

- Bypass Permissionはサブエージェントにも継承され上書きできない。`disallowed_tools`で不要なツール（Agent等）を明示的に外すこと。
- ネットワーク制御はDockerネットワーク自体ではなくClaude Code組み込みの`sandbox.network.allowedDomains`が主防御。許可ドメインを追加する際は`tools/sandbox/docker/claude-settings/settings.json`を更新する。
- GitHub Appのinstallation access tokenは1時間で失効する。コンテナ起動のたびに新規取得する設計であり、長時間実行のコンテナでは再取得ロジックが必要になる点に注意。
```

（本文は実装完了後の実際のファイル構成・ハマりどころに合わせて実装時に更新してよい。上記は現時点で判明している注意点の下書き）
