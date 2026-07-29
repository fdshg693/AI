# Step 3(実験): hookを使ったログ仕込みの実地検証

> [02-write-logs-and-settings.md](02-write-logs-and-settings.md) の続き。このステップはドキュメント成果物を書かない。実際にテスト用hookを仕込んで発火させ、結果メモを残して [04-write-hooks-logging.md](04-write-hooks-logging.md) に引き渡す。

## やること

`writing-hooks/hooks.md`に書かれているhook機構（type、matcher、exit code、JSON入出力、Windows特有の罠）を、実際に `.claude/settings.local.json` に一時的なテスト用hookを仕込んで検証する。「ドキュメント通りに動くか」「Windows環境固有の詰まりポイントが実際に再現するか」「どんなテンプレートなら実用的か」を手を動かして確認し、`hooks-logging.md`に載せるテンプレートの元ネタにする。

## 検証観点・仮説

- 最小のログ仕込み — `PostToolUse`でツール呼び出しをjsonlに追記するhookを実際に設定し、数回ツールを使って発火させ、出力されたjsonlの中身が`writing-hooks/hooks.md`記載のstdin構造（`tool_name`, `tool_input`, `tool_response`, `session_id`, `transcript_path`, `cwd`）と一致するか確認する
- exit codeの実際の挙動 — exit 0 + JSON出力／exit 2 + stderr／それ以外、のパターンをそれぞれ試し、ドキュメント記載どおりの挙動（exit 1が非ブロッキング扱いになる等）を実際に確認する
- Windows特有の罠の再現確認 — exec form（`args`指定）で`.cmd`/`.bat`シムを直接呼ぶとどう失敗するか、shell formとの違い、`shell: powershell`指定時の`${CLAUDE_PROJECT_DIR}`展開の実際の挙動
- hook自体のデバッグ手段の実際の見え方 — `claude --debug hooks`、`CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose`、`Ctrl+O`でのトランスクリプト表示それぞれで、仕込んだhookの発火がどう見えるか
- matcherの落とし穴の再現 — ハイフン付き名前や正規表現扱いになるケースが実際にこの環境のClaude Codeバージョンで再現するか（バージョン依存の記述のため）

## 検証の進め方（安全な実行方法・後片付け）

- テスト用hookは必ず `.claude/settings.local.json`（gitignore対象、個人ローカル）に追加する。プロジェクト共有の `.claude/settings.json` は変更しない
- ログの追記先は `C:\Users\xingw\AppData\Local\Temp\claude\...\scratchpad` 配下の一時ファイルにし、リポジトリ内に検証用ログを残さない
- 検証が終わったら、このステップの最後に必ず `.claude/settings.local.json` からテスト用hookの設定を削除し、通常のセッション挙動に影響が残らないようにする

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[04-write-hooks-logging.md](04-write-hooks-logging.md) 側から要約だけを参照する
  - 実際に動いた最小構成のhook設定（テンプレート化できる形）
  - ドキュメント記載と異なった実際の挙動（あれば）
  - Windowsで実際につまずいた点・回避方法
  - どのデバッグ手段（`--debug hooks`/`--debug-file`/`Ctrl+O`）が最も原因切り分けに有効だったか

## `.claude/rules` 更新ポイント

- なし

## 検証結果メモ（実施済み）

検証環境: Windows 11 / Claude Code v2.1.215（Step1と同一）。テスト用hookは全て `.claude/settings.local.json` に一時追加し、検証完了後に `{"outputStyle": "default"}` へ復元済み（リポジトリに検証用hookは残っていない）。ログ追記先・テストスクリプトは全て scratchpad 配下（`hook_log.py` / `hook_exit.py` / `hook_exit_json.py`）。

### 実際に動いた最小構成（テンプレート化できる形）

- `PostToolUse` + `matcher: "Bash"` + `type: "command"` で、shell formの `python "<script>" "<logpath>"` を指定 → **設定ファイル編集後、セッション再起動なしで即座にhot reloadされて発火した**（`.claude/settings.local.json` の変更をwatchしている旨のログ行 `Watching for changes in setting files ...` を確認）
- 発火したstdinの実際のJSON構造（Bashツール1回分）:
  ```
  {"session_id":"...","transcript_path":"...","cwd":"...","prompt_id":"...","permission_mode":"auto","effort":{"level":"high"},"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"...","description":"..."},"tool_response":{"stdout":"...","stderr":"","interrupted":false,"isImage":false,"noOutputExpected":false},"tool_use_id":"...","duration_ms":1148}
  ```
  `writing-hooks/hooks.md` 記載の `tool_name`/`tool_input`/`tool_response`/`session_id`/`transcript_path`/`cwd` は全て一致。**未記載の追加フィールドを確認**: `prompt_id`, `permission_mode`, `effort`（`{"level":"high"}`）, `tool_use_id`, `duration_ms`
- ログ追記は `python -c "..."` のインラインではなく、**別ファイルのスクリプトを絶対パスで呼ぶ形が安全**（JSON内でのクォートエスケープ地獄を回避できる）
- **追加検証（ユーザー指摘を受けて実施）: shell formの文字列コマンドではなく、`"command": "python", "args": ["<script>", "<arg>"]` という exec form で同じログ仕込みを行うテストも実施した。** 通常のBashトリガーと、出力に `'`（シングルクォート）・`"`（ダブルクォート）を含むBashトリガーの2種類で発火させたところ、**どちらもエラーなく正しくログに追記された**（`--debug-file`を介さず、通常のツール呼び出し結果として直接確認）。JSON入力はstdin経由で渡るため、コマンドライン上でのクォート処理が一切発生せず、shell formで起こりうるクォート/エスケープ由来のトラブルが構造的に発生しない。以降、ログ仕込みテンプレートは全てこのexec form（`command: "python"` 固定 + `args`にスクリプトパスと引数を配列で渡す）に統一する。npm.cmdのexec form検証（前掲）と合わせて、Windowsでも`python`という拡張子なしコマンドがexec formで正しく解決されることを確認済み

