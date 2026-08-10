---
type: Plan Step
status: implementing-done
---

# Step 2: 検索コマンド（`search`）+ ドキュメント整備

> [01-index-build.md](01-index-build.md)の続き。`tools/skill-search/data/skill-index.json`が既に生成できる前提で進める。

## やること

`tools/skill-search/data/skill-index.json`を読み込み、クエリを埋め込みベクトル化してコサイン類似度Top-Nを一覧表示する`search`サブコマンドを、Step1で作った`src/cli.mjs`のディスパッチに追加する。検索本体ロジックは将来の再利用（エージェント向けツール化）に備えてCLI引数パースから独立させる。あわせて`tools/skill-search/AGENTS.md`/`CLAUDE.md`でセットアップ・使い方（`pnpm link --global`によるグローバル導入を含む）を文書化する。

## 読むべきファイル・実行推奨Grep

**参照する既存モジュールのシグネチャを正確に把握するため（優先度: 高）**

- 読む: `skills-site/api/src/lib/embedding-similarity.js`の`topKByEmbedding(queryEmbedding, skills, k)`・`cosineSimilarity` — `skills`は`{ embedding, ...}`の配列であればよく、`skill-index.json`のスキーマとそのまま噛み合う
- 読む: `skills-site/api/src/lib/embeddings.js`の`fetchEmbeddings(texts, { apiKey })` — クエリ文字列1件を`fetchEmbeddings([query], { apiKey })`で埋め込みベクトル化する（`buildEmbeddingText`はスキル側のフォーマットなのでクエリには使わない。クエリの生テキストをそのまま埋め込む）
- 読む: `tools/skill-search/src/index-store.mjs`（Step1で作成済み） — `readIndex()`の戻り値の形をそのまま使う

**CLIの引数・出力形式の慣習を合わせるため（優先度: 中）**

- 読む: `tools/cline-wrapper/repo-search.mjs`の引数パース部分（`--repo/-r`, `--model/-m`）と、進捗を標準エラー出力・最終結果を標準出力に分ける慣習
- 読む: `skills-site/api/src/lib/suggest-core.js`の埋め込みTop-10部分（LLM再ランク前まで） — 本CLIはLLM再ランクをしないが、Top-K取得までの流れは参考になる

## 触るファイル

### 新規

- `tools/skill-search/src/search.mjs` — `searchSkills(query, { topK = 10, indexPath, repoRoot, apiKey })`をexport。処理順序: `readIndex()` → 実体`SKILL.md`が存在しないエントリを除外（`fs.existsSync(path.join(repoRoot, skill.path))`、**Top-Kへ絞り込む前に**行う） → `fetchEmbeddings([query], { apiKey })` → `topKByEmbedding()` → スコア付きで返す。CLI引数パースを含まない、単体で呼べる関数にする（将来のエージェント向けツール化を見据えた決定、[00-overview.md](00-overview.md)参照）
- `tools/skill-search/AGENTS.md` — セットアップ（`skills-site/.env`の`OPENROUTER_API_KEY`が前提）、グローバル導入（`pnpm --filter skill-search link --global`または`npm link`。`tools/aim`の`uv tool install --editable`と同じ位置づけ）、`build-index`/`search`それぞれの実行例（リンク前は`pnpm --filter skill-search exec skill-search build-index`、リンク後は`skill-search search --query "..."`）、インデックスが手動更新である旨、鮮度のずれの扱い（実体が無いスキルは除外・description等の内容ズレは許容）を記載
- `tools/skill-search/CLAUDE.md` — `@./AGENTS.md`（既存パッケージ（`tools/cline-wrapper/CLAUDE.md`等）と同じ1行フォーマット）

### 変更

