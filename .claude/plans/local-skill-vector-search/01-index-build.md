---
type: Plan Step
status: implementing-done
---

# Step 1: パッケージ雛形 + インデックス構築コマンド（`build-index`）

## やること

`tools/skill-search/`を新規pnpmパッケージとして作成し、`skills-site`の`discoverSkills()`・`attachSkillEmbeddings()`を相対importで呼び出して、埋め込みベクトル入りのローカルインデックスJSON（`tools/skill-search/data/skill-index.json`）を書き出す`build-index`サブコマンドを実装する。あわせて`package.json`に`bin`（`skill-search`コマンド）を登録し、`src/cli.mjs`をサブコマンドディスパッチャの起点として作る（Step2で`search`サブコマンドを追加する前提の土台）。

## 読むべきファイル・実行推奨Grep

**参照する既存モジュールのシグネチャ・再利用パターンを正確に把握するため（優先度: 高）**

- 読む: `skills-site/scripts/publication-core.mjs`の`discoverSkills({ repoRoot, registry, overrides })` — 引数の形（`registry`は配列、`overrides`は`{ excludeSources, excludeSkills }`）と戻り値（`skills`配列、各要素の`path`/`name`/`description`/`tool`/`plugin`/`status`）
- 読む: `skills-site/scripts/source-registry.mjs`の`SOURCE_REGISTRY`、`skills-site/scripts/site-overrides.mjs`の`SITE_OVERRIDES` — `discoverSkills()`にそのまま渡す定数
- 読む: `skills-site/scripts/build-skill-embeddings.mjs`の`attachSkillEmbeddings()`・`loadPreviousAiIndex()`・`loadLocalEnv()`・`AI_INDEX_SCHEMA_VERSION` — 差分更新（content-hash再利用）ロジックをそのまま流用する箇所。`attachSkillEmbeddings(skills, { apiKey, previousIndex, fetchImpl, fetchEmbeddingsFn })`の戻り値は`path`/`name`/`description`/`tool`/`plugin`/`status.key`/`embedding`/`embeddingHash`を持つ配列
- 読む: `skills-site/scripts/build-catalog.mjs`（冒頭〜`attachSkillEmbeddings`呼び出し周辺） — 上記3モジュールを実際にどう組み合わせているかの実例。`build-index.mjs`はこれの縮小版になる

**新規パッケージのレイアウト・慣習を合わせるため（優先度: 中）**

- 読む: `tools/cline-wrapper/package.json`・`tools/cline-wrapper/AGENTS.md` — 引数パース・`.env`読み込みの案内文の書き方（呼び出し形式は`pnpm run`だが、それ以外の書き方の作法は参考にする）
- 読む: `pnpm-workspace.yaml` — `packages`リストへの追記位置
- 参考: `tools/aim`のセットアップ手順（`uv tool install --editable`でグローバルにエディタブルインストールし、以降`aim`とだけ打てば呼べる） — 今回`skill-search`の`bin`登録＋`pnpm link --global`で目指す体験のNode版の対応物

## 触るファイル

### 新規

- `tools/skill-search/package.json` — `name: "skill-search"`, `private: true`, `type: "module"`, `engines.node >= 20`（`ai-skill-catalog-api`に合わせる）, `bin: { "skill-search": "src/cli.mjs" }`
- `tools/skill-search/src/cli.mjs` — `bin`エントリポイント（`#!/usr/bin/env node`シェバン付き）。第1引数をサブコマンド名として読み、このステップでは`build-index`のみをディスパッチする（未知のサブコマンドはエラーメッセージ＋非ゼロ終了）。`node:util`の`parseArgs`でサブコマンドごとの引数を受け、`loadLocalEnv()`を呼んでから対応するロジック関数を実行する
- `tools/skill-search/src/build-index.mjs` — 純粋なロジック本体。`discoverSkills()` → 既存インデックス読み込み（`loadPreviousAiIndex`相当、パスは`tools/skill-search/data/skill-index.json`） → `attachSkillEmbeddings()` → スキーマ情報を付けて返す、を行う関数をexport（`cli.mjs`から呼ばれるほか、Step2以降で他コードから直接importされることも想定した独立関数にする）
- `tools/skill-search/src/index-store.mjs` — `tools/skill-search/data/skill-index.json`の読み書きだけを担う小さいモジュール（`readIndex()`/`writeIndex()`）。Step2の`search.mjs`からも読み込み用に再利用する
- `tools/skill-search/.gitignore` — `data/`をgitignore対象にする（ルート`.gitignore`への追記でもよいが、ツール固有なのでパッケージ内に閉じた方が見つけやすい）

### 変更

