# Step 7(実験): Claude CLIによる完全分離テストの実地検証

> [06-write-otel-reference.md](06-write-otel-reference.md) の続き。このステップはドキュメント成果物を書かない。実際にClaude CLIを分離実行して結果メモを残し、[08-write-testing.md](08-write-testing.md) に引き渡す。

## やること

`claude-cli-use`スキルの`-p`/`--print`単発実行と、`claude-logs-investigate`が触れている`CLAUDE_CONFIG_DIR`・`--safe-mode`を組み合わせ、「現在のセッションの設定・hookから完全に切り離されたテスト環境」を実際に作れるか検証する。あわせて、サブエージェント（Agent tool）で同種の検証を行った場合との違い（設定・hookを共有してしまう制約）を実際に比較する。

## 検証観点・仮説

- `CLAUDE_CONFIG_DIR`分離の実効性 — 一時ディレクトリを`CLAUDE_CONFIG_DIR`に指定して`claude -p`を実行し、プロジェクトの`.claude/settings.json`のhookやpermissionsが実際に適用されない（＝まっさらな状態から始まる）ことを確認する
- `--safe-mode`との比較 — 同じタスクを`--safe-mode`あり/なしで実行し、hook・MCP・skillsの有無で挙動がどう変わるかを実際に比較する
- `--debug-file`での記録 — 分離実行時に`--debug-file <path>`を付けてログを取得し、後段の抽出スクリプト検証（Step9・10）に使える実データを確保する
- サブエージェントとの違いの実測 — Agent toolで似た確認作業をさせた場合、親セッションのhook・settingsが実際に引き継がれる（＝完全分離ではない）ことを、可能な範囲で実際に確認する
- 権限を絞った読み取り専用実行 — `--tools Read,Grep,Glob --permission-mode plan`での制限付き実行が意図通り書き込み不可になることを確認する

## 検証の進め方（安全な実行方法・後片付け）

- `CLAUDE_CONFIG_DIR`には必ずスクラッチ領域配下の一時ディレクトリを指定し、既存の`~/.claude`には触れない
- `--dangerously-skip-permissions`は使わない（`claude-cli-use`の既定方針どおり）
- API課金を伴うため、確認は短い非対話タスク（例: 単純な質問への応答）に留め、大掛かりなコーディングタスクは実行しない
- 検証で作成した一時`CLAUDE_CONFIG_DIR`ディレクトリと`--debug-file`の出力先は、Step9・10で使う分を除いてこのステップの最後に整理する

## 検証結果の記録方法（後続ステップから参照する）

- 実装時にこのステップを実行したら、以下を簡潔な箇条書きでこのファイルの末尾（またはこのステップの実行ログ）に追記し、[08-write-testing.md](08-write-testing.md) 側から要約だけを参照する
  - 実際に確認できた分離実行の具体的なコマンド（`CLAUDE_CONFIG_DIR`・`--safe-mode`・`--debug-file`の組み合わせ）
  - サブエージェントとClaude CLI分離の違いとして実際に確認できた点
  - Step9・10で使う実データ（`--debug-file`出力等）の保存先パス

## `.claude/rules` 更新ポイント

- なし

## 検証結果メモ（実装時に追記）

環境: Windows 11 / Claude Code v2.1.215（Step1と同一）。一時プロジェクトは `<SCRATCH>/step7-cli-isolation/test-project`（`.claude/settings.json` にPreToolUse+Bashのログhookを仕込み、`hook-fired.jsonl` に発火有無を記録させた）。一時`CLAUDE_CONFIG_DIR`は `<SCRATCH>/step7-cli-isolation/config-dir-clean`。

### 1. `CLAUDE_CONFIG_DIR`分離の実効性 — ユーザースコープのみ分離、プロジェクトスコープは分離されない

```bash
cd <test-project> && \
CLAUDE_CONFIG_DIR=<config-dir-clean> claude -p "Run the bash command: echo hello-from-isolated-run" \
  --model haiku \
  --debug-file <debug-logs>/A2-clean-config-dir-authed.log \
  --no-session-persistence
```

- **`CLAUDE_CONFIG_DIR`は`~/.claude`相当のユーザースコープ（`settings.json`・`.credentials.json`・`projects/`等）だけを差し替える。プロジェクト直下の`.claude/settings.json`（hookを含む）は分離対象外で、そのまま読み込まれ発火する**。実測: 上記コマンド実行後、`test-project/hook-fired.jsonl`にPreToolUse hookの発火記録（`tool_name: Bash`のstdin JSON）が実際に書き込まれた。`--debug-file`のログにも `Watching for changes in setting files <config-dir-clean>\settings.json, <test-project>\.claude\settings.json, <test-project>\.claude\settings.local.json...` という行があり、プロジェクト側`settings.json`が監視・読み込み対象に含まれていることを裏付けている。
  - ⚠️ **落とし穴**: 「`CLAUDE_CONFIG_DIR`を一時ディレクトリにすれば設定・hookから完全に切り離せる」という理解は誤り。プロジェクトディレクトリの外（`.claude/settings.json`が存在しない場所）で実行するか、後述の`--safe-mode`を併用しない限り、プロジェクトのhook・permissionsはそのまま効いてしまう。