### exit codeの実際の挙動

`PreToolUse` + `matcher: "Glob"` に対して3パターンを個別に試行:

| パターン                                                                                           | 結果                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exit 2` + stderr出力                                                                              | Globツール呼び出しがブロックされ、エラーとして `PreToolUse:Glob hook error: [<command>]: <stderrの内容>` がそのままアシスタント側に見える形で返ってきた。ドキュメント通り                                |
| `exit 0` + `{"hookSpecificOutput":{"permissionDecision":"deny","permissionDecisionReason":"..."}}` | 同様にブロックされたが、**`hook error` というプレフィックスは付かず、`permissionDecisionReason` の文言だけがそのままエラーとして返ってきた**（exit 2のケースとの違いとして実装者が区別できる有用な情報） |
| `exit 1` + stderr出力                                                                              | ブロックされず、Globツール呼び出しは正常に完了した（`No files found` 相当の結果がそのまま返った）。ドキュメント記載通り「exit 1は失敗として扱われない」を確認                                            |

### Windows特有の罠の再現確認

- **exec form + `.cmd`シム（`command: "npm", args: ["--version"]`）は、ドキュメントの「起動できない」という記載と相違し、実際には成功した**。`--debug-file`での確認で `Hook output does not start with {, treating as plain text` に続けて `Hook PreToolUse:Glob (PreToolUse) success:` の後にnpmのバージョン文字列（`11.2.0`）がそのまま出力されているのを確認。少なくともこの環境（Claude Code v2.1.215、同梱Node.js）では `.cmd` シムの直接起動が失敗しない。Node.jsが2024年のセキュリティ修正以降 `.cmd`/`.bat` 拡張子のコマンドをspawn時に自動的に `cmd.exe` でラップするようになった影響と推測されるが、断定はできない。**ドキュメント記載は古い/Node.jsバージョン依存の可能性がある**ため、hooks-logging.mdには「ドキュメント上の既知の制約」として記載しつつ、この環境では再現しなかった旨を明記する
- **`shell: "powershell"` 指定時の `${CLAUDE_PROJECT_DIR}` 展開は、ドキュメント記載通りに完全再現した**。同一コマンド内で4パターンを同時テストした結果:
  - 二重引用符内の `${CLAUDE_PROJECT_DIR}` → `C:\CodeRoot\AI`（展開成功）
  - 単一引用符内の `${CLAUDE_PROJECT_DIR}` → `${env:CLAUDE_PROJECT_DIR}`（リテラルのまま。Claude Code側で`${env:...}`へのテキスト置換は行われるが、PowerShellの単一引用符内では変数展開されないため）
  - `$env:CLAUDE_PROJECT_DIR`（正しい書き方）→ `C:\CodeRoot\AI`（展開成功）
  - 裸の `$CLAUDE_PROJECT_DIR`（`$env:`なし）→ 空文字列（未定義のローカル変数として`$null`扱い）
  - **ボーナスの発見**: 裸の`$CLAUDE_PROJECT_DIR`を検知すると、Claude Code自体が `[WARN] PowerShell hook command references $CLAUDE_PROJECT_DIR, which PowerShell reads as an undefined variable ($null). Use $env:CLAUDE_PROJECT_DIR or ${CLAUDE_PROJECT_DIR} instead.` という警告をデバッグログに出す。ドキュメントには書かれていないが実務上有用なので追記する
- matcherのハイフン正規表現の罠（`code-reviewer`等のsubagent名）は、サブエージェント起動を伴う検証コストが高い（実際にAPIコールが発生する）ため、今回は独立検証を行わなかった。Step1で確認済みのバージョン（v2.1.215）は、ドキュメント記載の修正版（v2.1.195以前で発生）より新しいため、再現しない可能性が高いという推測に留める

### hook自体のデバッグ手段の実際の見え方

- **`claude --debug-file <path>` が最も原因切り分けに有効だった**。`claude -p "..." --model claude-haiku-4-5-20251001 --debug-file <path> --no-session-persistence` の非対話1回実行で、hookのstdout内容・成功/失敗・警告メッセージまで全てファイルに残り、後から`grep`で追える。今回の全検証（exit code挙動、exec form成否、PowerShell展開結果）はこの方法で裏取りした
- `CLAUDE_CODE_DEBUG_LOG_LEVEL=verbose` を併用すると、`--debug-file`だけでは出てこない **matcher評価の過程**（`Getting matching hook commands for PreToolUse with query: Glob` → `Found 1 hook matchers in settings` → `Matched 1 unique hooks for query "Glob"`）が追加で見える。マッチしない・意図しないhookが多重発火する等の切り分けにはverboseが必須
- `Hooks: Found 0 total hooks in registry` というログ行は、実際にhookが発火していても常に0と表示される（別のレジストリを指しているとみられる紛らわしい行）。**このログ行だけを見てhookが未登録と判断しないこと**を注意点として記載する価値がある
- `Ctrl+O`でのトランスクリプト表示は対話UIが前提のため、今回のツール呼び出し経由の実行環境からは直接検証できなかった（ドキュメント記載をそのまま採用し、未検証である旨を明記する）