- `tools/skill-search/src/cli.mjs`（Step1で作成済み） — サブコマンド分岐に`search`を追加し、`--query/-q`（必須）、`--top/-k`（既定10）、`--json`（既定false、指定時はJSON配列をそのまま標準出力）を`node:util`の`parseArgs`で受けて`search.mjs`の`searchSkills()`を呼ぶ。既定は人間可読なテーブル形式（`path` / `name` / `score`）で標準出力へ表示する

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                         | 理由                                                                                                                                                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 実体`SKILL.md`が無いスキルの除外は、`topKByEmbedding`で絞り込む**前**の全件に対して行う                                                      | 絞り込んだ後に除外すると、上位K件の中に消えたスキルが混ざっていた場合、返る件数がKより少なくなってしまう。全件スキャンのコストは低い規模（現状90件、当面数百件）なので事前フィルタで問題ない                                                                                    |
| クエリの埋め込みには`buildEmbeddingText({ name, description })`を使わず、クエリ文字列をそのまま`fetchEmbeddings`に渡す                       | `buildEmbeddingText`はスキル側（`name`+`description`）の埋め込みフォーマットを揃えるためのものであり、自由文のクエリに同じ整形をかける意味がない。`skills-site/api/src/lib/suggest-core.js`でもクエリは生テキストのまま埋め込んでいるはずなので、そこでの扱いを確認して合わせる |
| 出力は既定でテーブル形式、`--json`指定時のみJSON配列                                                                                         | 人間が直接叩く用途を優先しつつ、将来スクリプトや別ツールから呼ぶ場合に備えて機械可読な出力も最初から用意しておく（軽い先取り、過剰設計にはならない範囲）                                                                                                                        |
| `cli.mjs`の`search`サブコマンドはエラー（インデックス未生成、APIキー未設定等）をわかりやすいメッセージで標準エラー出力に出し、非ゼロ終了する | `tools/skill-search/data/skill-index.json`が存在しない場合に「先に`skill-search build-index`を実行してください」等、次にすべき操作がわかるメッセージにする                                                                                                                      |
| `AGENTS.md`には`pnpm link --global`だけでなく、リンクせずに使う方法（`pnpm --filter skill-search exec skill-search ...`）も併記する          | CI/一時的な確認ではグローバルリンクが不要・むしろ避けたい場合がある。Step1の動作確認でも後者の形を使っている（[01-index-build.md](01-index-build.md)参照）                                                                                                                      |

## ルール更新ポイント

このリポジトリでは`.claude/rules`は使わず`AGENTS.md`でルール管理する（[.claude/plans/AGENTS.md](../AGENTS.md)参照）。今回追加する`tools/skill-search/AGENTS.md`は新規パッケージ単位のドキュメントであり、既存の共通ルールファイル（ルート`AGENTS.md`等）への追記は[00-overview.md](00-overview.md)の「ルール更新ポイント」で不要と判断済み。

新規`tools/skill-search/CLAUDE.md`のフロントマターは不要（`tools/cline-wrapper/CLAUDE.md`と同じ`@./AGENTS.md`の1行のみのファイルであり、`paths:`等のフロントマター方式ではない）。

## 推奨の進め方

- **実行主体**: メインエージェント。`search.mjs`は関数シグネチャ（将来の再利用を見据えた形）の設計判断を伴うため、サブエージェントへの委譲はしない。
- **TODO化**: 「`search.mjs`（ロジック）」→「`cli.mjs`に`search`サブコマンドを追加」→「実際に`pnpm --filter skill-search exec skill-search search --query "..."`を実行して結果が返ることを確認」→「`pnpm --filter skill-search link --global`でグローバルリンクし、`skill-search search --query "..."`だけで呼べることを確認」→「`AGENTS.md`/`CLAUDE.md`作成」の5項目程度に分けてTODO化する。
- **関連スキル**: 特になし。

---

## 動作確認

Step1で`skill-index.json`を生成済みの前提で、以下を実行し、関連するスキルがスコア付きで上位に表示されることを確認する。存在しないスキルパスを一時的にインデックスへ混ぜて、検索結果から除外されることも確認する。

```powershell
pnpm --filter skill-search exec skill-search search --query "ローカルでベクトル検索したい"
pnpm --filter skill-search exec skill-search search --query "ローカルでベクトル検索したい" --json
```

グローバルリンクの動作確認（`bin`登録の本来の目的）:

```powershell
pnpm --filter skill-search link --global
skill-search search --query "ローカルでベクトル検索したい"
```

## 計画との差分

[01-index-build.md](01-index-build.md)の差分どおり`pnpm link --global`はpnpm 11で廃止されているため、動作確認は`cd tools/skill-search && pnpm add -g .`（`pnpm --filter skill-search add -g .`は不可。`--filter`と`add -g`の組み合わせは対象パッケージ配下へ実際にはリンクされず無反応になる）で行った。確認後`pnpm remove -g skill-search`で元に戻した。`AGENTS.md`のグローバル導入手順には`cd tools/skill-search && pnpm add -g .`を明記済み。

`topKByEmbedding`（`skills-site/api/src/lib/embedding-similarity.js`）はスコアを返さず`skill`のみを返す仕様のため、`search.mjs`では同関数を呼ばず`cosineSimilarity`を直接使って同等のフィルタ・ソート・Top-K切り出しを実装し、各結果に`score`を付与した。
