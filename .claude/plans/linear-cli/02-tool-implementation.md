# Step 2: tools/linear-cli/ のCLI実装

> [01-research-linear-api.md](01-research-linear-api.md) の続き。Step1 の調査結果（クライアント方式・スキーマ・ページネーション・レート制限）を前提に実装する。

## やること

`tav` と同じ構成で `linear` コマンドを実装する。単一ディスパッチャ `linear_cli.py` が `linear <サブコマンド>` を各操作ラッパーへ委譲し、共通部分は `linear_core/` パッケージに持つ。

## 読むべきファイル・実行推奨Grep

**tav-cli の構成・client生成パターンを踏襲するため（優先度: 高）**

- 読む: `tools/tav-cli/tav_cli.py` — サブコマンド→ラッパーモジュールの薄いディスパッチ書き方、`SUBCOMMANDS` 表の持ち方
- 読む: `tools/tav-cli/tav_core/environment.py` — `.env` 読込・クライアント生成・環境変数トグルの出し分け（Linear版 client.py/environment.py の基準）
- 読む: `tools/tav-cli/tav_core/result_contract.py` — 戻り値契約（ExitCode/Envelope/OutputChannel）の持ち方
- 読む: `tools/tav-cli/tav_core/output.py` — JSON整形と唯一の出力シンク `emit()` の設計
- Grep: `requires-python` および `[project.scripts]` — tools 配下の pyproject.toml 共通形式を確認（uv tool install 前提のパッケージング）

**aim-ask のライブラリ直接import・薄いCLIパターンを参考にするため（優先度: 中）**

- 読む: `tools/aim-use/aim-ask/pyproject.toml` — workspace依存・console script定義の最小例
- 読む: `tools/aim-use/aim-ask/aim_ask/cli.py` — argparse/Typer のエントリポイント書き方

**規約・落とし穴を確認するため（優先度: 低）**

- 読む: `.claude/rules/cli-wrapper-tools.md` — このステップで新規作成する側。存在確認だけして無ければスキップ

## 触るファイル

### 新規

- `tools/linear-cli/pyproject.toml` — パッケージ定義 + `[project.scripts] linear = "linear_cli:main"`
- `tools/linear-cli/linear_cli.py` — サブコマンドを各操作ラッパーへ振り分ける薄いディスパッチャ（`tav_cli.py` 相当）
- `tools/linear-cli/linear_core/` — 共通実装パッケージ（`__init__.py` / `environment.py`[.env読込・APIキー] / `client.py`[Linear GraphQLクライアント生成] / `output.py`[JSON整形・`emit()`] / `result_contract.py`[戻り値契約]）。モジュール分割は tav_core を参考に実装時に導出
- `tools/linear-cli/<操作ラッパー>.py` — 各操作（例: `issues.py`=list/get/create/update, `teams.py`, `labels.py`, `comments.py`, `search.py`）。サブコマンド対応表は実装時に確定
- `tools/linear-cli/README.md` — Pythonコードの説明・インストール・`.env`手順（tav-cli README.md 相当）
- `tools/linear-cli/AGENTS.md` / `tools/linear-cli/CLAUDE.md` — `@./README.md` でエージェント向け入口
- `tools/linear-cli/.env.example` — `LIN_API_KEY=` のテンプレ（`.env` は gitignore）
- `tools/linear-cli/.gitignore` — `.env` / `__pycache__` 等
- `tools/linear-cli/tests/` — オフライン構造検証 + モック応答テスト（tav-cli tests/ 相当）
- `.claude/rules/cli-wrapper-tools.md` — 外部APIラッパーCLIツール共通規約（新規ルールファイル）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                      | 理由                                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| 共通coreは `linear_core/` に集約し、各操作ラッパーはトップレベルのまま `linear_cli.py` が importlib でディスパッチ        | tav-cli と同じく `python tools/linear-cli/<script>.py` 直接実行とディスパッチ両立のため。core のモジュール分割は tav_core を参考に実装時に導出 |
| クライアント生成（Step1 の調査方式に従う）を `linear_core/client.py` に閉じ込め、ラッパーから直接 HTTP/GraphQL を叩かない | API仕様変更・テスト時のモック差替の影響範囲を core に限定する（tav_core と同様の境界）                                                         |
| 認証キーは `LIN_API_KEY`（環境変数 or `tools/linear-cli/.env`）                                                           | tav-cli の `TAVILY_API_KEY` と同じ1キー運用。`environment.py` で読込                                                                           |
| 出力はデフォルト JSON to stdout、`--format table\|markdown` で切替                                                        | パイプ/API連携の既定。tav-cli の ResultEnvelope 思想に準じる                                                                                   |
| 一覧系は `--limit`（既定20等）+ cursor ページネーションをラッパー内で隠蔽                                                 | Step1 の調査結果の Relay 形式をそのまま露出させない。`--all` で全件取得も可                                                                    |

## 注意点・落とし穴

- Linear API のレート制限（Step1 で確定）を超えると 429 が返る。CLI 側で自動バックオフ要否は Step1 の結果次第だが、最低限 429 は人間に分かるエラーとして扱う（黙って失敗しない）。
- GraphQL のレスポンスエラーは HTTP 200 で `errors` 配列が返ることがある。ステータスコードだけで成否判定しない（tav-cli zipcloud 相当の落とし穴）。
- 認証エラー（401/invalid key）とレート制限（429）と APIエラー（`errors`）を明確に区別した終了コードにする（`result_contract.py` で定義）。
- 破壊的操作（create/update/delete）は `--dry-run` または確認プロンプトを置くか、デフォルト非破壊で `--yes` で確定とする。設計は実装時に tav-cli に倣って導出。
- 個人APIキーは `.env` に書かせ、ソース・ログへ出さない（tav-cli と同じ）。

## `.claude/rules` 更新ポイント

新規ルールファイル `.claude/rules/cli-wrapper-tools.md` を作成する（既存ルールに外部APIラッパーCLIツールの共通規約が無いため）。フロントマターで対象パスを列挙:

```markdown
---
paths:
  - "tools/tav-cli/**/*.py"
  - "tools/linear-cli/**/*.py"
  - "tools/aim-use/**/*.py"
---

## 外部APIラッパーCLIツール規約

- 単一の consoleコマンド + サブコマンドで構成し、`linear_cli.py`/`tav_cli.py` のような薄いディスパッチャが各ラッパーへ委譲する。
- 共通実装（client生成/.env読込/出力/戻り値契約）は `<tool>_core/` パッケージに集約し、ラッパーから直接外部APIを叩かない。
- APIキーは `.env`（環境変数優先）で扱い、ソース・ログへ出さない。
- 出力はデフォルト JSON to stdout、format切替で人間向け。GraphQL/REST問わず、HTTPステータスだけでなくレスポンスbody（`errors`/`results`）で成否判定する。
- 破壊的操作はデフォルト非破壊（dry-run/確認）とし、明示フラグで確定する。
- ツール本体（`tools/<tool>/README.md`）は Python実装説明、AI 判断フローは `claude-plugins/my-tools/skills/<tool>/SKILL.md` に分離する。スキルから Python スクリプトを直接叩かない。
```

---

## 書き方のポイント

- **「読むべきファイル・推奨Grep」はファイルパスを並べるだけにしない。** 「何を確認するために読むのか」でグルーピングし、優先度（高/中/低）を明示する。
- **新規ルールファイルを作る場合はフロントマターまでプランに書く。** 対象パス（`paths:`）を決めるのは設計判断そのもの。本文は要点のみ。
- 決定事項の理由には Step1 の調査結果を根拠として引用してよい（リンクで参照）。
