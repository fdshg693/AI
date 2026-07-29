# Step 2: `tools/ctx7` Python CLI実装

> [01-research.md](01-research.md) の続き。Step1の調査結果（採用方式・エンドポイント・レート制限）を前提に実装する。

## やること

Step1で確定した接続方式（MCPクライアント経由 or REST直叩き）に基づき、`tools/ctx7`配下にContext7のドキュメント取得用Python CLI（`ctx7`コマンド）を実装する。ライブラリ解決（`resolve-library-id`相当）とドキュメント取得（`query-docs`相当）の2機能を最低限持たせ、`mslearn`・`tav`と同じ運用（`uv tool install --editable`、`--json`フラグ、終了コード設計）に揃える。

## 読むべきファイル・実行推奨Grep

**CLIパッケージのひな形として流用するため（優先度: 高）**

- 読む: `tools/mslearn/pyproject.toml` — パッケージ名、`[project.scripts]`（entry point）の書き方
- 読む: `tools/mslearn/mslearn_cli.py` — サブコマンド構成、`--json`/`--timeout`等の共通オプションの実装、`tools`/`call`のような汎用パススルーサブコマンドの要否
- 読む: `tools/mslearn/mslearn_core/output.py` — 結果をフォルダ+`index.md`へ書き出す設計（検索結果が長文になる場合に会話コンテキストを汚さないための出力契約）。Step1で確認した典型的な分量次第で、この設計を踏襲するか判断する

**依存関係・ワークスペース登録を確認するため（優先度: 中）**

- 読む: リポジトリルート`pyproject.toml`の`[tool.uv.workspace] members` — 新規メンバー追加箇所
- 読む: `tools/mslearn/.gitignore`, `tools/tav-cli/.gitignore` — `__pycache__`等の除外パターン
- 読む: `tools/tav-cli/.env.example` — APIキー等をリポジトリにコミットしない`.env`運用のサンプル

**Step1の調査結果を実装に反映するため（優先度: 高）**

- 読む: [01-research.md](01-research.md)の「調査結果として残すもの」— 採用方式、エンドポイント/認証、レート制限の扱い

## 触るファイル

### 新規

- `tools/ctx7/pyproject.toml` — パッケージ定義、entry point `ctx7`
- `tools/ctx7/ctx7_cli.py` — argparseベースのCLIエントリポイント（ライブラリ解決・ドキュメント取得のサブコマンド）
- `tools/ctx7/ctx7_core/__init__.py` / `client.py` / `config.py` / （必要なら）`output.py` — Step1で確定した接続方式のクライアント実装、環境変数の扱い、結果出力
- `tools/ctx7/README.md` — CLIのセットアップ手順・サブコマンド一覧・設計意図（人間のメンテナ向け）
- `tools/ctx7/AGENTS.md`, `tools/ctx7/CLAUDE.md` — `@./README.md`形式の委譲ファイル（`mslearn`・`tav-cli`に倣う）
- `tools/ctx7/.gitignore` — `__pycache__`等除外

### 変更

- リポジトリルート`pyproject.toml` — `[tool.uv.workspace] members`に`tools/ctx7`を追加

## 決定事項・注意点／落とし穴

| 決定                                                                                                               | 理由                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| コマンド名は`ctx7`（公式Node製CLIと同名）にする                                                                    | ユーザー・エージェント双方が覚えやすく、`mslearn`/`tav`と同じ「ツール名の短縮形をそのままコマンド名にする」命名規則にも合う。ただし公式`npx ctx7`と同一環境で併用する運用は想定しない旨をREADMEに明記する（PATH上のコマンド名衝突を避けるため、公式Node CLIのグローバルインストールは行わない） |
| APIキーは環境変数（例: `CONTEXT7_API_KEY`）または`tools/ctx7/.env`で受け取り、リポジトリ・ログへ書き込まない       | `tav-cli`の`.env`運用パターンを踏襲。APIキー無しでも動作させ、有無でレート制限が変わることをREADMEに明記する                                                                                                                                                                                    |
| 結果の出力形式（terminalへ直接出力 vs フォルダ+`index.md`書き出し）はStep1で確認した典型的なレスポンス分量で決める | `ms-learn`/`tav-cli`が同じ理由（長文がメイン会話のコンテキストを汚す）で採用している設計を踏襲し、独自設計を増やさない                                                                                                                                                                          |
| テストは薄く済ませる（レスポンス整形などの純粋関数のみ、`mslearn`と同水準）                                        | CLI自体はネットワーク越しの薄いラッパーであり、`tav-cli`のような`experiments/`+`tests/`のフル構成は今回のスコープでは過剰。`mslearn`が同水準のテスト量で運用できている実績に揃える                                                                                                              |

## `.claude/rules` 更新ポイント

- 更新なし。`.claude/rules/ai-tools-config.md`（`ai-tools.yaml`経由のSSOT）は`claude-plugins/my-tools`が既に登録済みのプラグインルートであるため、新規スキル追加だけでは変更不要。`tools/ctx7`自体は`ai-tools.yaml`の管理対象（スキル/プラグインの所在）ではないため同様に変更不要。