- `pnpm-workspace.yaml` — `packages`に`"tools/skill-search"`を追加

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                       | 理由                                                                                                                                                                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `discoverSkills`/`attachSkillEmbeddings`等は相対パスで直接import（例: `../../../skills-site/scripts/build-skill-embeddings.mjs`）                          | [00-overview.md](00-overview.md)の決定事項どおり。`skills-site/scripts/build-skill-embeddings.mjs`自身が`../api/src/lib/embeddings.js`を同じ流儀で相対importしている前例に合わせる                                                                          |
| importされる側のファイル（`build-skill-embeddings.mjs`等）が使う`js-yaml`等の依存は`tools/skill-search/package.json`に追加しない                           | Nodeのbare specifier解決は「importする側のファイル自身の位置」基準で行われるため、`skills-site/scripts/`配下のファイルが使う依存は`skills-site`側の`node_modules`から解決される。呼び出し元パッケージでの再宣言は不要（かつ二重管理を避けられる）           |
| インデックスの保存先は`skills-site/api/data/ai-index.json`とは別に`tools/skill-search/data/skill-index.json`を新設する（既存ファイルを流用・上書きしない） | スキーマの意味と生成元パイプラインが別物（`ai-index.json`はサイトのビルド成果物で`catalog:build`が所有）。同じファイルを2つのツールが書き換えると競合・混乱の元になる                                                                                       |
| 差分更新（content-hash再利用）は`attachSkillEmbeddings`にそのまま任せる。CLI側で独自の再利用ロジックは書かない                                             | ラフプラン決定事項どおり、既存の差分更新パターンは「明示的な再構築コマンドの内部実装」としてのみ流用する（自動検知トリガーは追加しない）                                                                                                                    |
| `cli.mjs`は最初から「サブコマンド名で分岐する`bin`エントリポイント」として作り、`build-index-cli.mjs`のような単独スクリプトにはしない                      | Step2で`search`サブコマンドを追加する際に構造を作り直さずに済む。単一`skill-search`コマンドの下にサブコマンドを生やす形は、後から`bin`を導入し直すより最初から一枚岩にした方がシンプル                                                                      |
| `src/cli.mjs`には`#!/usr/bin/env node`シェバンを付け、実行属性（`chmod +x`）も設定する                                                                     | POSIX環境（Mac/Linux/WSL）で`pnpm link --global`後にシェバン無し・実行属性無しだと直接起動できない。Windows上のpnpm/npmはシェバンに依らないシム（`.cmd`等）を生成するため今回の開発環境では影響が出にくいが、クロスプラットフォームの正しさとして付けておく |
| CLI引数パースは`node:util`の`parseArgs`を使い、新規npm依存（yargs/commander等）は追加しない                                                                | 現時点でサブコマンドは`build-index`と`search`の2つのみで複雑なパース要件が無く、依存を増やすほどの規模ではない（YAGNI）                                                                                                                                     |

## ルール更新ポイント

このステップでは`AGENTS.md`本文の作成はしない（ツール専用ドキュメントはStep2でまとめて作成する。Step1完了時点ではまだ`search`コマンドが無く、片方だけのドキュメントは書きかけになるため）。

## 推奨の進め方

- **実行主体**: メインエージェント。既存モジュールのシグネチャを正確に踏襲する必要があり、分割してもレビューコストが増えるだけの規模。
- **TODO化**: 「パッケージ雛形+`pnpm-workspace.yaml`更新」→「`build-index.mjs`（ロジック）+`index-store.mjs`」→「`bin`登録+`cli.mjs`（`build-index`サブコマンドのディスパッチ）」→「実際に`pnpm --filter skill-search exec skill-search build-index`を実行して`skill-index.json`が生成されることを確認」の4項目程度に分けてTODO化する。
- **関連スキル**: 特になし。既存コードの移植・薄いラップが中心のため。

---

## 動作確認

実装後、`OPENROUTER_API_KEY`が`skills-site/.env`に設定された状態で以下を実行し、`tools/skill-search/data/skill-index.json`が生成され、スキル件数・`embeddingModel`等が想定どおりであることを確認する（この時点では`pnpm link --global`はまだ行わず、`pnpm exec`経由で`bin`が正しく解決されることだけを確認する）。

```powershell
pnpm install
pnpm --filter skill-search exec skill-search build-index
```

## 計画との差分

`pnpm --filter skill-search exec skill-search build-index` は動作しない（依存関係が0件のワークスペースパッケージは、pnpm 11でも自パッケージの`bin`が`node_modules/.bin`へ自己リンクされないため。`pnpm link --global`もpnpm 11で廃止され`pnpm add -g .`に置き換わっている）。動作確認は代わりに`pnpm add -g .`でグローバル登録した状態の`skill-search build-index`、または`pnpm --filter skill-search exec node src/cli.mjs build-index`で行い、確認後`pnpm remove -g skill-search`で元に戻した。`data/skill-index.json`が92件のスキル・想定`embeddingModel`で生成されることを確認済み。Step2でのドキュメント整備時、セットアップ手順に`pnpm add -g .`を明記すること。
