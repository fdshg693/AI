---
type: Plan Step
status: planning-breakdown
---

# Step 6: codex-wrapper — `MODEL` 直書きを `config.toml` へ

## やること

`main.py` の `MODEL = "gpt-5.6-luna"` と argparse の説明文に埋まったモデル名を削除し、`codex-wrapper/config.toml` のカタログから読む。Step 1 で分かった上限を付け、スレッド ID・使用量をログに出す。

## 読むべきファイル・実行推奨Grep

**現行の呼び出しを確認するため（優先度: 高）**

- 読む: `workflow/codex-wrapper/main.py`、`workflow/codex-wrapper/AGENTS.md`（実行方法が `pip` + `python` のまま）
- 読む: Step 1 の調査結果（Codex SDK のタイムアウト・使用量）

**写し元（優先度: 高）**

- 読む: Step 2 の `workflow/claude-wrapper/util/config.py`

## 触るファイル

### 新規

- `workflow/codex-wrapper/config.example.toml` — `[models]`（`id = "gpt-5.6-luna"` を 1 件、default）、`[limits]`
- `workflow/codex-wrapper/codex_config.py` — 読み込み・検証（モジュール名は概要の決定事項にそろえる）
- `workflow/codex-wrapper/test_codex_config.py` — 見本が通ること・検証エラー。標準ライブラリだけで書き、`python3 -m unittest test_codex_config`（codex-wrapper 内で実行）で動くようにする

### 変更

- `workflow/codex-wrapper/main.py` — `--model`（エイリアス）を追加し、カタログ経由で `thread_start(model=...)` へ。上限・ログ
- `workflow/codex-wrapper/AGENTS.md` — セットアップに `cp config.example.toml config.toml`

## 決定事項・注意点／落とし穴

| 決定 | 理由 |
| --- | --- |
| `pyproject.toml` の新設・アンブレラ workspace への登録は本プランの対象外 | 規約が求めるのは設定の一元化で、パッケージ化は別件。`tomllib` は標準ライブラリなので依存追加は不要 |
| `sandbox=Sandbox.read_only` は変えない | 規約 §4 に沿っている |

- 落とし穴: `tomllib` は Python 3.11+。`pyproject.toml` が無いので `requires-python` で守れない。AGENTS.md に必要バージョンを書く。
- 落とし穴: `cwd` が `parents[2]`（アンブレラ全体）になっている。規約 §4「リポジトリ全体を渡さない」に触れるが read-only なので今回は変えず、Step 9 で移行表に残す。

## ルール更新ポイント

- `workflow/codex-wrapper/AGENTS.md`: セットアップ手順と Python 3.11+ の注記。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 1 項目（1 コミット）。`workflow/codex-wrapper` で `python3 -m unittest test_codex_config` が通ることを完了条件にする（venv が無いので SDK を import しないテストに限る）。
