---
name: "tools/skill-search instructions"
description: "Instructions for files in tools/skill-search/"
applyTo: "tools/skill-search/**"
---

# skill-search — ローカルスキル・ベクトル検索CLI

`skills-site`の「AIにスキルを提案してもらう」機能（埋め込みベクトルのコサイン類似度によるTop-K検索）と同じ仕組みを、ローカルCLIから使えるようにしたツールです。LLMによる再ランク・理由文生成はせず、コサイン類似度Top-Nをそのまま一覧表示します。

- `src/cli.mjs` — `bin`エントリポイント。サブコマンド（`build-index` / `search`）をディスパッチする
- `src/build-index.mjs` — `skills-site`の`discoverSkills()`・`attachSkillEmbeddings()`を呼び出し、埋め込みベクトル入りのインデックスを構築するロジック
- `src/index-store.mjs` — インデックスJSONの読み書き（`readIndex()` / `writeIndex()`）
- `src/search.mjs` — `searchSkills(query, options)`をexport。CLI引数パースから独立しており、将来Claude Code自身がツールとして直接importすることも想定している

## セットアップ

`skills-site/.env`に`OPENROUTER_API_KEY`が設定済みであることが前提です（新規`.env`は増やさず、`skills-site`のビルド用APIキーをそのまま流用します）。未設定の場合はセットアップ手順を`skills-site/AGENTS.md`参照。

```powershell
pnpm install
```

## グローバル導入（任意）

`tools/aim`の`uv tool install --editable`と同じ位置づけで、以降`skill-search <subcommand> ...`とだけ打てるようにできます。グローバル登録します（`pnpm link --global`はpnpm 11で廃止され`pnpm add -g .`に置き換わっています）。

```powershell
cd tools/skill-search
pnpm add -g .
```

登録後はリポジトリ内のどこからでも`skill-search`コマンドが使えます（`repoRoot`はCLIのソースファイル位置基準で解決するため、実行時のカレントディレクトリに依存しません）。不要になったら解除します。

```powershell
pnpm remove -g skill-search
```

グローバル登録せずに使う場合（CI・一時的な確認など）は、リポジトリルートから`pnpm --filter skill-search exec`経由で呼びます。

```powershell
pnpm --filter skill-search exec node src/cli.mjs build-index
```

## 使い方

### インデックス構築（`build-index`）

`tools/skill-search/data/skill-index.json`に、登録済み全スキルの埋め込みベクトル入りインデックスを書き出します。完全手動更新です（スキルの追加・変更後は明示的に再実行してください。自動差分検知はありません）。差分更新（content-hashが一致するスキルは埋め込みを再計算しない）は`attachSkillEmbeddings`のロジックにより自動で行われます。

```powershell
skill-search build-index
# グローバル未登録の場合
pnpm --filter skill-search exec node src/cli.mjs build-index
```

### 検索（`search`）

クエリを埋め込みベクトル化し、インデックスとのコサイン類似度Top-Nを一覧表示します。

```powershell
skill-search search --query "ローカルでベクトル検索したい"
skill-search search --query "ローカルでベクトル検索したい" --top 5
skill-search search --query "ローカルでベクトル検索したい" --json
```

| オプション | 短縮形 | 必須 | 説明                                                                                        |
| ---------- | ------ | ---- | ------------------------------------------------------------------------------------------- |
| `--query`  | `-q`   | ○    | 検索クエリ文字列                                                                            |
| `--top`    | `-k`   | -    | 上位何件を表示するか（既定10）                                                              |
| `--json`   | -      | -    | 指定時はJSON配列を標準出力へ、未指定時は`score` / `path` / `name`のタブ区切りテーブルを表示 |

## インデックスの鮮度について

- `tools/skill-search/data/skill-index.json`はgitignore対象のビルド成果物で、手動再構築のたびに変わります。スキルを追加・削除・編集したら`skill-search build-index`を再実行してください。
- 検索時、インデックスに載っているが実体`SKILL.md`が既に無いスキル（削除・移動済み）はTop-K候補から除外されます（存在チェックのコストは低く、消えたスキルを提示する実害の方が大きいため）。
- 一方でdescription等の内容ズレ（インデックス構築後に`SKILL.md`を編集した場合）は検知しません。これは許容範囲としています（手動再構築の運用と表裏一体の判断）。

## エラー時の挙動

- インデックス未生成（`skill-index.json`が無い）の場合、「先に`skill-search build-index`を実行してください」という趣旨のメッセージを標準エラー出力に表示し、非ゼロ終了します。
- `OPENROUTER_API_KEY`未設定の場合も同様にエラーメッセージを表示し、非ゼロ終了します。