- **完全にクリーンな`CLAUDE_CONFIG_DIR`では認証情報(`.credentials.json`)も見えなくなり、API呼び出し前に失敗する**。実測: `.credentials.json`を用意していない状態で同じコマンドを実行したところ、`[ERROR] API error (attempt 1/11): Could not resolve authentication method. Expected one of apiKey, authToken, credentials, config, or profile to be set...` で失敗し、`Not logged in · Please run /login`が出力された（Bashツールは一度も呼ばれず、hookが発火する機会自体がなかった）。分離環境で実際にタスクを完走させて検証したい場合は、（a）`~/.claude/.credentials.json`を一時`CLAUDE_CONFIG_DIR`にコピーする、または（b）`ANTHROPIC_API_KEY`環境変数を渡す、のいずれかが必要（ユーザーへの確認要。認証情報のコピーはClaude Code自身の権限分類器が機微操作として確認を要求してくることがある — 実際に本検証でもブロックされ、ユーザーの明示承認を得た上でコピーを実行した）。検証後は一時`CLAUDE_CONFIG_DIR`ごと削除して後片付けする。

### 2. `--safe-mode`との比較 — プロジェクトスコープのhookも含めて無効化される

```bash
cd <test-project> && \
CLAUDE_CONFIG_DIR=<config-dir-clean> claude -p "Run the bash command: echo hello-from-safe-mode-run" \
  --model haiku \
  --safe-mode \
  --debug-file <debug-logs>/B-safe-mode.log \
  --no-session-persistence
```

- 実測: 上記コマンド実行後、`hook-fired.jsonl`は**作成されなかった**（＝プロジェクトの`.claude/settings.json`のhookが発火しなかった）。`CLAUDE_CONFIG_DIR`分離だけでは防げなかったプロジェクトスコープのhookも、`--safe-mode`なら確実に無効化できることを確認。
- `--debug-file`のログに `[DEBUG] Skipping plugin hooks - safe mode disables plugins (managed settings-file hooks still run)` という行があり、**managed policy設定のhookだけは`--safe-mode`でも無効化されない**というヘルプ記載（`Admin-managed (policy) settings still apply`）通りの挙動を実機でも確認した。
- 「本当に設定由来の問題かhook由来の問題かを切り分けたい」場合は、`CLAUDE_CONFIG_DIR`分離だけでなく`--safe-mode`を併用する（またはそちらだけを使う）べき、という結論が実測で裏付けられた。

### 3. `--debug-file`での記録

上記1・2のコマンドはいずれも`--debug-file <path>`を付けて実行しており、`grep`で狙った行（`Watching for changes in setting files`, `safe mode`, `API error`等）を後から追える形でログを確保できた。Step9・10で使う実データとして以下を保持:

- `<SCRATCH>/step7-cli-isolation/debug-logs/A-clean-config-dir.log`（認証情報なし・失敗ケース。API呼び出し前の設定読み込みログの参考に有用）
- `<SCRATCH>/step7-cli-isolation/debug-logs/A2-clean-config-dir-authed.log`（認証情報コピー後・成功ケース）
- `<SCRATCH>/step7-cli-isolation/debug-logs/B-safe-mode.log`（`--safe-mode`比較）
- `<SCRATCH>/step7-cli-isolation/debug-logs/D-readonly.log`（下記4の読み取り専用実行）
- `<SCRATCH>/step7-cli-isolation/test-project/hook-fired.A2.jsonl`（1で発火した実際のhook stdin JSON）

### 4. 権限を絞った読み取り専用実行

```bash
cd <test-project> && \
CLAUDE_CONFIG_DIR=<config-dir-clean> claude -p "Create a new file named should-not-exist.txt with the text 'hi' in it." \
  --model haiku \
  --tools Read,Grep,Glob \
  --permission-mode plan \
  --debug-file <debug-logs>/D-readonly.log \
  --no-session-persistence
```

- 実測: ファイル`should-not-exist.txt`は作成されなかった。応答は「I don't have access to a Write tool in this session, so I can't create the plan file required by plan mode. Could you enable file-writing tools, or let me know how you'd like to proceed?」——**`plan`モード自体が計画提示にWrite系ツールを要求するため、`--tools`でWriteを完全に外すと計画の提示すらできず、書き込み不可であることが明示的な応答として返ってくる**という具体的な組み合わせの挙動を確認した。単なる「拒否されて終わり」ではなく、モデル側が理由を説明して差し戻す形になる点はドキュメントだけでは分からなかった実地検証の成果。

### 5. サブエージェントとの違いの実測 — 親セッションのhook・settingsを完全に共有する

- 本番プロジェクト（`C:\CodeRoot\AI`）の`.claude/settings.local.json`に一時的なPreToolUse+Bashログhookを追加し（検証後に削除・原状復帰済み）、Agent tool（`general-purpose`）で「`echo hello-from-subagent-test`をBashで実行するだけ」の単純タスクを起動して実測した。
- 結果: サブエージェントのBash呼び出しでも親セッションのhookが**そのまま発火**した。発火したhookのstdin JSONには`agent_id`・`agent_type`フィールドが追加される一方、**`session_id`と`transcript_path`は親セッションと完全に同一**だった（別セッションとして分離されていない）。
- 結論: サブエージェント（Agent tool）は独立した設定・hook環境を持たず、常に親セッションのものを共有する。「hookやsettingsの変更が本当に効くか」を完全にクリーンな状態で確認したい場合はサブエージェントでは不十分で、`CLAUDE_CONFIG_DIR`分離＋（必要なら）`--safe-mode`を使ったClaude CLI別プロセス起動が必要、という区分けが実測で裏付けられた。

### 後片付け

- 一時`CLAUDE_CONFIG_DIR`（`.credentials.json`のコピーを含む）は検証完了後に削除済み。
- 本番プロジェクトの`.claude/settings.local.json`に追加した一時hookと`.claude/hook-scripts-tmp-step7/`は検証後に削除し、`settings.local.json`は元の内容（`{"outputStyle": "default"}`）に復帰済み。
- `<SCRATCH>/step7-cli-isolation/debug-logs/`と`test-project/hook-fired.A2.jsonl`はStep9・10で使うため保持。
