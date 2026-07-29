---
name: task-tracker-hook-mechanism-notes
description: task-trackerスキル実装のために調べたUserPromptExpansionフックとトランスクリプト所在の技術メモ
metadata:
  type: memo
---

# 技術調査メモ（実装時にここを読めば再調査不要なはず）

## `UserPromptExpansion` イベント

- 発火条件: ユーザーが**直接タイプした**スラッシュコマンド（skillも含む）やMCP promptが、プロンプトへ展開される**前**。Claudeがモデル判断でskillを自動起動した場合は発火しない（`PreToolUse`+`Skill`ツールの領域）。
  - → `task-tracker`は`disable-model-invocation: true`にする設計なので、この非対称性は気にしなくてよい（常にユーザー直接入力経由になる）
- `matcher`は`command_name`に対して評価される。`task-tracker`はハイフンのみで英数字・`-`のみの文字種なので完全一致として評価される（正規表現扱いにはならない）
- stdin JSON（common fieldsに加えて）:
  ```json
  {
    "session_id": "abc123",
    "transcript_path": "/Users/.../00893aaf.jsonl",
    "cwd": "/Users/...",
    "permission_mode": "default",
    "hook_event_name": "UserPromptExpansion",
    "expansion_type": "slash_command",
    "command_name": "example-skill",
    "command_args": "arg1 arg2",
    "command_source": "plugin",
    "prompt": "/example-skill arg1 arg2"
  }
  ```
  - `command_args`は生の文字列（シェル的なクォート展開などはされていない）。複数語のタスク名を許すなら`shlex`的なパースが必要だが、タスク名はkebab-case想定なので単純に最初の空白区切りトークンを取れば十分
  - `expansion_type`は`slash_command`（skill/custom command）か`mcp_prompt`。念のため`slash_command`であることも確認しておくとより安全
- decision control: `UserPromptExpansion`は展開自体をブロックできる（今回は使わない。不正なタスク名でもブロックせず`additionalContext`で警告するだけに留める設計）
- 出典: `.claude/skills/claude-code-docs/output/llms-full.txt` 内 `### UserPromptExpansion`（2026-07-26時点のドキュメントキャッシュ。バージョンで変わり得るので実装直前に`claude-code-docs`スキル経由で最新化推奨）

## セッショントランスクリプトの所在（`dump_sessions.py`用）

出典: [.claude/skills/claude-code-debugging/logs-and-settings.md](../../claude-code-debugging/logs-and-settings.md)

- `~/.claude/projects/<project>/<session-id>.jsonl` — セッショントランスクリプト本体。1行1JSON
  - `<project>`は作業ディレクトリの絶対パスの非英数字を`-`に置換したもの
  - **実地検証で確認済みの注意点**: ドライブレターが小文字化される場合がある（`C:\CodeRoot\AI` → `c--CodeRoot-AI`）。大文字始まりのディレクトリ（`C--CodeRoot-AI-*`）も同居することがあり表記揺れが実在する。決め打ち検索せず`~/.claude/projects/*/​<session_id>.jsonl`のように**projectディレクトリ名をワイルドカードにしてglobする**のが安全（session_id自体はUUID相当でグローバルにユニークなので、project名を絞り込まなくても実用上問題ない）
  - 巨大なツール出力は`<session-id>/tool-results/`ディレクトリに退避され、jsonl側には参照のみが残ることがある → `dump_sessions.py`は基本的にuser/assistantのテキストのみを対象にし、tool-results配下までは追わない設計でよい（PLAN.mdのオープンクエスチョン参照）
- 実体はバージョン間で内部形式に差異があるため、厳密な型定義に依存せず`obj.get(...)`的な緩い読み方にする（既存の`extract_log.py`もこの方針）

## 参考実装（コードは直接依存しないが読み方の参考にする）

[.claude/skills/claude-code-debugging/scripts/extract_log.py](../../claude-code-debugging/scripts/extract_log.py) の `cmd_transcript` 関数:

- jsonlを1行ずつ`json.loads`、パース失敗行は`warning`を出しつつスキップ（例外で全体を落とさない）
- `message.content[]`の中の`type == "tool_use"`エントリから`tool_name`一覧を抽出
- 出力は`output/temp/`配下（このリポジトリの`.gitignore`の`temp/`ルールで除外される）

`dump_sessions.py`もこの「パース失敗行はスキップして続行」「出力はtemp/配下」という方針を踏襲する。
