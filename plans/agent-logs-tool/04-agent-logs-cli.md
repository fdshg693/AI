---
type: Plan Step
status: planning-breakdown
---

# Step 4: agent-logs CLI の実装

> [03-knowledge-skills-log-specs.md](03-knowledge-skills-log-specs.md) の続き。ログ形式の前提は Step2 の調査結果と Step3 の知識スキルに従う。

## やること

`agent-compat/logs/agent-logs/` に Python（uv）の CLI `agent-logs` を作る。ツールごとのアダプタがローカルログを読み、共通スキーマに正規化し、横断で一覧・検索・集計する。v1 のサブコマンド:

- `sources` — 対象ツールごとの検出結果（ログの場所・有無・件数・最終更新）
- `sessions` — セッション一覧（ツール・プロジェクト/cwd・開始/終了・メッセージ数・モデル）
- `show <session>` — 1 セッションの正規化イベント列
- `search <query>` — 本文・ツール呼び出しの横断検索（正規表現可）
- `stats` — 集計（期間・ツール・プロジェクト・モデル・ツール呼び出し名別の件数、取れる場合はトークン）

共通フィルタ: `--tool`・`--since/--until`・`--project`・`--role`。出力は人間向けの表と `--json`（一覧系は NDJSON）。

## 読むべきファイル・実行推奨Grep

**既存パッケージの型（優先度: 高）**

- 読む: `agent-compat/hooks/agent-tooling/pyproject.toml`・`README.md`・`justfile`・`agent_tooling/sessions_cli.py` — 同じサブモジュールの CLI の作り（argparse、`--json`、`--watch` の出し分け、依存ゼロ方針）
- 読む: `agent-compat/hooks/agent-tooling/agent_tooling/core/fs_links.py` — Junction を辿らない走査（`is_link_like`）。パッケージ内に同じ関数を持つ方針
- 読む: Step3 で作った各 `<tool>-logs` スキルと `claude-logs-investigate/log-format.md` — アダプタの仕様

**似た既存ツール（優先度: 中）**

- 読む: `tools/coding-agent/ai-usage/ai_usage_core/` — ツールごとのコレクタを try/except で分離する構成
- 読む: `tools/skill-tools/` の README・`pyproject.toml` — `uv tool install --editable` 前提の配布

**登録・検査（優先度: 中）**

- 読む: `pyproject.toml`（ルートの uv workspace members）・`maintenance/docs/justfile-conventions.md`

## 触るファイル

### 新規

- `agent-compat/logs/README.md` — `logs/` の案内
- `agent-compat/logs/agent-logs/pyproject.toml` — パッケージ `agent-logs`、エントリ `agent-logs = agent_logs.cli:main`、実行時依存なし（dev に pytest）
- `agent-compat/logs/agent-logs/agent_logs/cli.py` — サブコマンドと出力整形
- `agent-compat/logs/agent-logs/agent_logs/model.py` — 正規化スキーマ（Session・Event）
- `agent-compat/logs/agent-logs/agent_logs/adapters/{claude,cursor,cline,kilo,antigravity,codex}.py` — ツール別の検出と読み取り
- `agent-compat/logs/agent-logs/agent_logs/query.py`・`stats.py` — フィルタ・検索・集計
- `agent-compat/logs/agent-logs/tests/`＋`tests/fixtures/<tool>/` — 架空データのフィクスチャで各アダプタと集計を検証
- `agent-compat/logs/agent-logs/{README.md,AGENTS.md,CLAUDE.md,justfile}`

### 変更

- `pyproject.toml`（ルート）・`uv.lock` — workspace member に追加
- `agent-compat/README.md` — 中身に `logs/` を追加
- `agent-compat/.gitignore` — 先頭 `/` の無い `logs/`・`*.sqlite3`・`*.log` が `logs/agent-logs/` 一式とフィクスチャを無視する。`/logs/*.log` 等に絞るか否定パターンを足す（`git check-ignore` で確認）

## 決定事項・注意点／落とし穴

| 決定・注意                                                                                                                                     | 理由                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| アダプタは共通インターフェース（`detect()`・`iter_sessions(filters)`・`iter_events(session)`）を実装し、1 アダプタの失敗は警告にして他を続ける | ログ形式は非公開で壊れやすい。ai-usage と同じ分離方針             |
| ルートはツールごとの環境変数（`AGENT_LOGS_<TOOL>_DIR`）で上書きでき、既定は Windows/POSIX の両方を持つ                                         | テスト・別マシン・Codex（実データ無し）のフィクスチャ検証に必要   |
| SQLite は `file:...?mode=ro` の URI で開く。ロックで開けなければ一時ディレクトリへコピーして読む（元ファイルは触らない）                       | 実行中のツールの WAL DB を壊さない                                |
| v1 はインデックスを持たず、`--since` をファイル mtime の前段フィルタにも使って走査量を減らす                                                   | 正しさ優先。遅ければ後でキャッシュ（`~/.cache/agent-logs`）を足す |
| 正規化できないレコードは `kind: "raw"` で残し、`show --raw` で元 JSON を見せる                                                                 | 未知のレコード種別を捨てずに調査できる                            |
| `search` の出力は既定で前後を切り詰め、全文は `show` で見る                                                                                    | ログに秘密情報・巨大なツール出力が入る                            |
| フィクスチャに実ログを使わない（架空値で作る）。AGENTS.md に明記                                                                               | サブモジュールは公開リポジトリ                                    |
| SQLite フィクスチャはバイナリをコミットせず、テスト時に SQL から作る                                                                           | `.gitignore` の `*.sqlite3` に掛からず、差分もレビューできる      |
| Antigravity の本文が平文で読めない場合、v1 はセッションのメタデータ（所在・時刻・件数）だけを返し、`sources` にその旨を出す                    | 非公開バイナリ形式の解析は採用しない（ai-usage の方針と同じ）     |
| SQLite フィクスチャはバイナリをコミットせず、テスト時に SQL から作る                                                                           | `.gitignore` の `*.sqlite3` に掛からず、差分もレビューできる      |
| パッケージ内で Junction・symlink を辿らない                                                                                                    | [repo-layout](../../maintenance/docs/repo-layout.md) の走査規約   |

## ルール更新ポイント

- `agent-compat/logs/agent-logs/AGENTS.md`（新規）: アダプタ追加手順（知識スキル→アダプタ→フィクスチャ→テストの順）、読み取り専用・外部送信禁止、フィクスチャに実ログを入れない、仕様の正本は知識スキル
- `agent-compat/AGENTS.md`「このフォルダの責務」に `logs/` を追記（Step1 で枠を作っていれば中身だけ）

## 進め方

- **実行主体**: メインエージェント。共通スキーマと CLI 骨格を先に作り、アダプタはツールごとにサブエージェントへ並列委任してよい（各アダプタは対応する知識スキルとフィクスチャだけを入力にする）。
- **TODO化**: (1) スキーマ・CLI 骨格・`sources`、(2) Claude アダプタ＋`sessions`/`show`、(3) 残り 5 アダプタ（1 つ 1 項目）、(4) `search`・`stats`、(5) README・AGENTS.md・workspace 登録。各項目で `just --justfile agent-compat/logs/agent-logs/justfile test` を通し、実機で `agent-logs sources` の結果を目視確認する。
