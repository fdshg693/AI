---
trigger: glob
glob: tools/claude-wrapper/**
description:
---

# Claude Agent SDK を使った、カスタマイズした Claude 利用 CLI ツール

## 関連ファイル

- `.claude\skills\claude-agent-sdk\`

## ファイル構成

- `minimal_agent.py` — Haiku モデルに一回限りのクエリを送る最小の動作確認スクリプト
- `todo_runner.py` — todo.json / NEXT.md 駆動の自律タスク実行ループ（詳細は後述）
- `pyproject.toml` — 依存関係定義（`claude-agent-sdk`）

## セットアップ

前提: `claude` CLI がインストール・ログイン済みであること（または環境変数 `ANTHROPIC_API_KEY` を設定）。

グローバルPythonにインストールする:

```powershell
python -m pip install claude-agent-sdk
```

## 実行

```powershell
cd tools\claude-wrapper
python minimal_agent.py
```

期待される出力（応答テキスト + 終了ステータス）:

```text
私はClaudeで、... をサポートするエージェントです。
終了: success
```

`ClaudeAgentOptions(model="haiku")` の `haiku` エイリアスは `claude-haiku-4-5` に解決される（動作確認済み）。
モデルエイリアスの仕様は公式ドキュメント `https://code.claude.com/docs/en/model-config` を参照。

## todo_runner.py — TODO 駆動の自律実行ループ

通常の AI CLI ツールではタスクごとにコンテキストが積み重なり、コンパクションしても
コンテキストを完全にはクリーンにできない。このスクリプトは、エージェントの記憶を
「システムプロンプト + 目標 + NEXT.md + todo.json 等の実ファイル」だけに限定し、
TODO が全完了するまで作業を継続する。

### 仕組み

1. エージェントはシステムプロンプトの指示により、目標をタスク分割して `todo.json`
   （`{"tasks": [{"id", "title", "status": pending|in_progress|done}]}`）を作成する。
2. 1 回のエージェント呼び出しでは **1 タスクだけ**を完了させ、次タスクへの
   引継ぎ事項を `NEXT.md` に書いて終了する。
3. アプリ側はエージェント終了ごとに `todo.json` を検査し、全タスク `done` でない
   限り `query()` の**新規セッション**でエージェントを再呼び出しする
   （`resume` / `continue_conversation` は使わないのでコンテキストは完全にクリーン）。
   その際、固定システムプロンプトとともに `NEXT.md` の内容をプロンプトへ注入し、
   `NEXT.md` は空にする。
4. 全タスク `done` で正常終了（exit 0）。停滞検出（完了数が増えない連続回数）と
   イテレーション上限で打ち切る安全機構あり。

### 実行

```powershell
cd tools\claude-wrapper
python todo_runner.py "達成したい目標" --workdir <作業ディレクトリ> --model haiku
```

主なオプション: `--max-iterations`（既定 20）、`--max-turns`（既定 15）、
`--max-stagnant`（既定 3）。

### Haiku での実測（2026-07-19）

4 タスクの俳句作成目標を 4 イテレーション（各 8〜11 ターン、計約 $0.18）で完走。
注意点として、Haiku は `cwd` を絶対パスへ正しく解決できず `/work/...` 等へ
迷走し、作業ディレクトリ外へ書き込んで「完了」と誤報することがあった。
対策として、システムプロンプト・ユーザープロンプト双方に作業ディレクトリの
絶対パスを埋め込み、「`/` 始まり・相対パス禁止、必ず `<workdir>\...` の
絶対パスを使う」と明示している（これで迷走は解消）。

### 参照した公式ドキュメント

- `https://code.claude.com/docs/en/agent-sdk/python` — `query()` は既定で毎回新規セッション、
  `ClaudeAgentOptions`（`system_prompt`, `permission_mode`, `setting_sources` 等）、
  `ResultMessage`（`subtype` / `is_error` / `errors`）
- `https://code.claude.com/docs/en/agent-sdk/sessions` — セッションを継がず
  「必要な情報をアプリ側で保持し新規セッションのプロンプトに注入する」設計
- `https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts` — カスタム
  システムプロンプトの指定方法
