---
type: Plan
status: implementing-done
order: 2/3
depends_on:
  - ../account-foundation/00-overview.md # Step3（入力検証基盤）まで完了していること
blocks:
  - ../notification-preferences/00-overview.md # 本プラン完了後に着手可
---

## 実装ステータス

- [x] [01-research-zipcloud-api.md](01-research-zipcloud-api.md) — 外部API仕様の事前調査
- [x] [02-api-client-and-form.md](02-api-client-and-form.md) — APIクライアント実装 + フォーム組み込み

# 郵便番号からの住所自動入力機能 実装プラン - 概要（サンプル）

> 架空の機能を題材に、複数ステップに分割するプランの概要を示すサンプル。実装対象ではありません。`../account-foundation/`と`../notification-preferences/`は架空の兄弟プランで、依存がないプランには`order`/`depends_on`/`blocks`を付けない。

## 要件

- 会員登録フォームの郵便番号欄に、外部API（zipcloud）を使った住所自動入力を追加する。
- 該当住所が無い場合はエラーにせず、住所欄を空のまま残す。

## 実装ステップ

1. [01-research-zipcloud-api.md](01-research-zipcloud-api.md) — 外部API仕様の事前調査（Web調査 + 既存コード調査をサブエージェントへ委任） → 詳細結果: [progress/01-research-results.md](progress/01-research-results.md)
2. [02-api-client-and-form.md](02-api-client-and-form.md) — APIクライアント実装 + フォーム組み込み → 実装メモ・差分: [progress/02-implementation-notes.md](progress/02-implementation-notes.md)

## 主要な決定事項

| 決定                                                                             | 理由                                                                                                    |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| DBスキーマは変更しない（住所は取得のたびにフォームへ表示するだけで永続化しない） | 保存が要件に含まれておらず、永続化は過剰設計                                                            |
| 外部APIクライアントは新規レイヤー `Services/ExternalApi/` として独立させる       | Article本体のドメインロジックとは無関係な横断的関心事であり、既存の `ArticleService` 等とは責務が異なる |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `ArticleShare/Services/ExternalApi/IPostalCodeApiClient.cs` / `PostalCodeApiClient.cs`
- `ArticleShare/wwwroot/js/postal-code-autofill.js`
- `rules/external-api.md`

### 変更

- `ArticleShare/Controllers/AccountController.cs`
- `ArticleShare/Views/Account/Register.cshtml`

## ルール更新ポイント

> ルールの格納先はレポジトリによって異なる。`rules/`（Claude Code・複数ファイル＋`paths:`フロントマター）、`AGENTS.md`（レポジトリ直下・Codex等）、`CLAUDE.md`（Claude Codeのプロジェクトメモリ）、`.clinerules`（Cline）など。本サンプルでは `rules/` を前提で書くが、実際のプランでは対象レポジトリの既存ルール格納先に合わせて読み替えること。

- `external-api.md`（Step2, 新規作成・フロントマター付き）: 外部APIクライアントの配置規約とレスポンス成否判定の注意点

## 進め方

- **TODO化**: ステップ一覧の各項目をそのまま1つのTODOにする。各ステップの実行主体・TODO粒度は各ステップファイルの「進め方」節に書き、概要には持ち込まない（概要は目次・導線を保つ）。

---

## 書き方のポイント

- **要件は2〜4行の箇条書きで十分。** 背景の説明やユースケースの動機は書かない。
- **外部API・外部ライブラリなど、実装前にWeb上の仕様を確認しないと決定事項が固まらない機能は、調査を独立したステップ（Step1）として先に置く。** 実装ステップ（Step2）はその結果を前提に書けるので、調査時に読んだページの全文を実装ステップ側に持ち込まずに済む。詳細は[plan-writing.md](../../guides/plan-writing.md)の「外部知識が必要な場合」節を参照。
- **実装ステップの数は機能の複雑さなりに。** 小さい機能は調査ステップも不要で、1ファイルに収める（[../tag-popularity-sort.md](../tag-popularity-sort.md) 参照）。無理に `00-overview.md` + 複数ステップの型に当てはめない。
- **決定事項は「決定」と「理由」を1行ずつ。** 判断の根拠となる規約は `[[リンク]]` で指すだけにする。理由の全文はリンク先のルールファイル（`rules/`・`AGENTS.md`・`CLAUDE.md` 等、レポジトリの格納先）に書かれているべきもので、プラン側で重複させない。
- **ファイル一覧は「新規」「変更」の2分類のみ。** 「読むべきファイル・推奨Grep」のような、実装者向けの詳細な手引きは各ステップファイル側に書き、概要ファイルには持ち込まない。
- **frontmatter直下の「実装ステータス」は必須。** 各項目はステップファイルへのリンクにする（`lint_plans.py` はリンク先で照合する）。更新のタイミングと`status`の遷移は[plan-writing.md](../../guides/plan-writing.md)の「status の遷移基準」節を参照。
- **別プランの依存はoverviewのfrontmatterで表す。** `order`は読みやすい予定順、`depends_on`は着手条件、`blocks`はその逆方向の宣言。パスは兄弟プランのoverviewを指し、コメントで必要な完了ステップを補足する。2つのプランの片側だけを更新しない。
