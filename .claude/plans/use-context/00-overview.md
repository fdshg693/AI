# use-context スキル（Context7連携） 実装プラン - 概要

## 要件

- 外部ライブラリ・フレームワークの最新API・設定・コード例をContext7から取得するClaude Codeスキル`use-context`を作る。
- Context7へのアクセスはMCP経由でクライアントに直接晒さず、CLI経由に寄せる。理由: MCP接続だとできない柔軟なカスタマイズ（クエリ整形、出力形式、jq等の後段CLIへのパイプ等）がこのスキルの目的だから。
- CLI本体はPythonで実装し、`ms-learn`（`tools/mslearn`）・`tav-cli`（`tools/tav-cli`）と同じ構成で、スキルから分離して`tools/`配下に置く。スキル側はCLIのインストール済みを前提とし、インストール処理は行わない。
- スキル本体は「Context7をいつ使うか」「クエリの作り方」「`ms-learn`との使い分け」「長い調査のコンテキスト分離」等の判断を扱い、Context7利用に関する既存調査メモ（[memo/](../../../claude-plugins/my-tools/skills/use-context/memo/)配下）の内容を土台にする。

## 実装ステップ

1. [01-research.md](01-research.md) — Context7のAPI仕様の事前調査（MCPを使わないREST直叩きが可能か、不可能ならMCPクライアントとしての実装方式）
2. [02-implement-cli.md](02-implement-cli.md) — `tools/ctx7` Python CLI実装
3. [03-implement-skill.md](03-implement-skill.md) — `use-context`スキル本体（SKILL.md）の作成・README.md更新

## 主要な決定事項

| 決定                                                                                                                                                             | 理由                                                                                                                                                                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CLI本体は`tools/ctx7`に新規Pythonパッケージとして配置し、`uv tool install --editable tools/ctx7`でインストールする運用にする                                     | `mslearn`・`tav`と同じ導入パターンに揃え、リポジトリ内のCLIツール一式の運用方法を一貫させるため                                                                                                                                                                                                                                                           |
| CLIはMCPを使わず、Context7公式REST API（`GET /api/v2/libs/search`, `GET /api/v2/context`）を`requests`で直叩きする（[01-research.md](01-research.md)で確定）     | Context7が`https://context7.com/api/v2/...`配下に素のREST APIを公開していることが判明したため。公式Python SDKは無く（TypeScript SDKのみ）、公式ドキュメントのサンプルコードも`requests`を使用している。`fastmcp`依存は不要になり、`tools/mslearn`より`tools/tav-cli`（APIを直接叩きAPIキー・出力先を`*_core/environment.py`で管理する型）に近い構成になる |
| スキル自体はCLI未インストール時のエラーに対処せず、`tools/ctx7/README.md`のセットアップ手順をユーザーに案内するだけにする                                        | `ms-learn`・`tav-cli`と同じ責務分離（前提条件の充足はスキルの責務外）                                                                                                                                                                                                                                                                                     |
| 公式Context7 MCPプラグイン・`docs-researcher`エージェント・`/context7:docs`コマンドとは独立に位置づけ、二重発火を避ける発火条件をSKILL.mdのdescriptionに明記する | 公式プラグインが導入済みの環境と併用される可能性があるため（[03-skill-design.md](../../../claude-plugins/my-tools/skills/use-context/memo/03-skill-design.md)の「公式スキルとの差分」節を踏襲）                                                                                                                                                           |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照）

### 新規

- `tools/ctx7/`（`pyproject.toml`, `ctx7_cli.py`, `ctx7_core/`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`）
- `claude-plugins/my-tools/skills/use-context/SKILL.md`

### 変更

- `claude-plugins/my-tools/skills/use-context/README.md`
- `pyproject.toml`（リポジトリルート、`[tool.uv.workspace] members`に`tools/ctx7`を追加）

## `.claude/rules` 更新ポイント

- 新規ルールファイルの作成・既存ルールファイルの変更は無し。`.claude/rules/ai-tools-config.md`は`claude-plugins/my-tools`が既に登録済みのプラグインルート（`skills_layout: subdir`）であるため新規スキル追加だけでは`ai-tools.yaml`の変更が不要、`.claude/rules/skill-meta-fields.md`は`paths: ["meta_field.yaml", "**/SKILL.md"]`で既に新規`SKILL.md`もカバーしている。詳細な確認はStep2・Step3で行う。

---

## 書き方のポイント

このプランは[.claude/plans/references/](../references/)のフォーマットに従う。実装詳細（コードスニペット、具体的な関数シグネチャ等）は書かず、後続ステップおよび実装時に既存の`tools/mslearn`・`tools/tav-cli`を参照して導出する。
