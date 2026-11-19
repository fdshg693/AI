---
type: Plan Step
status: ready
---

# Step 6: codex-wrapper — `MODEL` 直書きを `config.toml` へ

## やること

`main.py` の `MODEL = "gpt-5.6-luna"` と argparse の説明文に埋まったモデル名を削除し、`codex-wrapper/config.toml` のカタログから読む。Step 1 で分かった上限を付け、スレッド ID・使用量をログに出す。

## 読むべきファイル・実行推奨Grep

**現行の呼び出しを確認するため（優先度: 高）**

- 読む: `workflow/codex-wrapper/main.py`、`workflow/codex-wrapper/AGENTS.md`（実行方法が `pip` + `python` のまま）
- Step 1 の調査結果は下の決定事項に反映済み（根拠: [progress/01-research-results.md](progress/01-research-results.md)）

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

| 決定                                                                                                                                                                                                                                                                                                                                   | 理由                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `[limits]` は `max_items`（1 ターン内の `item/completed` 数）・`timeout_seconds`・`max_total_tokens`。`thread.run()` をやめ、`AsyncCodex` の `thread.turn()` + `stream()` で経過時間・item 数・`ThreadTokenUsageUpdatedNotification` の累計を監視し、超えたら `handle.interrupt()`、最後に `Codex.close()`（`with`）でプロセスを止める | Step 1: SDK にターン数・タイムアウト・予算のオプションは無い。`asyncio` のキャンセルだけではワーカースレッドが残る |
| ログ: 要求エイリアス・カタログの `id`・`thread.read().thread.model`（`ModelReroutedNotification` があればその `to_model`）・`thread.id`・`result.usage.total`・`status`（`RuntimeError` は `failed`）・自前の終了理由。コスト（USD）は記録しない                                                                                       | Step 1: コストは非公開 API の推定値しか無い                                                                        |
| `openai-codex` のバージョンは固定しない（pyproject が無いため）。AGENTS.md に動作確認した版（2026-11-14 時点の PyPI 0.169.0）を 1 行書く                                                                                                                                                                                               | Step 1: uv.lock にも .venv にも入っていない                                                                        |
| `pyproject.toml` の新設・アンブレラ workspace への登録は本プランの対象外                                                                                                                                                                                                                                                               | 規約が求めるのは設定の一元化で、パッケージ化は別件。`tomllib` は標準ライブラリなので依存追加は不要                 |
| `sandbox=Sandbox.read_only` は変えない                                                                                                                                                                                                                                                                                                 | 規約 §4 に沿っている                                                                                               |

- 落とし穴: `tomllib` は Python 3.11+。`pyproject.toml` が無いので `requires-python` で守れない。AGENTS.md に必要バージョンを書く。
- 落とし穴: `cwd` が `parents[2]`（アンブレラ全体）になっている。規約 §4「リポジトリ全体を渡さない」に触れるが read-only なので今回は変えず、Step 9 で移行表に残す。

## 実行中に判明した変更

- 2026-11-14（Step 1 完了時）: SDK の上限・使用量の調査結果を「決定事項・注意点」に反映（上限の自前監視・ログ項目・SDK 版の記録）。根拠は [progress/01-research-results.md](progress/01-research-results.md)。

## ルール更新ポイント

- `workflow/codex-wrapper/AGENTS.md`: セットアップ手順と Python 3.11+ の注記。

## 進め方

- **実行主体**: メインエージェント。
- **TODO化**: 1 項目（1 コミット）。`workflow/codex-wrapper` で `python3 -m unittest test_codex_config` が通ることを完了条件にする（venv が無いので SDK を import しないテストに限る）。
