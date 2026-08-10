---
type: Plan
status: implementing-done
---

# ローカルスキル・ベクトル検索CLI 実装プラン - 概要

> ラフプラン: [rough/01-approach.md](rough/01-approach.md)（調査結果・決定事項の経緯はこちら）

## 要件

- `skills-site`の「AIにスキルを提案してもらう」機能（埋め込みベクトルのコサイン類似度でTop-K検索）と同じ仕組みを、ローカルCLIから使えるようにする。
- LLMによる再ランク・理由文生成はしない。コサイン類似度Top-Nをそのまま一覧表示するだけ。
- DBは導入しない。埋め込みを含むローカルインデックスは1本のJSONファイルに書き出し、インデックス更新は完全手動（自動差分検知はしない）。

## 実装ステップ

1. ✅ [01-index-build.md](01-index-build.md) — パッケージ雛形 + インデックス構築コマンド（`build-index`）
2. ✅ [02-search-and-docs.md](02-search-and-docs.md) — 検索コマンド（`search`）+ ドキュメント整備

## 主要な決定事項

| 決定                                                                                                                                  | 理由                                                                                                                                                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools/skill-search/`を新規pnpmパッケージとして追加する                                                                               | `pnpm-workspace.yaml`は既に`skills-site`と`skills-site/api`を別パッケージとして管理しており、同じ構成に合わせるのが自然                                                                                                                                                                                 |
| `skills-site/scripts/*.mjs`・`skills-site/api/src/lib/*.js`は相対パスで直接importする（`exports`整備や`workspace:*`依存は増やさない） | `skills-site/scripts/build-skill-embeddings.mjs`が既に`../api/src/lib/embeddings.js`をパッケージ境界を越えて相対importしており（`skills-site/package.json`に依存宣言は無い）、これが本レポジトリの既存パターンだったため合わせる。詳細: [rough/01-approach.md](rough/01-approach.md)                    |
| カタログは`skills-site/generated/catalog.json`を経由せず、`discoverSkills()`を`SOURCE_REGISTRY`/`SITE_OVERRIDES`と共に直接呼ぶ        | `pnpm run catalog:build`の事前実行に依存させず、CLI単体で完結させるため                                                                                                                                                                                                                                 |
| `OPENROUTER_API_KEY`は新規`.env`を増やさず`build-skill-embeddings.mjs`の`loadLocalEnv()`（`skills-site/.env`を解決）をそのまま使う    | 鍵管理箇所を増やさない。この関数はファイル自身の位置基準でパスを解決するため、呼び出し元の位置に依存せず動く                                                                                                                                                                                            |
| インデックスJSON（`tools/skill-search/data/skill-index.json`）はgitignore対象                                                         | `skills-site/api/data/ai-index.json`と同様、埋め込みベクトルを含むビルド成果物であり、手動再構築のたびに変わるため                                                                                                                                                                                      |
| 検索結果は、ローカルインデックスにあるが実体`SKILL.md`が既に無いスキルを候補から除外する（description等の内容ズレは許容）             | ラフプラン時点の決定。パス実在チェックはコストが低く、消えたスキルを提示するのは実害が大きい一方、内容ズレの検知は手動再構築の運用と表裏一体で許容範囲                                                                                                                                                  |
| CLIは`package.json`の`bin`に単一コマンド`skill-search`を登録し、`build-index`/`search`はそのサブコマンドとしてディスパッチする        | ユーザーが簡略化した呼び出しを明示的に要望。`tools/aim`の`uv tool install --editable`と同様、`pnpm link --global`（または`npm link`）でグローバルにエディタブルインストールすれば以降`skill-search <subcommand> ...`とだけ打てる。本レポジトリのNode製CLIツールに前例は無いが、この機能で初めて導入する |
| 検索本体ロジック（`searchSkills()`）はCLI引数パースから独立した関数としてexportする                                                   | 今回はCLIのみがスコープだが、将来Claude Code自身がツールとして呼び出す場合に、サブプロセス起動でなく直接importできるようにしておく（拡張性のための軽い先取り）                                                                                                                                          |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `tools/skill-search/package.json`（`bin.skill-search`を含む）
- `tools/skill-search/src/cli.mjs` — `bin`エントリポイント。サブコマンドディスパッチ（Step1で`build-index`、Step2で`search`を追加）
- `tools/skill-search/src/build-index.mjs`
- `tools/skill-search/src/index-store.mjs`
- `tools/skill-search/src/search.mjs`
- `tools/skill-search/AGENTS.md` / `CLAUDE.md`
- `tools/skill-search/.gitignore`（または該当エントリをルート`.gitignore`に追加）

### 変更

- `pnpm-workspace.yaml` — `packages`に`tools/skill-search`を追加

## ルール更新ポイント

このリポジトリでは`.claude/rules`は使わず`AGENTS.md`でルール管理する（[.claude/plans/AGENTS.md](../AGENTS.md)参照）。

- `tools/skill-search/AGENTS.md`（新規作成）: このツール専用のセットアップ・使い方ドキュメント。Step2で作成（[02-search-and-docs.md](02-search-and-docs.md)参照）
- ルート`AGENTS.md`/`README.md`の更新は不要と判断: `README.md`の`tools/`一覧は`ctx7`/`mslearn`/`my-agents`/`schedule`/`tav-cli`等、既存の全サブフォルダを網羅していない（意図的に主要ツールのみの抜粋になっている）ため、`skill-search`も追記必須にはしない

## 推奨の進め方（概要ファイル）

- **TODO化**: ステップ一覧の2項目をそのままTODO化する。Step1（インデックス構築）が完了しないとStep2（検索）の動作確認ができないため、順序どおり進める。
- **実行主体**: 両ステップとも既存モジュールの参照方法（相対import、関数シグネチャ）の正確な把握が前提になるためメインエージェントで進める。サブエージェントへの分割が有効なほど独立した並行作業は無い規模。
- **関連スキル**: 新規ドキュメント作成時のフォーマットに迷ったら[writing-rules](../../skills/writing-rules/writing.md)を参照（ただし今回はルールファイルではなくツールREADME相当のため必須ではない）。
