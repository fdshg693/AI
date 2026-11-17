# Step2 調査: ツール別の詳細結果

> [../02-research-log-formats.md](../02-research-log-formats.md) の実行で得られた詳細。要約と後続ステップへの反映はプラン本体（Step2「調査結果」、Step3・Step4 の決定事項）にある。ここは根拠・フィールド表・未解決事項の参照元。

- 調査日: 2026-11-17。6 ツールを読み取り専用のサブエージェントに 1 つずつ委任し、実ログは構造だけを集計させた（会話本文・秘密情報は持ち帰っていない）。レコード例の値はすべて架空。
- 「実データ推定」と書いた事項はこの PC の実ログから推定したもので、公式に記載が無くバージョン依存・未保証。
- 調査の副作用の疑い: Antigravity の `conversation_summaries.db` などを `mode=ro` で開いたあと、隣に 0 バイトの `-wal` と 32KB の `-shm` ができていた（アプリ起動中だった可能性もあり未確定）。詳細は Antigravity の節。

## Claude Code

- 調査日: 2026-11-17。確認したバージョン: Claude Code 2.1.325（`claude --version`）。実データの `version` は 2.1.301〜2.1.325 の 12 版。
- 調べた実データ: `~/.claude/projects/` の 109 ディレクトリ（約 521MB）にある jsonl 749 本。サブエージェント分の 49 本を含み、`journal.jsonl` は除く。全 78,126 レコードを集計し、JSON の壊れた行は 0。ファイルの更新日は 2026-10-19〜2026-11-17。
- 実データにはまだ無い形式の扱い: compact 境界、`summary` レコード、`progress` レコードは、この PC には 1 件も無かった（下の「未解決」を参照）。

### 所在

- 基点は `~/.claude`。Windows では `%USERPROFILE%\.claude`、macOS/Linux では `~/.claude`。`CLAUDE_CONFIG_DIR` を設定すると全体がそのディレクトリへ移る（公式記載）。
- 一時ディレクトリ（scratchpad）は `~/.claude` の外にある。Windows は `%TEMP%\claude\<project>\<session>\scratchpad\`、Linux は `/tmp/claude-<uid>/...`、macOS は `/private/tmp/claude-<uid>/...`（公式記載）。

| パス（`~/.claude/` から）                                                          | 中身                                                             | 実データ         |
| ---------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------- |
| `projects/<enc-cwd>/<sessionId>.jsonl`                                             | メインのトランスクリプト                                         | 有               |
| `projects/<enc-cwd>/<sessionId>/subagents/agent-<agentId>.jsonl` と `.meta.json`   | サブエージェントのトランスクリプト（メインと同じ形式、公式記載） | 有 42 組         |
| `projects/<enc>/<sid>/subagents/workflows/wf_<id>/agent-*.jsonl`・`journal.jsonl`  | Workflow から起動したサブエージェント（公式に記載なし）          | 有               |
| `projects/<enc>/<sid>/tool-results/<rand>.txt`                                     | 大きいツール出力の退避先                                         | 有 175           |
| `projects/<enc>/<sid>/mcp-tasks/`                                                  | MCP タスクの再開用データ                                         | 無               |
| `projects/<enc>/<sid>.orphaned-<ts>-<suffix>.jsonl`・`<sid>.jsonl.superseded-<ts>` | 退避された旧トランスクリプト。セッション一覧に出ない（公式記載） | 無               |
| `projects/<enc>/memory/*.md`                                                       | auto memory。ログではない                                        | 有               |
| `history.jsonl`                                                                    | 入力したプロンプトの履歴（プロジェクト横断）                     | 有 464 行        |
| `sessions/<pid>.json`                                                              | 実行中セッションの登録簿                                         | 有 8             |
| `stats-cache.json`                                                                 | `/usage` 用の集計キャッシュ                                      | 有               |
| `file-history/<sessionId>/<hash>@v<n>`                                             | 編集前のファイルの写し（チェックポイント用）                     | 有 914           |
| `debug/<sessionId>.txt`                                                            | `--debug` か `/debug` のときだけ書かれる                         | 空               |
| `session-env/<sessionId>/`                                                         | セッションごとの環境メタデータ                                   | ディレクトリだけ |
| `shell-snapshots/snapshot-bash-<epochms>-<rand>.sh`                                | シェル環境のスナップショット                                     | 有               |
| `teams/`                                                                           | 空                                                               | 空               |
| `plans/`・`tasks/`・`paste-cache/`・`image-cache/`                                 | 公式に記載あり                                                   | 未確認           |
| `todos/`・`statsig/`・`logs/`                                                      | 旧版の名残。今は書かれない（公式記載）                           | —                |

### 形式とレコード構造

- 形式は JSONL で、1 行 1 JSON。基本は追記だけ。1 行の最大は約 740KB だった。
- 公式の位置づけ: 中身はメッセージ、ツール呼び出し、ツール結果に加え、システムプロンプト、ツール定義、リクエストのパラメータまで入る。フィールドの細かい構造は公式に書かれておらず、以下はすべて実データからの推定で、バージョンにより変わりうる。

**`type` の出現数（全ファイル合計）**

| 種別                    | 件数   |
| ----------------------- | ------ |
| `assistant`             | 25,683 |
| `attachment`            | 21,623 |
| `user`                  | 14,495 |
| `api-request-blob`      | 14,353 |
| `api-request`           | 11,472 |
| `atis-latch`            | 7,064  |
| `last-prompt`           | 6,916  |
| `ai-title`              | 6,282  |
| `session-owner`         | 4,692  |
| `queue-operation`       | 2,088  |
| `file-history-delta`    | 1,526  |
| `tools-used`            | 1,522  |
| `file-history-snapshot` | 928    |
| `api-request-shape`     | 811    |
| `cost-state`            | 655    |
| `system`                | 294    |
| `pr-link`               | 68     |
| `mode`                  | 58     |
| `permission-mode`       | 31     |
| `custom-title`          | 30     |

- ファイルの先頭行の種別: `session-owner` 484 本、`queue-operation` 193 本、`user` 54 本、ほか。
- `system` の `subtype`: `stop_hook_summary` 278、`turn_duration` 14、`api_error` 1、`local_command` 1。
- `attachment.attachment.type`: `deferred_tools_record`、`total_tokens_reminder`、`environment`、`prompt_snapshot`、`nested_memory`、`date`、`model`、`skill_listing`、`edited_text_file`、`hook_blocking_error`、`queued_command`、`plan_mode`、`max_turns_reached` など 27 種。

**会話を表すレコード（`user` / `assistant` / `attachment` / `system`）の共通フィールド**

| フィールド                                              | 意味（実データ推定）                                                                                        |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `uuid`・`parentUuid`                                    | レコードの木構造。`parentUuid` が null なのは各ファイル先頭の `user` だけ（749 件）                         |
| `isSidechain`                                           | サブエージェントのファイルでは true、メインでは false。例外は 0 件                                          |
| `sessionId`                                             | メインではファイル名と常に一致。サブエージェントでは親のセッション ID。Workflow 配下では祖先のセッション ID |
| `agentId`                                               | サブエージェントのレコードだけにある。ファイル名 `agent-<agentId>` と対応                                   |
| `timestamp`                                             | ISO8601 の UTC、ミリ秒付き（`2026-01-01T00:00:00.000Z` の形）。全件この形                                   |
| `cwd`・`gitBranch`・`version`・`entrypoint`・`userType` | `entrypoint` は `claude-vscode`、`sdk-py`、`sdk-cli`、`cli` の 4 種                                         |
| `promptId`（user）・`requestId`（assistant）            | ターンや API リクエストとの対応                                                                             |

**`assistant` レコード**

- `message` は API の Message をそのまま持つ: `id`、`model`、`role`、`content[]`、`stop_reason`、`usage`。
- **1 レコードに content ブロックは必ず 1 個**（25,712 件すべて）。1 つの API 応答が、同じ `message.id` を持つ 1〜10 個以上のレコードに分かれて記録される。`usage` は同じ id のレコードでほぼ同じ値が繰り返される（同一 14,231 件、差あり 7 件）。
- content の型: `tool_use`（id / name / input）、`thinking`、`text`。
- `usage` の中身: `input_tokens`、`output_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens`、`cache_creation{}`、`service_tier`、`server_tool_use`、`output_tokens_details`、`iterations`、`speed` など。
- `message.model` の値: `claude-opus-5-5`、`claude-haiku-5-5`、`claude-sonnet-5-5`、`<synthetic>`（エラーなどの合成応答、8 件）。
- その他: `requestedModel`、`effort`、`isApiErrorMessage`、`error`。

**`user` レコード**

- `message.content` は文字列（人の入力、450 件）か、配列。配列の要素は `tool_result`（13,233）、`text`（1,151）、`image`（3）。
- ツール結果のレコードには `toolUseResult` が付く。中身はツールごとの構造化データで、`stdout`・`stderr`、`filePath`・`originalFile`・`structuredPatch`、`oldString`・`newString`、`persistedOutputPath` など。結果の発生元の assistant を `sourceToolAssistantUUID` で指す。
- `isMeta: true` はシステムが注入したもの（95 件）。

**会話以外のレコード（公式に記載なし）**

| 種別                                                     | フィールド                                                                                                                                                                                                                                                                                                          |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cost-state`                                             | `totalCostUSD`、`totalDuration`、`startTime`（epoch ms）、`modelUsage{<model>:{inputTokens, outputTokens, thinkingTokens, cacheReadInputTokens, cacheCreationInputTokens, webSearchRequests, costUSD}}`、`totalLinesAdded`・`totalLinesRemoved`。値は累積なので、最後のレコードがそのセッションの合計になる（推定） |
| `ai-title` / `custom-title` / `last-prompt`              | `aiTitle` / `customTitle`（`/rename` で付けた題）/ `lastPrompt`・`leafUuid`                                                                                                                                                                                                                                         |
| `session-owner`                                          | `accountUuid`・`organizationUuid`                                                                                                                                                                                                                                                                                   |
| `api-request`                                            | `params`（model、betas、max_tokens、thinking など）、`shapeHash`、`querySource`                                                                                                                                                                                                                                     |
| `api-request-shape`                                      | `shape.system[]`・`shape.tools[]`（システムプロンプトとツール定義の本体）                                                                                                                                                                                                                                           |
| `api-request-blob`                                       | `hash`、`message{role, content[]}`。リクエスト本文の重複保存で、会話本文を含む                                                                                                                                                                                                                                      |
| `queue-operation`                                        | `operation`（`enqueue` / `dequeue` / `remove`）、`content`                                                                                                                                                                                                                                                          |
| `file-history-snapshot` / `file-history-delta`           | `trackingPath`、`backup.backupFileName` など                                                                                                                                                                                                                                                                        |
| `pr-link`                                                | `prNumber`、`prUrl`、`prRepository`                                                                                                                                                                                                                                                                                 |
| `mode` / `permission-mode` / `tools-used` / `atis-latch` | 種別名どおり。`tools-used.tools[]` は使ったツール名の一覧                                                                                                                                                                                                                                                           |

- サブエージェントの `.meta.json` のキー: `agentType`、`description`、`toolUseId`（親の Agent 呼び出しの `tool_use` id）、`spawnDepth`、`finished`、`isBuiltIn`、`model?`、`effort?`、`workflowPhase?`。
- `journal.jsonl` のキー: `type`、`agentId`、`key`、`label`、`phase`。

**レコード例（値はすべて架空）**

```json
{"type":"assistant","uuid":"u2","parentUuid":"u1","isSidechain":false,"sessionId":"<sid>","timestamp":"2026-01-01T00:00:00.000Z","cwd":"C:\\proj","version":"2.1.325","requestId":"req_x","message":{"id":"msg_x","model":"claude-opus-5-5","role":"assistant","content":[{"type":"tool_use","id":"toolu_x","name":"Bash","input":{"command":"<cmd>"}}],"usage":{"input_tokens":1,"output_tokens":2,"cache_read_input_tokens":3,"cache_creation_input_tokens":4}}}
{"type":"user","uuid":"u3","parentUuid":"u2","sessionId":"<sid>","timestamp":"...","sourceToolAssistantUUID":"u2","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_x","content":"<text>"}]},"toolUseResult":{"stdout":"<text>","stderr":"","interrupted":false}}
{"type":"cost-state","sessionId":"<sid>","totalCostUSD":0.12,"startTime":1700000000000,"modelUsage":{"claude-opus-5-5":{"inputTokens":1,"outputTokens":2,"costUSD":0.1}}}
```

**周辺ファイル**

- `history.jsonl`: `{display, pastedContents{}, timestamp(epoch ms の整数), project(cwd の絶対パス), sessionId}`。
- `sessions/<pid>.json`: `pid`、`sessionId`、`cwd`、`startedAt`、`updatedAt`（epoch ms）、`version`、`kind`、`entrypoint`、`name`、`status`、`messagingSocketPath` など。
- `stats-cache.json`: `version`、`dailyActivity[]`、`dailyModelTokens[]`、`modelUsage{}`、`totalSessions`、`longestSession`、`hourCounts`。

### セッション⇔プロジェクト対応

- ディレクトリ名は、起動時の cwd の英数字以外をすべて `-` に置き換えたもの。公式の記載は scratchpad の `<project>` についてで、`projects/` にも同じ規則が当てはまることは実データで確認した。例: `C:\C\ai` → `C--C-ai`。
- **ドライブレターの大文字・小文字は起動元の書き方がそのまま残る。** VS Code から起動すると小文字になりやすい。そのため同じフォルダが `c--C-ai-...` と `C--C-ai-...` の 2 つのディレクトリに分かれる（実データで確認）。
- この変換は元に戻せない。`ai/temp` と `ai-temp` はどちらも `ai-temp` になる。**プロジェクトの正は各レコードの `cwd` にする。** ディレクトリ名は使わない。
- `cwd` はセッションの途中で変わりうる。ディレクトリ名と食い違ったレコードの内訳は、サブディレクトリ 8,830 件、大文字小文字だけの違い 2,867 件。プロジェクトは最初の `user` か `attachment` の `cwd` で決め、比較するときはドライブレターを正規化する。
- 最長のディレクトリ名は 147 文字で、切り詰めは見当たらなかった。長いパスでの扱いは未確認。
- 公式 SDK の `listSessions({dir})` は、git worktree の別パスもまとめて返す（`includeWorktrees`）。

### 読み取り安全性・保持期間・秘密情報

- **読み取り**: 追記型の JSONL で、SQLite は使っていない。書き込み中のファイルは最終行が途中で切れていることがあるので、`JSONDecodeError` は行単位で読み飛ばす。ロックはかからない（推定。今回 0 エラー）。読むときは `encoding='utf-8', errors='replace'` を付ける。
- **保持（公式記載）**: `cleanupPeriodDays` の既定は 30 日、最小は 1。0 は検証エラーになる。
  - 対象: `projects/*/<session>.jsonl`、`subagents/`（親と一緒に消える）、`tool-results/`、`file-history`（直近 100 チェックポイント分を保持）、`debug/`、`plans/`、`session-env/`、`tasks/`、`paste-cache/`、`shell-snapshots/`（正常終了で削除）。
  - 消えないもの: `history.jsonl` と `stats-cache.json` は手で消すまで残る（HIPAA 構成の場合だけ `history.jsonl` の古い行が消える）。
  - `sessions/` は終了時に消える。`memory/` はスイープの対象外。
  - Desktop・Cowork で始めたセッションの保持は `desktopSessionCleanupPeriodDays` に従う（v2.1.248 以降）。`--bare` のときと、設定が壊れているときはスイープが止まる。
  - この PC は `settings.json` に `cleanupPeriodDays` が無く、既定の 30 日。最古のファイルが 2026-10-19 で、30 日の範囲と合う。最後にスイープした時刻は `.last-cleanup` にある（公式に記載なし）。
- **秘密情報**: 公式に「平文で保存、暗号化しない。`.env` を読めば値がトランスクリプトに残る」とある。特に注意が要るフィールド:
  - 本文やコマンドの出力: `message.content` の text、`tool_use.input`、`tool_result.content`、`toolUseResult`（`originalFile` はファイル全文、`stdout` など）、`tool-results/*.txt`、`api-request-blob`、`api-request-shape`（システムプロンプト、CLAUDE.md の中身）
  - 入力や貼り付け: `attachment`（環境・メモリの注入）、`queue-operation.content`、`history.jsonl` の `display`・`pastedContents`、`last-prompt`
  - 識別子: `session-owner` の `accountUuid`・`organizationUuid`、`pr-link`、`cwd` に入るユーザー名
  - その他: `file-history` の写し、`shell-snapshots`（環境変数）
  - `~/.claude/.credentials.json` は絶対に読まない。

### 正規化スキーマへの写像

**Session**

| 項目            | 取り方                                                                           |
| --------------- | -------------------------------------------------------------------------------- |
| `id`            | ファイル名の stem（= `sessionId`）                                               |
| `tool`          | `claude-code`                                                                    |
| `project`/`cwd` | 最初の会話レコードの `cwd`                                                       |
| `started_at`    | 最初の `timestamp`。`cost-state.startTime` でもよい                              |
| `ended_at`      | 最後の `timestamp`。ファイルの mtime で代用も可                                  |
| `model`         | `assistant.message.model` で最も多いもの（`<synthetic>` は除く）                 |
| `title`         | 最後の `custom-title` → 最後の `ai-title` → 最初の人の入力、の順で採る           |
| 追加の候補      | `gitBranch`、`entrypoint`、`version`、`cost`（最後の `cost-state.totalCostUSD`） |

**Event**

| 元のレコード                                    | 写像                                                                               |
| ----------------------------------------------- | ---------------------------------------------------------------------------------- |
| `user` で content が文字列、または text         | `role=user`、`kind=message`（`isMeta` は `kind=meta`）                             |
| `user` の `tool_result`                         | `kind=tool_result`。`tool_use_id` で対応する `tool_use` を引き、`tool_name` を補う |
| `assistant` の `text` / `thinking` / `tool_use` | `kind=message` / `thinking` / `tool_call`。`tool_name` = `name`                    |
| `system`                                        | `kind=system`                                                                      |
| `attachment`                                    | `kind=attachment`（既定では隠す）                                                  |

- `ts` は `timestamp`。
- `tokens_in`/`tokens_out` は `usage` から取り、**`message.id` ごとに 1 回だけ数える**（同じ id の最後のレコードを採る）。キャッシュのトークンは別の欄に分ける。
- **取れないもの**:
  - 1 イベントあたりのコスト。セッション単位の `cost-state` しか無く、モデル別の累積だけ。
  - `ended_at` の明示的なレコード。
  - サブエージェント分が親の `cost-state` に含まれるかどうか（未確認）。

### アダプタ実装の注意

1. `projects/*/*.jsonl` は直下だけを列挙する。`subagents/**/agent-*.jsonl` は親セッションの子として別に扱い、`.meta.json` の `toolUseId` で親の Agent 呼び出しにつなぐ。`journal.jsonl`、`*.orphaned-*`、`*.superseded-*`、`memory/` は除外するか、別の扱いにする。
2. assistant の応答はブロック 1 個ごとに 1 行になっている。トークンを合計するときは `message.id`（または `requestId`）で重複を取り除く。そうしないと数倍に膨らむ。
3. 未知の `type` は捨てる。対象は `user`・`assistant`・`system` と、メタデータ用の `ai-title`・`custom-title`・`cost-state` だけに絞る。`api-request*` は大きくて本文と重複するので、パースせずに飛ばす。行の文字列に `"type":"api-request` が含まれるかで先に判定するのが速い。
4. cwd からディレクトリ名へのエンコードは一方向にしか使えない。`--project <path>` での絞り込みは「エンコードしたものを大文字小文字を区別せずに比較してディレクトリを絞る → 中のレコードの `cwd` で確かめる」の 2 段にする。
5. Windows では `cwd` が `C:\...` の形で、ドライブレターの大文字小文字が混じる。正規化してから比べる。
6. 1 行が約 1MB になりうるので、全文読み込みではなくストリームで読む。最終行が途中で切れているのは許容する。
7. 形式は内部仕様で、版ごとに種別が増える。今回だけでも `api-request-blob`、`atis-latch` など、既存スキルに無い種別が多数あった。フィールドは `.get` で読み、知らない値も通す。公式の Agent SDK に `listSessions` / `getSessionMessages`（TS）、`list_sessions`（Python）があり、仕様の参照先として使える。
8. 本文を表示・検索するときは秘密情報を出さない配慮が要る。マスクのオプションや、既定では本文を一部だけ表示するなど。

**既存資産との差分**

- `claude-logs-investigate/SKILL.md` に**書かれていないこと**:
  - `subagents/`（`.meta.json`、workflows）
  - `mcp-tasks/`、orphaned / superseded
  - `memory/`
  - ドライブレターの大文字小文字でディレクトリが分かれること
  - assistant が 1 ブロック 1 行に分かれていること
  - `cost-state`・`ai-title` などの新しい種別
  - `history.jsonl` と `stats-cache.json` はスイープされないこと
  - `sessions/` に増えたフィールド（`status`・`kind`・`updatedAt` など）
- 既存スキルに書かれている「`cleanupPeriodDays` 既定 30 日」「エンコードは非英数字を `-` に置換」は、公式とも実データとも合っている。
- `tools/coding-agent/ai-usage/ai_usage_core/collectors/claude_code.py` はトランスクリプトを読まない。statusLine フックが書く独自の JSONL から、レート制限の最新値（5h / 7d の `used_percentage`）を読むだけ。今回のアダプタと処理が重なる部分は無い。

### 根拠

- 公式（Explore the .claude directory）: https://code.claude.com/docs/en/claude-directory 。所在、保持、平文保存、`<project>` のエンコード規則、subagents / tool-results / orphaned の記載。リポジトリ内のスナップショット: `skills/plugins/cc-knowledge/skills/claude-code-docs/output/llms-full.txt`（17060 行目付近から）。
- 公式（settings の `cleanupPeriodDays`・`desktopSessionCleanupPeriodDays`）: 同じ `llms-full.txt` と `skills/plugins/cc-knowledge/skills/claude-settings/settings.md`。
- 公式（SDK の `listSessions`・`getSessionMessages`、`SDKCompactBoundaryMessage`）: `skills/plugins/cc-knowledge/skills/claude-agent-sdk/output/pages/agent-sdk/typescript.md`、`python.md`。
- 既存の資産: `skills/plugins/cc-knowledge/skills/claude-logs-investigate/SKILL.md`、`tools/coding-agent/ai-usage/ai_usage_core/collectors/claude_code.py`。
- 実データからの推定（公式に記載なし、バージョン依存で保証なし）: レコード種別とフィールド、1 ブロック 1 行の分割、`usage` の重複、`cost-state` の累積の意味、ドライブレターの大文字小文字問題、`.meta.json` と `journal.jsonl` の構造、`.last-cleanup`。

### 未解決・要追加確認

- **compact の表現**: 実データに 0 件。SDK のストリームでは `system/compact_boundary` と `compact_metadata{trigger, pre_tokens}`。トランスクリプト側も同じ形か（`compactMetadata`、`logicalParentUuid`、`isCompactSummary` の user レコード）は、`/compact` を 1 回実行して確かめる必要がある。
- **旧形式**: `summary` レコードと `progress` レコードは今の版で出ているか不明。旧版のファイルが残っていた場合に備え、未知の種別として許容する。
- サブエージェントのトークンやコストが親の `cost-state` に含まれるか。
- 長いパス（200 文字超など）でのディレクトリ名の切り詰めやハッシュ付与の有無。
- `cost-state.totalCostUSD` が `/resume` や fork のあとで累積し直されるか。同じ `message.id` で `usage` が違う 7 件の原因（ストリーミング途中の値か）。
- CLI だけで起動したとき（`entrypoint=cli`）にドライブレターが大文字になるかの再現確認。
- `teams/`、`debug/`、`session-env/` はこの PC では空で、中身の形式は未確認。

## Cursor（IDE と CLI `cursor-agent`/`agent`）

- 調査日: 2026-11-17。対象は Cursor IDE 3.30.14（`%LOCALAPPDATA%\Programs\cursor\resources\app\product.json`）と cursor-agent。cursor-agent は `%LOCALAPPDATA%\cursor-agent\versions\` にある最新の 2026.10.22-27dcf5f を対象にした。cursor-agent は Git Bash の PATH に無いので、バージョンはフォルダ名から推定した。知識スキルの help は 2026.07.08 時点のもの。
- この PC にあった件数: transcript jsonl 714 本、CLI chats 137 件（`store.db` があるのは 101 件）、IDE の composerHeaders 739 件。
- ローカルの保存形式について Cursor の公式文書（cursor.com/docs）には記載が見つからなかった。以下は**ほぼすべて実データからの推定で、バージョン依存・未保証**。forum とサードパーティ文書は傍証として「根拠」に分けて載せる。

### 所在

保存先は 3 系統ある。

| 系統                           | Windows 実パス                                                                                                                                  | POSIX/macOS（傍証）                                                                             | 用途                                           |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| A. transcript（IDE・CLI 共通） | `%USERPROFILE%\.cursor\projects\<enc-cwd>\agent-transcripts\<sessionId>\<sessionId>.jsonl`。サブエージェントは同じ場所の `subagents\<id>.jsonl` | `${CURSOR_CONFIG_DIR:-~/.cursor}/projects/...`                                                  | 会話本文とツール呼び出しの入力                 |
| B. CLI chats                   | `%USERPROFILE%\.cursor\chats\<md5(cwd)>\<chatId>\{meta.json, store.db[-wal,-shm], prompt_history.json}`                                         | `~/.cursor/chats/`（新しい版では `~/.config/cursor/chats/` という報告もある。この PC には無い） | CLI セッションの完全な状態（ツール結果を含む） |
| C. IDE SQLite                  | `%APPDATA%\Cursor\User\globalStorage\state.vscdb`（1.6GB、WAL あり）と `workspaceStorage\<32hex>\{state.vscdb, workspace.json}`                 | mac: `~/Library/Application Support/Cursor/User`、Linux: `~/.config/Cursor/User`                | IDE Composer/Agent の完全な状態                |

`projects\<enc-cwd>\` の下には、ほかに `terminals/`、`agent-tools/*.txt`、`uploads/`、`canvases/`、`mcps/`、`repo.json`（`{id}`）がある。

補助のデータ:

- `~/.cursor/ai-tracking/ai-code-tracking.db`（SQLite）: `ai_code_hashes`（model・conversationId・timestamp）、`scored_commits`、`conversation_summaries`（この PC では 0 件）など。
- `ide_state.json`、`agent-cli-state.json`（`{version, hasShown...}` だけで、ログではない）。
- `~/.cursor/agents/` と `~/.cursor/plans/` はこの PC では空だった。

### 形式とレコード構造

**A. transcript jsonl（最優先の情報源）**: 1 行が 1 JSON。レコード種別は次の 2 つだけ。

| 種別       | フィールド                                                                         | 備考                                                                    |
| ---------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| メッセージ | `role`（`user` か `assistant`）、`message.content[]`                               | content の要素は `{type:"text",text}` か `{type:"tool_use",name,input}` |
| ターン終端 | `type:"turn_ended"`、`status`（`success`/`error`/`aborted`）、`error`（str、任意） | ファイル末尾に来ることが多い                                            |

- 時刻・モデル・usage・tool_result・id・parent のフィールドは**どれも無い**。
- user の text は `<user_query>…</user_query>` で包まれ、`<timestamp>Weekday, Mon D, YYYY, H:MM AM (UTC+9)</timestamp>` が埋め込まれている（user 行の約 9 割）。ほかに `<attached_files>`、`<code_selection>`、`<manually_attached_skills>`、`<external_links>`、`<uploaded_documents>` などのタグがある。
- tool_use の name の例: Read、Grep、StrReplace、Shell、ReadFile、Glob、Write、ApplyPatch、CallDynamicTool（MCP）、Task、Subagent、TodoWrite、WebFetch、CreatePlan など。サブエージェントは `Task`/`Subagent` の input `{description,prompt,subagent_type,model?,readonly?,run_in_background?}` で起動される。ただし子の jsonl の id との対応は transcript からは取れない。

```json
{"role":"user","message":{"content":[{"type":"text","text":"<timestamp>Monday, Nov 16, 2026, 9:00 AM (UTC+9)</timestamp>\n<user_query>\n<text>\n</user_query>"}]}}
{"role":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"path":"<path>"}}]}}
{"type":"turn_ended","status":"success"}
```

**B. CLI `store.db`**

- `meta.json` は `{schemaVersion:1, createdAtMs, updatedAtMs, cwd, hasConversation, title?}`。
- `store.db` のテーブルは `meta(key,value)` と `blobs(id,data)` の 2 つ。
- `meta` は key `'0'` の 1 行だけで、値は hex エンコードした JSON。中身は `{agentId, latestRootBlobId, name, mode(default/search/auto-run/plan), approvalMode?, isRunEverything?, createdAt, lastUsedModel?, subagentInfo?{parentAgentId,rootParentAgentId,toolCallId,typeName}, blobEncryptionKey?}`。
- `blobs` は content-addressed で、`id = sha256(data)` を全件で確認した。
- root blob（`latestRootBlobId`）は protobuf。field 1（32 バイト、repeated）がメッセージ blob の id を**会話順に並べた列**になっている。
- メッセージ blob は JSON で、Vercel AI SDK に似た形。
  - 形: `{id?, role: system|user|assistant|tool, content: str|[...], providerOptions?{cursor:{requestId|modelProviderMessageId|highLevelToolCallResult|…}}}`
  - content の要素: `text`、`reasoning{text,signature}`、`redacted-reasoning{data}`、`tool-call{toolCallId,toolName,args}`、`tool-result{toolCallId,toolName,result,experimental_content}`
- メッセージ単位の時刻と usage は無い。
- blobs にはファイル内容のキャッシュ（JSON や生テキスト）も混在する。
- `prompt_history.json` は入力したプロンプト文字列の list。

**C. IDE `globalStorage/state.vscdb`**

- テーブル: `ItemTable`、`cursorDiskKV`（key TEXT、value BLOB）、`composerHeaders`、`remoteAgentHeaders`。
- `composerHeaders` の列: `composerId, workspaceId, createdAt, lastUpdatedAt, isArchived, isSubagent, recency, checkpointAt, value(JSON), subagentTypeName`。
  - value JSON の主なキー: name、subtitle、unifiedMode、workspaceIdentifier{id, uri{fsPath,path,scheme}}、contextUsagePercent、totalLinesAdded/Removed、filesChangedCount、trackedGitRepos など。
  - **セッション一覧を取るには最良の入口。**
- `cursorDiskKV` のキー接頭辞（件数）:
  - `agentKv:blob:<x>`（約 14 万）
  - `bubbleId:<composerId>:<bubbleId>`（5.1 万、旧形式）
  - `bubbleId:<composerId>:<x>:<bubbleId>`（新しめの行の大半が 4 分割）
  - `composerData:<composerId>`（824）
  - `composerConvHeaders:<composerId>:<chunk>`
  - `checkpointId:*`、`codeBlockPartialInlineDiffFates:*`、`ofsContent:*`、`inlineDiff:*`、`composer.content.<sha256>`
- `composerData`（`_v` は 13〜18）の主なキー:
  - `createdAt`、`lastUpdatedAt`、`name`、`status`、`unifiedMode`
  - `modelConfig{modelName,maxMode,selectedModels}`、`usageData`（空の {} が多い）
  - `contextTokensUsed/Limit`、`promptTokenBreakdown{totalUsedTokens,maxTokens,categories}`
  - `subComposerIds`、`subagentComposerIds`、`subagentInfo`、`workspaceIdentifier`
  - 秘密: `blobEncryptionKey`、`speculativeSummarizationEncryptionKey`
- バブルの並び順は形式で変わる。旧は `fullConversationHeadersOnly[{bubbleId,type,grouping,createdAt(ISO),startedAtMs,completedAtMs}]`、新（_v18 の一部）は `headerLog{chunkSize,chunkCount,count,generation}` で、本体は `composerConvHeaders:<id>:<chunk>`（同じ要素の JSON 配列）にある。
- bubble JSON の主なキー:
  - `type`（1=user、2=assistant）、`text`、`createdAt`（ISO8601Z）、`startedAtMs`、`completedAtMs`、`turnDurationMs`、`thinking`
  - `toolFormerData{tool,name,toolCallId,status(completed/loading/error/cancelled),params,rawArgs,result,additionalData,modelCallId,toolIndex,toolCallBinary}`
  - `tokenCount{inputTokens,outputTokens}`。ただし**全 56,345 件で 0 だった**。
  - `modelInfo{modelName}`（ごく一部）、`requestId`、`checkpointId`
  - ほかに大量の空配列フィールド
- `workspaceStorage/<hash>/state.vscdb` は ItemTable だけ。キーは `composer.composerData{selectedComposerIds,lastFocusedComposerIds}`、`aiService.prompts[{text,commandType}]`、`aiService.generations[{unixMs,generationUUID,type,textDescription}]`。旧版の名残で、本文の正本ではない。

### セッション⇔プロジェクト対応

- **transcript のフォルダ名 `<enc-cwd>`** は推定で `re.sub(r'[^A-Za-z0-9]+','-',cwd).strip('-')`。例: `C:\C\ai` → `c-C-ai`。
  - CLI 101 件中 84 件が完全一致し、残る 17 件はドライブ文字の大小だけが違った。**Windows では大文字小文字を無視して照合する必要がある。**
  - この変換は可逆ではない（`-` や `.` が区別できない）。cwd は B または C から取る。
- 数字だけの名前（13 桁のエポックミリ秒）や `empty-window` のフォルダは、フォルダを開いていないウィンドウ。composerHeaders.workspaceId と同じ値になる。
- **セッション ID の共通性**: transcript の `<sessionId>` は IDE の composerId（main 390 件、sub 196 件）か CLI の chatId（116 件）と一致した。どちらにも無いものが 8 件あった。transcript を軸にして、B か C で補完できる。
- CLI chats のフォルダ名は `md5(meta.cwd の UTF-8)` の hex で、137 件中 137 件一致した。
- IDE: `composerHeaders.workspaceId` は `value.workspaceIdentifier.id` と全件一致した。フォルダは `workspaceIdentifier.uri.fsPath`（739 件中 680 件にある）か、`workspaceStorage/<workspaceId>/workspace.json` の `{folder}` または `{workspace}`（URI）で引ける。workspaceId 56 種のうち 29 種は workspaceStorage に存在しない（削除済み、または数字 ID）。

### 読み取り安全性・保持期間・秘密情報

- **SQLite の開き方**
  - `mode=ro` で global・CLI・ai-tracking の各 DB を開けた。Cursor 起動中でも開け、journal_mode は wal だった。
  - `immutable=1` でも開けたが、WAL を読まないので**直近の書き込みが欠ける**。フォールバックとしてだけ使い、その場合は利用者に警告する。
  - global の DB は 1.6GB ある。`json_extract` を使った SQL 側での絞り込みと、`LIMIT`/`rowid` でのページングが必須。
- **書き込み中のファイル**: jsonl は追記中のことがある。最終行の JSON が壊れていたら捨てる。
- **保持期間**
  - `projects/.agent-data-cleanup-YYYY-MM-DD`（空ファイル）が 2026-08 からほぼ毎日作られており、Cursor が自動でクリーンアップしていると推定。どの基準で消すかは不明。
  - 実データの範囲: transcript 2026-03-10〜、IDE 2026-01-31〜、CLI chats 2026-07-09〜。
  - forum には「サイドバーが空でも transcript がディスクに残っていた」という報告がある。
- **秘密情報**
  - `blobEncryptionKey` と `speculativeSummarizationEncryptionKey`（store.db の meta、composerData）。出力から必ず除外する。
  - `ItemTable` の `secret:*` キー（19 件）。読まない。
  - tool-result、toolFormerData.result、bubble の text。シェル出力・ファイル内容・環境変数が入りうる。
  - blobs のファイル内容キャッシュ、`prompt_history.json`、`aiService.prompts`、`uploads/`、`terminals/`。
  - `meta.cwd` と URI に含まれるユーザー名。

### 正規化スキーマへの写像

| 正規化フィールド      | A transcript                                                                  | B CLI                                          | C IDE                                                                                     |
| --------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Session.id            | フォルダ名の uuid                                                             | chatId（フォルダ名）。agentId もある           | composerId                                                                                |
| tool                  | "cursor"。source=ide/cli は B か C のどちらに id があるかで判定               | cursor-cli                                     | cursor-ide                                                                                |
| project/cwd           | フォルダ名を大文字小文字無視で B/C と突き合わせる（可逆ではない）             | meta.json.cwd                                  | workspaceIdentifier.uri.fsPath または workspace.json                                      |
| started_at / ended_at | user の `<timestamp>` を解析（分単位・ローカル TZ 付き）。無ければ mtime      | meta.createdAtMs / updatedAtMs                 | composerHeaders.createdAt / lastUpdatedAt                                                 |
| model                 | 取れない（Task の input.model だけ）                                          | meta.lastUsedModel                             | modelConfig.modelName、bubble.modelInfo                                                   |
| title                 | 取れない                                                                      | meta.json.title / meta.name                    | composerHeaders.value.name                                                                |
| Event.ts              | user ターンだけ（assistant は直前の値を引き継ぐ）                             | 取れない（メッセージ単位では無い）             | bubble.createdAt / startedAtMs                                                            |
| role / kind           | role と content.type（text→message、tool_use→tool_call）、turn_ended→turn_end | role（tool→tool_result）、reasoning、tool-call | type 1/2。toolFormerData があれば tool_call と tool_result をまとめて扱う                 |
| tool_name             | tool_use.name                                                                 | toolName                                       | toolFormerData.name                                                                       |
| tokens_in/out・cost   | 取れない                                                                      | 取れない                                       | tokenCount は実質 0。セッション単位の contextTokensUsed だけ。**cost は全系統で取れない** |
| 親子関係              | `subagents/` に置かれていることから親を推定                                   | meta.subagentInfo.parentAgentId                | composerHeaders.isSubagent、subagentComposerIds                                           |

### アダプタ実装の注意

1. **既定の入力は A（transcript）にする。** IDE と CLI の両方を 1 つの形式で走査でき、標準ライブラリだけで扱える。B と C はセッションのメタデータ（cwd、title、model、時刻）と tool_result を補う任意の enrich として扱う。
2. **transcript の時刻**: user の `<timestamp>` を `%A, %b %d, %Y, %I:%M %p (UTC+N)` 相当で解析する。曜日・月名は英語固定なので、ロケールに依存しない自前のパーサにする。日の数字は 1 桁と 2 桁の両方がある。無い場合はファイルの mtime で代用する。
3. **ツール結果は A に無い。** 欲しければ B の tool-call/tool-result を toolCallId で、C の toolFormerData を使って結合する。A との対応は「同じツール名と引数の出現順」で取るしかない（サードパーティ deja の方式）。
4. **B（CLI store.db）の読み方**: meta の値は hex→JSON。会話順は root blob の protobuf field 1 を自前の最小 varint パーサで読む（約 20 行で書ける）。blobs を全件走査すると、ファイル内容キャッシュまで拾ってしまう。
5. **C（IDE）の読み方**
   - 一覧は `composerHeaders` テーブルから取る（古い版には無い可能性がある。`composer.composerHeaders.migratedToTable` フラグを確認する）。
   - バブルの順序は `fullConversationHeadersOnly`、`headerLog`+`composerConvHeaders`、bubbleId の前方一致の 3 段フォールバックで取る。
   - bubbleId キーには 3 分割と 4 分割が混在する。
   - value が NULL や非 JSON のこともある。
6. **パス照合**: Windows では `<enc-cwd>` を大文字小文字無視で照合する。cwd→enc の変換は一方向でしか使わない。
7. 出力・索引から `*EncryptionKey`、`secret:*`、`prompt_history` を必ず除外する。
8. `CURSOR_CONFIG_DIR` での上書きと、`~/.config/cursor/chats`（新しい版）も探索候補に入れる。

### 根拠

- **実データからの推定（この PC、2026-11-17）**: 上のパス、キー、件数、md5 と sha256 の一致、エンコード規則、ID の相互対応は、すべて読み取り専用（`mode=ro`）のスクリプトで確認した。
- **リポジトリ内**
  - `skills/plugins/ai-tools-knowledge/skills/cursor-cli-docs/output/help_result.yaml`: `--resume [chatId]`、`ls`、`resume`、`create-chat` があることだけ記載。保存先の記述は無い。
  - `skills/plugins/ai-tools-knowledge/skills/cursor-docs/output/llms.txt`: 保存先の記述は無い。関連は shared-transcripts と privacy の URL だけ。
  - `tools/coding-agent/ai-usage/ai_usage_core/collectors/cursor.py`: usage は TUI の `/usage` をスクレイプしており、ローカルログは使っていない。
- **forum（傍証）**
  - https://forum.cursor.com/t/chat-history-lost-for-one-project-only-other-projects-unaffected/161857/10 （`~/.cursor/projects/<project>/agent-transcripts/*.jsonl`）
  - https://forum.cursor.com/t/agents-sidebar-empty-222-transcripts-still-on-disk-windows/162757
  - https://forum.cursor.com/t/cursor-cli-past-chats-not-showing-up/152450 （CLI は `~/.cursor/chats`）
- **サードパーティ（未保証）**
  - https://vshulcz.github.io/deja-vu/registry/cursor （transcript に時刻が無いこと、`<timestamp>` の解析、chats が md5(cwd)、`CURSOR_CONFIG_DIR`、各 OS の User ルート）
  - https://agentgrep.org/backends/cursor-cli （meta が hex JSON、`~/.config/cursor/chats`）

### 未解決・要追加確認

- 自動クリーンアップ（`.agent-data-cleanup-*`）が何を基準に、何日で、どの系統（A/B/C）を消すのか。
- transcript の `subagents/<id>` を親の Task/Subagent 呼び出しに結び付ける方法。C の subagentComposerIds、B の subagentInfo.toolCallId で取れる見込みだが未検証。
- `agentKv:blob:*`（約 14 万件）の中身（B と同じ blob 方式で IDE 側の会話状態を持つ可能性がある）と、`bubbleId` が 4 分割のときの第 3 要素の意味。
- tokenCount が 0 なのは仕様か（サーバー側でしか集計しない？）。usage と cost のローカルでの所在は、ai-tracking.db の model 列以外には見つかっていない。
- macOS/Linux での実パス（`~/.cursor` か `~/.config/cursor` か）と、CLI の版ごとの移行。この PC の CLI は `~/.cursor/chats` だけだった。
- `blobEncryptionKey` がある store.db で、一部の blob が暗号化されているか。今回の範囲ではメッセージは平文 JSON で読めた。

## Cline（VS Code 拡張・Cline CLI）

- 調査日: 2026-11-17
- 確認したバージョン
  - Cline CLI: 3.0.46（`cline --version`）
  - VS Code 拡張: 4.0.11（`task_metadata.json` の `environment_history[].cline_version` の値、VS Code 1.130.0）
- 実データの量: 拡張のタスクが 2 件、CLI のセッションが 49 件（`sessions.db` の 49 行と一致）
- 最大の発見: 保存形式は 2 系統ある。CLI と新しい拡張は同じ SDK（`@cline/core`）の「セッション形式」で `~/.cline/data/sessions/` に保存する。古い拡張のタスクは「レガシーのタスク形式」で `globalStorage` に残る。どちらも読むアダプタが必要。

### 所在

| 系統                                                   | Windows の実パス                                                                                                              | POSIX / macOS                                                                                                                                                                                          |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A. SDK セッション（CLI と新しい拡張。`source` で区別） | `%USERPROFILE%\.cline\data\sessions\<sid>\`、`%USERPROFILE%\.cline\data\db\sessions.db`                                       | `~/.cline/data/...`（`CLINE_DATA_DIR` で丸ごと差し替え可能。公式）                                                                                                                                     |
| B. レガシーの拡張タスク                                | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\{state\taskHistory.json, tasks\<taskId>\, checkpoints\<hash>\.git}` | macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/`、Linux: `~/.config/Code/...`（VS Code の慣例。推定）。Insiders・VSCodium・Cursor などでは `Code` の部分が変わる |
| B'. 旧 CLI・JetBrains                                  | `~/.cline/data/tasks/<taskId>/`、`tasks/taskHistory.json`                                                                     | 公式の Prompt Storage 文書と cline リポジトリの `.clinerules/storage.md` に記載がある。この PC には無い                                                                                                |

- 公式文書（hub-spoke ページ）は `sessions.db` を `sessions/` の直下と書いている。実際は `data/db/sessions.db` にあり、SDK のソース（`resolveDbDataDir()` が `<data>/db`）とも一致する。文書の方が古い。
- 補助ファイル（会話ログではない）
  - `data/logs/cline.log`: pino 形式の JSON 行
  - `data/logs/hooks.jsonl`: キーは `hookName, pid, reason, sessionId, source, ts`
  - `data/logs/hub-daemon.log`: 実測 360MB。読まない
  - `data/cache/user_input_history.jsonl`: キーは `{prompt, ts}`
  - `data/workspaces/<8 桁 hex>/workspaceState.json`: 中身はトグルだけで会話は無い
  - `data/db/{cron,teams}.db`

### 形式とレコード構造

**A. SDK セッション（JSON。jsonl ではない）**

`sessions/<sid>/` には `<sid>.json`（メタデータ）と `<sid>.messages.json`（会話）の 2 ファイルが必ずある。`<sid>` は `<epoch ミリ秒>_<英数 5 文字>`。

`<sid>.json`（`version: 1`）の主なフィールド:

| フィールド                                                                        | 型・値の例                                                                  | 備考                                                                              |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `session_id`                                                                      | str                                                                         | ディレクトリ名と同じ                                                              |
| `source`                                                                          | `"cli"`                                                                     | SDK の enum は `core/cli/subagent/desktop/kanban/vscode/jetbrains/neovim/unknown` |
| `started_at`, `ended_at`                                                          | ISO8601 で末尾が `Z`                                                        |                                                                                   |
| `status`, `exit_code`                                                             | `completed / failed / cancelled`                                            |                                                                                   |
| `provider`, `model`                                                               | str                                                                         |                                                                                   |
| `cwd`, `workspace_root`                                                           | 絶対パス                                                                    | 一致は 29 件、不一致は 20 件                                                      |
| `prompt`                                                                          | 最初の依頼の本文                                                            | 機密                                                                              |
| `interactive`, `enable_tools`, `enable_spawn`, `enable_teams`, `team_name`, `pid` |                                                                             |                                                                                   |
| `messages_path`                                                                   | 絶対パス                                                                    |                                                                                   |
| `metadata.title`                                                                  | str                                                                         |                                                                                   |
| `metadata.usage` / `metadata.aggregateUsage`                                      | `{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, totalCost}` | aggregate はサブエージェント込み（推定）                                          |
| `metadata.totalCost`, `metadata.aggregatedAgentsCost`                             | float                                                                       |                                                                                   |
| `metadata.git`                                                                    | `{url, branch}`                                                             |                                                                                   |
| `metadata.checkpoint`                                                             | `{latest, history[]}`                                                       |                                                                                   |
| `metadata.systemPrompt`, `metadata.terminal_marker*`, `metadata.mode`             |                                                                             | 一部のレコードにだけある                                                          |

- `metadata` に何のキーがあるかは版ごとにかなり違う。実測で 11 通りあった。

`<sid>.messages.json` は `{version:1, updated_at, agent:"lead", sessionId, system_prompt, messages:[...]}` という形。`messages[]` は Anthropic の MessageParam 形式を拡張したもの。

- ユーザー（user）
  - キーは `{id, role:"user", ts(ms), content[]}`
  - 中身は `text` ブロック、または `tool_result{tool_use_id, name, content(str か配列), is_error?}`
- アシスタント（assistant）
  - キーは `{id, role:"assistant", ts, content[], metrics{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, cost}, modelInfo{id, provider}, metadata?{invalidToolCalls[]}}`
  - 中身は `thinking`・`text`・`tool_use{id, name, input}` ブロック
- 実測の件数
  - ブロック: tool_use 1014、tool_result 1010、thinking 681、text 601
  - content が文字列のメッセージ: 1 件
  - ツール名: `run_commands, editor, read_files, search_codebase, fetch_web_content, ask_question, skills` など
  - `ts` が無いメッセージ: 1 件
- 公式の契約文書（`messages-contract-v1.md`）は、これを「正規の再生・エクスポート用の成果物」と位置づけている。

`sessions.db` の `sessions` テーブルは JSON の索引にあたる。列は次のとおり。

- JSON と同じ値: `session_id, source, started_at, ended_at, status, provider, model, cwd, workspace_root, prompt, metadata_json, messages_path, updated_at`
- 親子関係: `parent_session_id, parent_agent_id, agent_id, conversation_id, is_subagent`
- その他: `transcript_path, hook_path`

ほかに `subagent_spawn_queue`、`schedules`、`schedule_executions(tokens_used, cost_usd)` のテーブルがある。この PC では親子関係の列はすべて空、`transcript_path` も空だった。

最小の例（値は架空）:

```json
{"id":"m2","role":"assistant","ts":1780000000000,"modelInfo":{"id":"<model>","provider":"<prov>"},
 "metrics":{"inputTokens":10,"outputTokens":5,"cacheReadTokens":0,"cacheWriteTokens":0,"cost":0.001},
 "content":[{"type":"thinking","thinking":"<text>"},{"type":"tool_use","id":"t1","name":"read_files","input":{"files":[{"path":"<p>"}]}}]}
{"id":"m3","role":"user","ts":1780000000500,"content":[{"type":"tool_result","tool_use_id":"t1","name":"read_files","content":"<text>"}]}
```

**B. レガシーの拡張タスク（JSON 配列）**

`<taskId>` は epoch ミリ秒。ファイルは次のとおり。

- `state/taskHistory.json`: 一覧。要素は `{id, ulid, ts, task, tokensIn, tokensOut, cacheWrites, cacheReads, totalCost, size, cwdOnTaskInitialization, modelId, isFavorited}`
- `tasks/<id>/api_conversation_history.json`: MessageParam の配列。各要素は `{role, content[], ts}`。assistant にはさらに `modelInfo{providerId, modelId, mode}` と `metrics{tokens{prompt, completion, cached}, cost}` が付く。ブロックは `text`、`text` に `call_id` や `reasoning_details` が付いたもの、`thinking{thinking, signature, summary}`。この版では `tool_use` ブロックを確認できなかった。ツール呼び出しは text に埋め込まれる XML 形式か `call_id` 付きで、実データからの推定。
- `tasks/<id>/ui_messages.json`: 配列。要素は `{ts, type:"say"|"ask", say|ask, text?, partial?, conversationHistoryIndex, modelInfo?, images?, files?, lastCheckpointHash?, isCheckpointCheckedOut?}`
  - 実測の `say` 種別: `task, text, tool, api_req_started, task_progress, checkpoint_created, conditional_rules_applied, error`
  - 実測の `ask` 種別: `resume_task`
  - `say:"api_req_started"` の `text` は JSON 文字列で、`{request, tokensIn, tokensOut, cacheWrites, cacheReads, cost}` を持つ。リクエストごとのトークンとコストはここにある。
  - `say:"tool"` の `text` は JSON 文字列で、`{tool:"readFile"|"listFilesTopLevel"|"listFilesRecursive"|"searchFiles"|..., path, content, ...}` を持つ。
- `tasks/<id>/task_metadata.json`: `{files_in_context[{path, record_state, record_source, cline_read_date, cline_edit_date, user_edit_date}], model_usage[{ts, model_id, model_provider_id, mode}], environment_history[{ts, os_name, os_version, os_arch, host_name, host_version, cline_version}]}`
- `focus_chain_taskid_<id>.md`

```json
{
  "ts": 1780000000000,
  "type": "say",
  "say": "api_req_started",
  "conversationHistoryIndex": 0,
  "text": "{\"request\":\"<text>\",\"tokensIn\":100,\"tokensOut\":20,\"cacheWrites\":0,\"cacheReads\":0,\"cost\":0.0}"
}
```

### セッション⇔プロジェクト対応

- A（SDK セッション）: `cwd` と `workspace_root` が絶対パスで直接入っている。パスのエンコード規則は無い。`metadata.git.url/branch` も使える。
- B（レガシー）: `taskHistory.json` の `cwdOnTaskInitialization` が絶対パス。SDK のソースもこれを `cwd` と `workspaceRoot` の両方に写している。
- 対応付けに使えないもの
  - `data/workspaces/<8 桁 hex>/`: 中身はトグルとマイグレーション版だけ
  - `checkpoints/<10 桁の数字>/`: パスのハッシュと推定する。中身は shadow git
- Windows ではドライブレターの大小（`c:\` と `C:\`）が混在する。比較の前に正規化する。

### 読み取り安全性・保持期間・秘密情報

- `sessions.db` は WAL モード。`mode=ro` で開けた。`immutable=1` でも開けたが、そのときは WAL を読まない。`cron.db` には 1.2MB の未チェックポイントの WAL があるので、`immutable` だと最新を取りこぼす。`mode=ro` を優先し、失敗したときだけ `immutable` に落とし、その場合は「不完全」と明示する。
- JSON は書き込み中に丸ごと書き換えられる（推定）。JSON の読み込みに失敗したら 1 回だけ再試行し、ダメならスキップする。`status` が `running` のように終わっていないセッションは `ended_at` が無いか古い可能性がある。
- 削除・保持
  - 自動ローテーションや保持期間の公式記載は見つからなかった。
  - 手動の管理は、CLI なら `cline history`、拡張なら UI のタスク削除。
  - SDK にはコンパクションの成果物のパス（`sessionCompactionPath`）がある。この PC ではコンパクションのファイルを確認できていない。
  - 拡張から `~/.cline/data` へのマイグレーションでは VS Code 側を消さない（ソースのコメント）。
- 秘密情報
  - `data/secrets.json`（キー 4 件）と `data/settings/providers.json` は API キーなので絶対に読まない。
  - `globalState.json` の `openAiHeaders` にも認証ヘッダが入りうる。
  - 会話本文、`prompt`、`system_prompt`、tool_result（ファイル内容・コマンド出力）、`ui_messages` の `request`/`content`、`user_input_history.jsonl`、`files_in_context.path`、`metadata.git.url` も注意が要る。
  - `cline.log` と `environment_history` にはホスト名が入る。

### 正規化スキーマへの写像

| 正規化フィールド | A（SDK セッション）                                                                                            | B（レガシー）                                                                     |
| ---------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Session.id       | `session_id`                                                                                                   | `taskHistory.id`（= ディレクトリ名）                                              |
| tool             | `"cline"`（`source` は副属性。`cli` / `vscode` など）                                                          | `"cline"`（`source` は `vscode-legacy`）                                          |
| project/cwd      | `cwd`（`workspace_root` も併記）                                                                               | `cwdOnTaskInitialization`                                                         |
| started_at       | `started_at`                                                                                                   | `taskHistory.ts` か id の epoch。最初の ui `ts` の方が確実                        |
| ended_at         | `ended_at`                                                                                                     | 取れない。最後の ui `ts` で代用                                                   |
| model            | `model`                                                                                                        | `modelId`、または `model_usage[-1].model_id`                                      |
| title            | `metadata.title`、無ければ `prompt` の先頭                                                                     | `task` の先頭                                                                     |
| Event.ts         | `messages[].ts`（ms）                                                                                          | `api_history[].ts` / `ui[].ts`                                                    |
| role / kind      | `role` とブロック種別で決める（text→message、thinking→reasoning、tool_use→tool_call、tool_result→tool_result） | `api_history` の role と text。tool は `ui say:"tool"` から                       |
| tool_name        | `tool_use.name` / `tool_result.name`                                                                           | `ui say:"tool"` の `text.tool`                                                    |
| tokens_in / out  | `metrics.inputTokens/outputTokens`（キャッシュ分も取れる）                                                     | `ui api_req_started` の `tokensIn/out`、または `metrics.tokens.prompt/completion` |
| cost             | `metrics.cost`（合計は `metadata.totalCost`）                                                                  | `api_req_started.cost`（合計は `taskHistory.totalCost`）                          |

取れないフィールドと注意点:

- B は `ended_at` と明示のタイトルが無い。
- B では tool_call と tool_result の厳密な ID 対応が取りにくい。
- A では、サブエージェントの親子関係が DB の列にしか無い（このデータでは空）。
- この版の B では `cost` が整数の 0 で、実質意味がない。

### アダプタ実装の注意

1. 2 系統を別アダプタにする（`cline-sessions` と `cline-legacy`）。新しい拡張は A に書く。A の `source` に `vscode` があり、B と同じタスクがマイグレーションで重複する可能性がある。B の id と A の id／metadata の `legacyTask`・`migratedFromLegacyTask` で重複を除く（ソースからの推定）。
2. ルートの解決順は「`CLINE_DATA_DIR` → `~/.cline/data`」。B は VS Code 系列ごとの `globalStorage/saoudrizwan.claude-dev` を候補として列挙する。旧 CLI の `~/.cline/data/tasks/` も B 形式で読む。
3. A の一覧は `sessions.db` があればそれを使い、無いか開けなければ `sessions/*/*.json` を走査する。この PC では両者が完全に一致した。ただし `.json` の方がフィールドは豊富。
4. JSON の全体読み込みが必要になる（数百 KB 程度。jsonl ではない）。ストリーミングは不要。`hub-daemon.log` のような巨大ログは対象外にする。
5. `content` が文字列の場合、`ts` が無い場合、`metadata` のキー欠落を許容する。`tool_result.content` は文字列か配列。
6. A では、子エージェントの messages が同じ root ディレクトリに別の stem（`childArtifactFileStem`）で出る可能性がある（ソースからの推定）。`*.messages.json` をすべて拾い、`agent` フィールドで区別する。
7. B の `ui_messages` にある `partial: true` は表示の途中状態なので重複扱いにする。`api_req_started.text` は JSON の二重エンコード。
8. 秘密のファイル（`secrets.json`、`settings/providers.json`）は glob の対象から明示的に除外する。

### 根拠

- 公式文書（リポジトリ内のスナップショット: `skills/plugins/ai-tools-knowledge/skills/cline-docs/output/llms-full.txt`）
  - https://docs.cline.bot/getting-started/config: `~/.cline/data` のレイアウト、`CLINE_DATA_DIR`
  - https://docs.cline.bot/sdk/architecture/hub-spoke: `sessions.db` は SQLite の索引で、JSON が正本
  - https://docs.cline.bot/enterprise-solutions/monitoring/prompt-storage: `~/.cline/data/tasks/<id>/api_conversation_history.json` は MessageParam 形式
- `skills/plugins/ai-tools-knowledge/skills/cline-cli-docs/output/help_result.yaml`: `history` サブコマンド
- 公式のソース（cline/cline、grep.app で取得）
  - https://github.com/cline/cline/blob/main/sdk/packages/core/docs/messages-contract-v1.md
  - .../sdk/packages/core/src/services/session-artifacts.ts
  - .../sdk/packages/shared/src/storage/paths.ts
  - .../sdk/packages/core/src/types/common.ts（`SessionSource`）
  - .../apps/vscode/src/hosts/vscode/vscode-to-file-migration.ts（taskHistory は未移行で、VS Code では globalStorage のまま）
  - .../apps/vscode/src/sdk/sdk-task-history.ts（`cwdOnTaskInitialization` を cwd に写す）
  - .../.clinerules/storage.md
- `tools/coding-agent/ai-usage/README.md`: Cline の使用量の収集は見送り（API ベース）。ローカルログの知見は無い。
- 実データからの推定（版依存で保証なし）: フィールド表、`say` の種別、`metrics` の形、件数、DB の列が空であること、WAL の挙動、`workspaces/` や `checkpoints/` の中身。

### 未解決・要追加確認

- 新しい拡張（SDK 版）が書いた `source:"vscode"` のセッションの実物を、この PC では確認できていない。どの拡張バージョンから A に書くのかも分からない。
- サブエージェント・チームの実データが無い。子の `.messages.json` の命名、`parent_session_id` の値、`aggregateUsage` との関係が未確認。
- コンパクション後の成果物（`sessionCompactionPath`）のファイル名と形式、`messages.json` 内での要約の表現が未確認。
- レガシーの `ui_messages` について、今回見えなかった種別（`deleted_api_reqs`、`completion_result`、`command` など）と、`conversationHistoryDeletedRange`（コンテキスト切り詰め）の扱い。
- レガシー版で native tool calling を有効にしたとき、`api_conversation_history` に `tool_use` ブロックが出るか（公式の例には `tool_use` がある）。
- 保持期間・自動削除の公式仕様。`cline history` の削除が JSON と DB の両方を消すか。
- macOS と Linux の実パス（VS Code の globalStorage）の実機確認。

## Kilo Code

- 調査日: 2026-11-17
- 確認したバージョン:
  - VS Code 拡張 `kilocode.kilo-code-7.8.27-win32-x64`
  - PATH 上の `kilo` CLI: 7.6.2（pnpm global）
  - DB 内 `session.version` の値: 7.5.6〜7.8.27 が混在
  - DB の最新 migration: `20261028192305_kilocode_continuation_intent`
- 結論:
  - **現行の Kilo（CLI/TUI と新 VS Code 拡張の両方）は、ローカル履歴を `kilo.db`（SQLite、WAL）だけに保存している。**
  - 拡張は同梱の `kilo serve`（log に `version=7.8.27 command=serve`）を起動し、その経由で同じ DB に書く。
  - `%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\` は**空**（ファイル 0 件）。旧 Cline 系の `tasks/` 形式はこの環境には無い。

### 所在

| 対象                                                                                            | Windows                                                                                                      | macOS/Linux                                                                                          | 根拠                                               |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| DB（正本）                                                                                      | `%USERPROFILE%\.local\share\kilo\kilo.db`（`-wal`・`-shm` 付き）                                             | `~/.local/share/kilo/kilo.db`                                                                        | 公式                                               |
| 上書き                                                                                          | `KILO_DB`（相対パスはデータディレクトリ基準、`:memory:` も可）、`XDG_DATA_HOME`、dev チャネル                | 同じ                                                                                                 | 公式。確実なのは `kilo db path`                    |
| VS Code Remote SSH                                                                              | リモート側の `~/.local/share/kilo/kilo.db`                                                                   | 同じ                                                                                                 | 公式                                               |
| `storage/session_diff/<sessionID>.json`                                                         | 同じデータディレクトリの下                                                                                   | 同じ                                                                                                 | 公式（「session diffs はまだ JSON」）              |
| `storage/session_diff_base/`、`session_pr_link_recorded/`、`wakeup/`、`migration`（中身は `2`） | 同じ                                                                                                         | 同じ                                                                                                 | 実データからの推定                                 |
| `log/`                                                                                          | `YYYY-MM-DDTHHMMSS.log`（起動ごとに 1 つ）、`daemon.log`、`opencode.log`、`background-process/scope-<hash>/` | 同じ                                                                                                 | 実データからの推定（daemon.log は公式）            |
| `tool-output/`                                                                                  | 長すぎて切り詰めたツール出力の退避先（今回は空）                                                             | 同じ                                                                                                 | 実データからの推定                                 |
| `snapshot/<project-id>/<worktree-hash>/`                                                        | チェックポイント用の bare git                                                                                | 同じ                                                                                                 | 公式                                               |
| `worktree-pool/`、`repos/`                                                                      | Agent Manager の worktree、管理対象 repo のキャッシュ                                                        | 同じ                                                                                                 | 推定（`repos/` は公式）                            |
| `auth.json`、`telemetry-id`                                                                     | 認証情報・テレメトリ ID                                                                                      | 同じ                                                                                                 | **読まないこと**                                   |
| 旧 VS Code 拡張（Cline 系）                                                                     | `%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\`                                                      | `~/Library/Application Support/Code/User/globalStorage/...`、`~/.config/Code/User/globalStorage/...` | 公式には settings の所在だけ記載。今回の環境では空 |

### 形式とレコード構造

kilo.db は opencode 由来の Drizzle スキーマ。時刻はすべて **epoch ミリ秒**の integer。テーブルごとの件数（実データ）:

- session 757、message 19,645、part 104,573、event 495,534
- project 27、project_directory 38、todo 1,317
- kilo_board 399、kilo_board_message 559
- session_message・session_input・workspace・session_share・session_context_epoch は 0 件

**session**（列で持つ。JSON ではない）

| 列                                                                                             | 内容                                                            |
| ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `id`                                                                                           | `ses_` + 26 文字。**新しいものほど辞書順で小さい（降順 ID）**   |
| `project_id`                                                                                   | `project.id` への参照                                           |
| `parent_id`                                                                                    | サブエージェントのとき親セッション。313 件が非 NULL             |
| `directory`                                                                                    | 作業ディレクトリ。`C:/x/y` 形式（スラッシュ区切り）             |
| `path`                                                                                         | ワークツリー内の相対パス（空のこともある）                      |
| `slug`、`title`、`version`、`agent`                                                            | `agent` は `code` / `explore` / `general` など                  |
| `model`                                                                                        | JSON 文字列 `{"id","providerID","variant"}`                     |
| `cost`（REAL）                                                                                 | セッション累計のコスト                                          |
| `tokens_input`、`tokens_output`、`tokens_reasoning`、`tokens_cache_read`、`tokens_cache_write` | セッション累計のトークン                                        |
| `summary_additions`、`summary_deletions`、`summary_files`、`summary_diffs`                     | 変更行数・ファイル数・差分                                      |
| `metadata`                                                                                     | JSON。キーは `kilocode.sandbox` だけ                            |
| `permission`                                                                                   | JSON 配列 `[{permission, pattern, action}]`。子セッションに付く |
| `revert`、`share_url`                                                                          |                                                                 |
| `time_created`、`time_updated`、`time_compacting`、`time_archived`                             |                                                                 |

**message**: 列は `id`（`msg_`、昇順）、`session_id`、`time_created`、`time_updated`、`data`（JSON）。`data` の中に `id` と `sessionID` は**含まれない**。

| `data` のキー                                                                | user                                                        | assistant                                          |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------- |
| `role`                                                                       | `"user"`                                                    | `"assistant"`                                      |
| `time.created` / `time.completed`                                            | ○ / -                                                       | ○ / ○                                              |
| モデル                                                                       | `model{providerID, modelID, variant}`                       | `providerID`、`modelID`、`variant`（トップレベル） |
| `agent` / `mode`                                                             | ○                                                           | ○                                                  |
| `parentID`                                                                   | -                                                           | 対応する user メッセージの ID                      |
| `path{cwd, root}`                                                            | -                                                           | ○                                                  |
| `tokens{input, output, reasoning, total, cache{read, write}}`、`cost`        | -                                                           | ○（`cost` は int 0 か real）                       |
| `finish`                                                                     | -                                                           | `tool-calls` / `stop`                              |
| `error{name, data}`                                                          | -                                                           | 任意（`APIError`、`MessageAbortedError`）          |
| `summary{diffs[]}`                                                           | 任意（`file`、`patch`、`additions`、`deletions`、`status`） | -                                                  |
| `editorContext{activeFile, openTabs[], visibleFiles[], shell}`、`tools{...}` | 任意（VS Code 経由のとき）                                  | -                                                  |

**part**: 列は `id`（`prt_`、昇順）、`message_id`、`session_id`、時刻、`data`（JSON）。`data.type` で種類を分ける。

| type（件数）            | 主なフィールド                                                                                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text`（3,887）         | `text`、`synthetic?`、`ignored?`、`time{start, end}`、`metadata.openai.*`                                                                                                 |
| `reasoning`（22,356）   | `text`、`time`、`metadata.openai.*`（暗号化された推論の可能性）                                                                                                           |
| `tool`（37,677）        | `tool`（read/bash/grep/edit/task/board_post など）、`callID`、`state{status: completed/error/running, input{...}, output, title, error, metadata{...}, time{start, end}}` |
| `step-start`（18,604）  | `snapshot?`、`time.start`                                                                                                                                                 |
| `step-finish`（18,522） | `reason`、`cost`、`tokens{...}`、`time{start, end, elapsed}`、`metrics{generation, source}`、`snapshot?`                                                                  |
| `patch`（3,525）        | `hash`、`files[]`                                                                                                                                                         |
| `file`（2）             | `filename`、`mime`、`url`（data URL がありうる）                                                                                                                          |

- `tool` part は呼び出しと結果を **1 つのレコードに同居**させている（`input` と `output` が同じ part の中にある）。
- `task` ツールの `state.metadata.sessionId` が子セッションの ID を指す（326 件中 324 件で `session.parent_id` と一致）。
- 切り詰めた出力は `state.metadata.outputPath`（`tool-output\...` を指す Windows 区切りのパス）に退避される。

**event**: `aggregate_id` は `ses_*`。`type` は `message.part.updated.1`、`message.updated.1`、`session.updated.1`、`session.created.1`、`message.part.removed.1`、`message.removed.1`。`data` には `info`（`id` や `sessionID` を含む完全なオブジェクト）が入る。同期とイベントソーシング用のログで、更新のたびに積み上がる（part 更新だけで 37 万件）。**正本は session/message/part テーブルで、event は使わない**（推定）。

**kilo_board / kilo_board_message**: マルチエージェントの掲示板。`type` は ASK/INFO/RESULT/HOLD/VETO、`body` は平文、`sender_session_id`、`recipient`（多くは `ses_*`）。

最小の例（値は架空）:

```json
// message.data (assistant)
{"role":"assistant","parentID":"msg_<id>","agent":"code","mode":"code","providerID":"openai","modelID":"<model>","variant":"high","path":{"cwd":"C:/<dir>","root":"C:/<dir>"},"time":{"created":1790000000000,"completed":1790000005000},"tokens":{"input":1000,"output":50,"reasoning":10,"total":1060,"cache":{"read":0,"write":0}},"cost":0,"finish":"tool-calls"}
// part.data (tool)
{"type":"tool","tool":"read","callID":"<id>","state":{"status":"completed","input":{"filePath":"<path>"},"output":"<text>","title":"<t>","metadata":{"truncated":false},"time":{"start":1790000001000,"end":1790000001200}}}
// part.data (step-finish)
{"type":"step-finish","reason":"stop","cost":0.0012,"tokens":{"input":1000,"output":50,"reasoning":0,"total":1050,"cache":{"read":800,"write":0}},"time":{"start":0,"end":0,"elapsed":0}}
```

**storage/\*.json**:

- `session_diff/ses_*.json` は配列 `[{file, patch, additions, deletions, status}]`。
- `session_pr_link_recorded/*` は `{link}`。
- これらは補助データで、会話本体は入っていない。

### セッション⇔プロジェクト対応

- `session.project_id` は `project.id` を参照する。
  - git 管理下では `project.id` が 40 桁の hex。opencode の実装では **ルートコミットの SHA**（推定）。
  - git 管理外では `id='global'`、`worktree='/'`。
- 対応の決め方:
  - `project.worktree` はリポジトリのルート（`C:/x/y` 形式）。
  - 実際の cwd は **`session.directory`** を使う（757 件中 730 件が worktree と一致。不一致の 26 件は global、1 件はサブディレクトリ）。
  - `project_directory(project_id, directory, strategy='git_worktree')` には worktree の別ディレクトリが入る。
- パスのエンコードやハッシュ化は無く、生のパスがそのまま入る。区切りは `/`、ドライブ文字付き。照合するときは大文字小文字と区切りの正規化が必要。
- `message.data.path.cwd` / `path.root` でも cwd が取れる。

### 読み取り安全性・保持期間・秘密情報

- **読み取り安全性**
  - `file:///C:/Users/<u>/.local/share/kilo/kilo.db?mode=ro`（uri=True）で、Kilo の起動中（WAL・shm あり）に問題なく開けた。`immutable=1` は不要だったので試していない。
  - 公式に記載された pragma: WAL、`synchronous=normal`、`busy_timeout` 5 秒、passive checkpoint。
  - immutable=1 を使うと WAL 内の未チェックポイント分が見えない（今回の WAL は約 7MB）ので、使うのは最後の手段にする。
  - `kilo db` は書き込みもできるため使わない。公式も `sqlite3 -readonly` を推奨している。
  - DB は 2.2GB ある。`json_extract` での全件走査は重い。既存インデックス（`message_session_time_created_id_idx`、`part_session_idx`、`part_session_step_finish_idx`）に乗るクエリにする。
- **保持期間**
  - DB の自動削除は見当たらない（未確認）。削除は UI か `kilo session delete` で、FK の CASCADE により message・part・todo も消える。
  - revert 後に新しいメッセージを送ると、巻き戻した分が物理削除される（公式）。
  - snapshot は毎時 `git gc --prune=7.days`（公式）。
  - `log/` は直近 10 件前後の起動ログが残る（推定）。`tool-output/` も空だったので掃除されていると推定。
- **秘密情報が入りうる場所**
  - `account` / `control_account`（`access_token`、`refresh_token`、`email`）
  - `credential.value`
  - `session_share.secret`
  - `auth.json`、`log/daemon.log`、`daemon.json`
  - 本文系: `part.text`、`state.input.command` / `body` / `prompt`、`state.output`、`state.metadata.output` / `diff` / `preview`、`file.url`（data URL）、`message.summary.diffs[].patch`、`editorContext`
  - `kilo_board_message.body`、`todo.content`、`session.title`、`directory`
  - **アダプタは session / message / part / project 以外のテーブルを SELECT しないこと。**

### 正規化スキーマへの写像

| 正規化                | 写像元                                                                                                                                                                                                              |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Session.id            | `session.id`                                                                                                                                                                                                        |
| tool                  | 固定値 `kilo`（`version` 列も付けられる）                                                                                                                                                                           |
| project/cwd           | `session.directory`。repo のルートは `project.worktree`                                                                                                                                                             |
| started_at / ended_at | `session.time_created` / `time_updated`。ended_at は近似値で、`max(message.time.completed)` の方が正確                                                                                                              |
| model                 | `session.model` の JSON の `id` / `providerID`。メッセージ単位なら assistant の `modelID`                                                                                                                           |
| title                 | `session.title`                                                                                                                                                                                                     |
| parent                | `session.parent_id`（正規化スキーマへの追加を推奨）                                                                                                                                                                 |
| Event.ts              | part の `time.start`、無ければ `part.time_created`。message は `time.created`                                                                                                                                       |
| role                  | `message.data.role`                                                                                                                                                                                                 |
| kind                  | `text` は message。`reasoning` は reasoning。`tool` は tool_call と tool_result の **2 つのイベントに分割**するか 1 つにまとめる。`step-*` と `patch` は捨てるかメタ扱い。`text.synthetic=true` は system/synthetic |
| tool_name             | `part.data.tool`                                                                                                                                                                                                    |
| text                  | `text.text`。tool なら `state.input` / `state.output`                                                                                                                                                               |
| tokens_in / out、cost | assistant メッセージの `tokens.*` と `cost`（step-finish の合計と一致: 300 件中 tokens 298 件、cost 300 件）。セッション合計は session 列                                                                           |

正規化スキーマで取れない・扱いにくいもの:

- user メッセージ単位のトークン（無い）
- tool_call と tool_result の別時刻（`state.time.start` / `end` で代用）
- 「ended_at」の明示的な値（無い）
- compaction / 要約の表現（今回のデータには無い: `time_compacting` はすべて NULL、`compaction` part は 0 件）

### アダプタ実装の注意

1. 正本は SQLite。`storage/` の JSON や旧 `storage/session/...` 形式（opencode の旧 JSON ストレージ）は移行済みで、残っていない。古い opencode の JSON ストレージが残っている環境のためにフォールバックを付けるかは任意。
2. `data` 列は JSON 文字列。ID は列の方を使う（`data` 内には無い）。part の順序は `ORDER BY message_id, id` で決まる。昇順 ID だが、`time_created` と組み合わせるのが安全。
3. session の ID は**降順**なので、ID でソートすると新しい順になる。時刻でソートする。
4. `cost` が `0`（int）のものは「無料」か「未計測」。今回は openai サブスクリプション経路がすべて 0 だった。`cline-pass` では real 値が入る。0 を NULL 扱いにするかは設計で決める。
5. `session.model` と `permission` は JSON 文字列。`metadata` のキーにはドットを含むもの（`kilocode.sandbox`）がある。
6. `state.status=running` の part が残る（45 件: 中断されたもの）。`MessageAbortedError` も同様。
7. part 1 件で最大 0.8MB。text や output は既定で切り詰めるか、オプトインで出す設計にする。
8. スキーマは Drizzle migration で頻繁に変わる（43 本、kilocode 独自テーブルあり）。`PRAGMA table_info` で列の有無を確認してから使う。
9. Python の sqlite3 は JSON1 を使える（sqlite 3.50.4 で確認）。ただし大量処理は Python 側で `json.loads` した方が予測しやすい。
10. Windows のパスを URI に渡すときは `file:///C:/...` と区切りを変換する。`%` や `?` を含むパスは `urllib.parse.quote` する。
11. ルート `kilo` CLI と拡張の同梱 CLI でバージョンが違うと migration の差が出る。読み取り専用なら影響は無いが、アダプタは「未知の列・未知の part type をスキップする」方針にする。

### 根拠

- **公式（リポジトリ内スナップショット `skills/plugins/ai-tools-knowledge/skills/kilo-code-docs/output/llms.txt`、元は kilo.ai/docs）**
  - `/code-with-ai/agents/session-history`（https://kilo.ai/docs/code-with-ai/agents/session-history）: DB の所在表、`KILO_DB` / `XDG_DATA_HOME`、`kilo db path`、session / message / part の SQL 例、読み取り専用の推奨、WAL / shm の注意
  - `/contributing/architecture/cli-runtime`（https://kilo.ai/docs/contributing/architecture/cli-runtime）: `${Global.Path.data}/kilo.db`、WAL などの pragma、JSON から SQLite への一回限りの移行、`session_diff` は JSON のまま、`daemon.json` / `daemon.log`、snapshot のパス
  - `/code-with-ai/features/checkpoints`（https://kilo.ai/docs/code-with-ai/features/checkpoints）: snapshot の場所、`git gc --prune=7.days`、revert 後の削除
  - 同じ llms.txt の 31081 行付近: `$XDG_DATA_HOME/kilo` は session data・logs・`repos/`
- **実データからの推定（バージョン依存で保証なし）**:
  - テーブルや JSON のキー構成
  - tokens / cost の整合性
  - ID 順序
  - project.id = global / 40hex
  - task ツールから子セッションへの対応
  - event テーブルの位置づけ
  - log / tool-output の保持
  - 拡張の globalStorage が空であること
- `tools/coding-agent/ai-usage/` には Kilo の知見は無かった（rg でヒット 0 件）。
- opencode の公式 storage ドキュメントは web-lookup で引いていない（下記の未解決に回した）。

### 未解決・要追加確認

- compaction / 要約の表現。opencode では `compaction` part や `summary: true` の assistant メッセージで表すが、このデータには 0 件。`/compact` を実行したセッションで確認が必要。
- 旧 Kilo Code VS Code 拡張（v4 系、Cline フォーク）の `tasks/<id>/api_conversation_history.json`・`ui_messages.json` 形式が残っている環境への対応。この PC では未確認。Cline のアダプタを流用できるかは Cline 担当の調査結果と突き合わせる。
- DB 本体の保持期間、自動 prune・アーカイブ（`time_archived`）の動作。
- `reasoning.metadata.openai.*` に暗号化された推論が入っているか（キー名だけ確認、値は未確認）。
- `session_message` / `session_input` テーブル（今回 0 件）が今後の正本に変わる可能性。
- macOS / Linux で `XDG_DATA_HOME` を設定しない場合の実際のパス（公式は `~/.local/share/kilo` と記載。macOS でも同じパスかは実機未確認）。

## Antigravity（Google）

- 調査日は 2026-11-17。確認したバージョンは、Antigravity CLI `agy` 1.5.9（`~/.gemini/bin/agy.version.json`）、Language Server 2.32.0（`~/.gemini/antigravity/log/cli-*.log` と `daemon/hub_*.json` の `lsVersion`）、Antigravity IDE の `ideVersion` 2.7.0（VS Code 1.107.0 ベース。`%LOCALAPPDATA%\Programs\Antigravity IDE\resources\app\product.json`）。
- 結論を先に書く。会話本文は平文で読める。暗号化されているのは思考署名だけ。
  - JSONL：`brain/<conv>/.system_generated/logs/transcript*.jsonl`。最も扱いやすいが、2026-10-29 以降の会話にしかない。
  - SQLite＋protobuf：`conversations/<conv>.db`。全期間をカバーするが、スキーマ非公開の protobuf blob になる。
  - v1 の方針案：一覧とメタデータは `conversation_summaries.db` から取る。本文は transcript.jsonl があればそれを使い、無ければ本文なしにする（後述）。

### 所在

公式ドキュメントに書かれている所在は 2 つだけで、どちらも保存形式の説明はない。

- `~/.gemini/antigravity-cli/cache/last_conversations.json`：resume ドキュメントに記載がある。
- `~/.gemini/antigravity/` が Artifacts と Knowledge Items の置き場：リポジトリ内スキルの記述。

以下はすべて実データからの推定（Windows では `C:\Users\<user>\.gemini\...`）。POSIX/macOS も `~/.gemini/...` と同じ構造だと推定するが、未確認。

| パス                                                              | 内容                                                                                                                                                                                                                                   |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `~/.gemini/antigravity/`                                          | 現行メイン。Antigravity 2.0（エージェントマネージャ）、IDE（2026-10-29 に移行）、CLI が共用している                                                                                                                                    |
| ├ `conversations/<conv-uuid>.db`                                  | 1 会話＝1 SQLite（500 件、約 675MB）                                                                                                                                                                                                   |
| ├ `conversation_summaries.db`                                     | 全会話の索引（SQLite＋FTS5。591 行）                                                                                                                                                                                                   |
| ├ `agyhub_summaries_proto.pb`                                     | 会話サマリの protobuf スナップショット（約 290KB）                                                                                                                                                                                     |
| ├ `brain/<conv-uuid>/`                                            | アーティファクト（`task.md` など）と `.system_generated/` 一式。81 件                                                                                                                                                                  |
| ├ `annotations/<conv-uuid>.pbtxt`                                 | protobuf テキスト形式。`title:"..."`（ユーザーによるリネーム）と `last_user_view_time:{seconds,nanos}`                                                                                                                                 |
| ├ `presence/<conv-uuid>.lock`                                     | 0 バイトのロックファイル                                                                                                                                                                                                               |
| ├ `log/cli-YYYYMMDD_HHMMSS.log`（`cli.log` はシンボリックリンク） | glog 形式の Language Server ログ（`I1117 hh:mm:ss.us pid file.go:line] ...`）。32 本                                                                                                                                                   |
| ├ `daemon/hub_<port>.json`                                        | 起動中プロセスの情報（pid、ポート、`lsVersion`、`csrfToken`）                                                                                                                                                                          |
| ├ `antigravity_state.pbtxt`                                       | UI 状態と移行フラグ（`migrate_convos_into_projects` など）                                                                                                                                                                             |
| └ `knowledge/`、`crashes/`、`cache/`                              | 調査時点で `knowledge/` は lock ファイルだけ                                                                                                                                                                                           |
| `~/.gemini/antigravity-cli/`                                      | 旧 CLI。構成は同じ（`conversations/*.db` 15 件、`conversation_summaries.db`、`jetbox_summaries_proto.pb`、`history.jsonl`、`cache/last_conversations.json`、`cache/conversation_metadata.json`）。最終更新は 2026-10-28                |
| `~/.gemini/antigravity-ide/`                                      | 旧 IDE。`conversations/*.db` 501 件と `-wal`/`-shm` 13 組、`brain/` 556 件、`browser_recordings/`、`html_artifacts/`。`.ide_migration`（2026-10-29）があり凍結状態。会話 db は 419 件がメインと同じ ID（移行時のコピー）               |
| `%APPDATA%\Antigravity IDE\User\`                                 | VS Code 系の領域。`globalStorage/state.vscdb`（ItemTable 969 キー。会話に関係するのは `antigravity.notification.*` など UI 状態だけ）と `workspaceStorage/<hash>/workspace.json`（`{"folder":"file:///..."}`）。会話本文はここには無い |
| `%APPDATA%\Antigravity\`                                          | 旧 Antigravity（2025〜2026-05）の Electron 領域                                                                                                                                                                                        |
| `~/.gemini/logs/install.log`                                      | インストーラのログ。会話とは無関係                                                                                                                                                                                                     |

### 形式とレコード構造

**A. `brain/<conv>/.system_generated/logs/transcript.jsonl` と `transcript_full.jsonl`（JSONL。推奨の入力）**

1 行＝1 step。`transcript.jsonl` は長いフィールドを切り詰めた版で、どのフィールドを切ったかが `truncated_fields` に入る。`transcript_full.jsonl` は全文版。`logs/chunks/{transcript,transcript_full}/0000000N.jsonl` は同じ内容をチャンクに分けたもの。

| フィールド                                             | 型と値の例                                                                                                                    |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `step_index`                                           | int。db の `steps.idx` と一致する                                                                                             |
| `type`                                                 | `USER_INPUT`、`PLANNER_RESPONSE`、`GENERIC`（ツール結果）、`SYSTEM_MESSAGE` など。`CORTEX_STEP_TYPE_*` から接頭辞を除いた名前 |
| `source`                                               | `USER_EXPLICIT`、`MODEL`、`SYSTEM`                                                                                            |
| `status`                                               | `DONE`、`RUNNING`、（`ERROR`、`CANCELED` もあると推定）                                                                       |
| `created_at`                                           | ISO8601 UTC（`YYYY-MM-DDThh:mm:ssZ`）                                                                                         |
| `content`                                              | str。本文。無い step もある                                                                                                   |
| `thinking`                                             | str。思考要約（PLANNER_RESPONSE のみ）                                                                                        |
| `tool_calls[]`                                         | `{name, args(dict)}`。`name` は `read_file`、`run_command`、`edit_file`、`write_file` など。**呼び出し ID は無い**            |
| `model`                                                | 例 `gemini-x-...`（PLANNER_RESPONSE のみ）                                                                                    |
| `input_tokens` / `output_tokens` / `cache_read_tokens` | int（PLANNER_RESPONSE のみ）                                                                                                  |
| `truncated_fields`                                     | 例 `["content"]`（切り詰め版のみ）                                                                                            |

```json
{"step_index":3,"type":"PLANNER_RESPONSE","source":"MODEL","status":"DONE","created_at":"2026-01-01T00:00:00Z","model":"<model>","input_tokens":1000,"output_tokens":50,"cache_read_tokens":0,"thinking":"<text>","tool_calls":[{"name":"run_command","args":{"<k>":"<v>"}}]}
{"step_index":4,"type":"GENERIC","source":"MODEL","status":"DONE","created_at":"2026-01-01T00:00:01Z","content":"<tool output>"}
```

- ツール結果（`GENERIC`）には tool 名も call ID も無い。直前の `PLANNER_RESPONSE.tool_calls` と出現順で対応付けるしかない（推定）。
- `brain/<conv>/.system_generated/steps/<idx>/output.txt` はツール出力の全文。
- `.system_generated/messages/<uuid>.json` はエージェント間メッセージ：`{id, recipient, sender, priority, timestamp, renderDetails.messageTitle, content, sourceMetadata.tool{conversationId, stepIndex, toolCall{id,name,argumentsJson,thinkingSignature}}}`。`messages/read.json` は `{<id>:true}`。
- アーティファクトは `brain/<conv>/{task,implementation_plan,walkthrough}.md` と、それぞれの `*.md.metadata.json`（`{artifactType, summary, updatedAt}`）。`task.md` は `# タイトル` の下に `- [x]/- [ ]` のチェックリストが並ぶ。ほかに画像（`<name>_<epochms>.png/.webp`）と `scratch/`（エージェントが作った作業ファイル）がある。旧 IDE の brain には `*.resolved.<n>` もあると推定（未確認）。

**B. `conversations/<conv>.db`（SQLite、WAL）**

テーブル：

- `trajectory_meta(trajectory_id PK, cascade_id, trajectory_type, source)`
- `steps(idx PK, step_type, status, has_subtrajectory, metadata, error_details, permissions, task_details, render_info, step_payload, step_format)`
- `gen_metadata(idx PK, data, size)`
- `executor_metadata(idx, data)`
- `parent_references(idx, data)`
- `trajectory_metadata_blob(id='main', data)`
- `battle_mode_infos`

blob はすべて素の protobuf（`step_format` は全 45,683 行で 0）。

enum の数値と名前は、`agy.exe` に埋め込まれた descriptor から抽出した（推定）。

- `step_type`：14 USER_INPUT、15 PLANNER_RESPONSE、8 VIEW_FILE、21 RUN_COMMAND、5 CODE_ACTION、9 LIST_DIRECTORY、7 GREP_SEARCH、23 CHECKPOINT、33 SEARCH_WEB、17 ERROR_MESSAGE、31 READ_URL_CONTENT、85 BROWSER_SUBAGENT、90 EPHEMERAL_MESSAGE、101 SYSTEM_MESSAGE、127 INVOKE_SUBAGENT、132 GENERIC、138 ASK_QUESTION（全 140 種）。
- `status`：3 DONE、6 CANCELED、7 ERROR、2 RUNNING。
- `trajectory_type`：4 CASCADE。
- `trajectory_meta.source`：1 CASCADE_CLIENT、17 CLI、22 VSCODE。

`step_payload` は「1=type、4=status、5=step metadata、型ごとの oneof フィールド」という構成。oneof のフィールド番号は USER_INPUT→19、PLANNER_RESPONSE→20、VIEW_FILE→14、RUN_COMMAND→28、CODE_ACTION→10、GENERIC→140、SYSTEM_MESSAGE→114。

- `5.1{1:seconds,2:nanos}` は作成時刻。
- `20.3` は応答本文（utf8）。
- `20.7` はツール呼び出し：`.1` ID、`.2` tool 名、`.3` 引数 JSON。
- `20.7.7.2.1` はエントロピー約 8.0 の bytes。暗号化された思考署名とみられる（推定）。それ以外の本文は utf8 平文。
- `gen_metadata.data` の中身：`1.19` モデル名文字列、`1.4.2`/`1.4.3` 入力/出力トークン（推定）、`1.4.9`/`1.4.10` キャッシュ系のトークンらしき値（不明）、`1.4.1` モデル enum。

**C. `conversation_summaries.db`（索引）**

`conversation_summaries` の列：`conversation_id`、`title`、`preview`、`step_count`、`last_modified_time`（`YYYY-MM-DD hh:mm:ss.fffffff+00:00`。未設定は `0001-01-01`）、`workspace_uris`（JSON 配列。例 `["file:///c%3A/..."]`。空のものが 10 件）、`status`（全件 `CASCADE_RUN_STATUS_IDLE`）、`source`（`''` または `CORTEX_TRAJECTORY_SOURCE_CLI`）、`project_id`（uuid）、`agent_name`、`parent_conversation_id`、`nesting_depth`、`battle_id`、`winning_conversation_id`、`not_fully_idle`、`killed`、`last_user_input_time`、`last_user_input_step_index`、`app_data_dir`（`antigravity`）、`raw_summary`（protobuf blob）、`group_id`。

- `conversation_parents(conversation_id, parent_id)` はこの環境では 0 行。
- `conversations_fts`（FTS5）は会話を最大 3 チャンクに分け、`user_body`/`agent_body` を平文で持つ。
- `agyhub_summaries_proto.pb` は `repeated 1{1:conv_id, 2:summary{1:title, 2:step_count, timestamps..., 4:uuid...}}` の形で、`raw_summary` と同じ型の可能性が高い（推定）。

**D. その他**

- `antigravity-cli/history.jsonl` のキーは `display`、`timestamp`、`type`、`workspace`（プロンプト履歴）。
- `cache/last_conversations.json` は `{絶対パス: conv_id}`（公式記載）。

### セッション⇔プロジェクト対応

- ファイル名・ディレクトリ名の UUID が、そのまま会話 ID になる。`conversations/<id>.db`、`brain/<id>/`、`annotations/<id>.pbtxt`、`presence/<id>.lock`、`conversation_summaries.conversation_id`、`trajectory_meta.cascade_id`（推定）がすべて同じ ID でつながる。
- 突き合わせ結果：summaries 591 件のうち db があるのは 500 件、brain が 81 件、annotations が 573 件。db だけある会話は 0 件。
- ワークスペースは `conversation_summaries.workspace_uris` から取る。`file:///c%3A/...` の形なので、URL デコードしてパスに戻す。1 会話あたり 0〜1 件で、distinct 11 種。`project_id` は Antigravity 内の「プロジェクト」概念で 7 種。プロジェクト名の所在は未確認。
- CLI だけは `last_conversations.json` が絶対パス⇔最新の会話 ID を持つ（公式記載）。
- `workspaceStorage/<hash>` の hash は会話との対応に使わない。

### 読み取り安全性・保持期間・秘密情報

- すべての db は WAL（`journal_mode=wal`）。稼働中の IDE 側には `-wal`/`-shm` がある。
- **注意（本調査の副作用の可能性）**：`mode=ro` で 2 ファイル（メインの `conversation_summaries.db` と最新の会話 db 1 本）を開いたあと、そのタイムスタンプの 0 バイト `-wal` と 32KB `-shm` が隣にできていた。アプリが起動中だった可能性もあり、原因は確定していない。それ以降は `mode=ro&immutable=1` だけを使い、全 db を問題なく開けた。
  - 対策：読み取り時は immutable=1 を使うか、`.db`（と、あれば `-wal`）を一時ディレクトリにコピーしてから開く。
  - immutable=1 は WAL 上の未チェックポイント分を見落とす。最新性が要るならコピー方式にする。
- 書き込み中のファイル：`status=RUNNING` の step や、`presence/*.lock` がある会話は進行中とみなせる（推定）。transcript.jsonl は追記型なので、最終行が不完全なら捨てる。
- 保持と削除：自動ローテーションの記述は見つけられなかった。会話は CLI の picker（F4）や UI から削除できる（公式記載）。削除時にどのファイルが消えるかは未確認。`log/` はセッションごとのファイルが蓄積されていく。
- 秘密情報が入りうる場所：`content`、`thinking`、`tool_calls.args`（コマンド、ファイル内容）、`steps/*/output.txt`、`scratch/`、FTS の `user_body`/`agent_body`、`title`/`preview`、db の protobuf 内 utf8 全般、`messages/*.json`、`daemon/hub_*.json` の `csrfToken`、`installation_id`、`workspace_uris`（ユーザー名を含むパス）。

### 正規化スキーマへの写像

| 正規化フィールド | ソース                                                                                                                                                   |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Session.id       | conversation_id（UUID）                                                                                                                                  |
| tool             | `antigravity`。`source` と `trajectory_meta.source` で cli／ide(vscode)／manager を細分できる                                                            |
| project/cwd      | `workspace_uris[0]` を URL デコードしたもの（空なら null）                                                                                               |
| started_at       | 最初の step の `created_at`（transcript）または `steps.metadata 1.1`（db）。summaries には開始時刻が無い                                                 |
| ended_at         | `last_modified_time`                                                                                                                                     |
| model            | PLANNER_RESPONSE の `model`（最頻値か最後の値）。db では `gen_metadata 1.19`                                                                             |
| title            | `annotations` の `title`（リネーム）を優先し、無ければ `conversation_summaries.title`                                                                    |
| Event.ts         | `created_at`                                                                                                                                             |
| role             | `USER_INPUT`→user、`PLANNER_RESPONSE`→assistant、`SYSTEM_MESSAGE`/`EPHEMERAL_MESSAGE`→system、`GENERIC`/`VIEW_FILE`/`RUN_COMMAND` など→tool              |
| kind             | `PLANNER_RESPONSE` の content→message、`thinking`→thinking、`tool_calls[]`→tool_call（1 件ずつ展開）、`GENERIC` など→tool_result、`ERROR_MESSAGE`→error  |
| tool_name        | tool_call は `name`。tool_result は直前の呼び出しから順序で推定。db からは `step_type` 名で代替できる                                                    |
| tokens_in/out    | `input_tokens`/`output_tokens`（追加で `cache_read_tokens`）                                                                                             |
| cost             | 取れない（料金情報なし）                                                                                                                                 |
| 親子             | `parent_conversation_id`/`nesting_depth`（サブエージェント 4 件、`agent_name` に例 `research`/`self`）。db の `has_subtrajectory` と `parent_references` |
| compact/要約     | 明示的なレコードは確認できなかった。`CONVERSATION_HISTORY`/`CHECKPOINT`（23）step が候補（推定）                                                         |

### アダプタ実装の注意

- 3 層のフォールバックにする：(1) transcript_full.jsonl → (2) summaries＋db のメタデータだけ（本文なし）→ (3) 余力があれば db protobuf の最小デコーダ（フィールド番号 20.3、20.7.x、19.x、5.1 を固定で読む）。(3) はスキーマ非公開で、バージョンによって番号が変わりうる。
- ルートは 3 つ（`antigravity`、`antigravity-cli`、`antigravity-ide`）をすべて走査する。同じ会話 ID が重複するので、ID で dedupe し、mtime が新しい方を採る。
- タイムスタンプの形式が揃っていない。summaries は 7 桁小数＋`+00:00`（Python 3.11 未満の `fromisoformat` では読めない）、`0001-01-01` は未設定値、protobuf は `{seconds,nanos}`、transcript は `Z` 付き。
- SQLite は必ず URI 形式の `mode=ro&immutable=1` で開くか、コピーしてから開く。メインの会話 db は 1 本あたり約 1〜2MB×500 件あるので、一覧表示に db を開かず summaries だけを使う。
- `transcript.jsonl` は切り詰め版なので `_full` を優先する。`GENERIC` には tool 名が無い。
- Windows のパスは URI で `c%3A` にエンコードされている。比較の前に大文字・小文字とスラッシュを正規化する。
- `daemon/`、`log/`、`presence/` は本文ソースではない。`csrfToken` は絶対に出力しない。

### 根拠

- 公式ドキュメント：
  - https://antigravity.google/docs/cli/commands/resume.md （`~/.gemini/antigravity-cli/cache/last_conversations.json` の所在と形式）
  - https://antigravity.google/docs/cli/conversations.md （履歴の workspace スコープ、fork）
  - https://antigravity.google/docs/artifacts.md 、 https://antigravity.google/docs/cli/artifacts.md （アーティファクトの概念のみで、保存形式の記載なし）
- リポジトリ内スキル：`c:\C\ai\skills\plugins\ai-tools-knowledge\skills\antigravity-memory\SKILL.md`（`~/.gemini/antigravity/` が Artifacts/Knowledge の格納場所）、`c:\C\ai\skills\plugins\ai-tools-knowledge\skills\antigravity-docs\SKILL.md`（`.md` twin の取り方）。
- 実データからの推定（バージョン依存で未保証）：上記以外のすべて。具体的にはディレクトリ構成、SQLite スキーマ、protobuf のフィールド番号、transcript.jsonl のキー、enum 対応表（`agy.exe` 1.5.9 の埋め込み descriptor から抽出）。

### 未解決・要追加確認

- transcript.jsonl を生成する条件。2026-10-29 以降の 81 会話にしか無く、2.0 で導入されたのか、設定やソースによるのかは不明。旧会話を遡って生成するかどうかも不明。
- `gen_metadata` のトークンフィールドの正確な意味（1.4.2/1.4.3/1.4.9/1.4.10）と、transcript の `input_tokens` との一致の検証。
- 会話削除時に db／brain／summaries／annotations のどれが消えるか。自動削除やサイズ上限があるか。
- `project_id` からプロジェクト名を引ける場所（`antigravity_state.pbtxt` か `cache/conversation_metadata.json` か）。
- macOS/Linux の実パス（`~/.gemini/...` と同一であるかの確認）、旧 IDE brain の `*.resolved.<n>` の形式、`CONVERSATION_HISTORY`/`CHECKPOINT` step による compact 表現。
- `mode=ro` で開いたあとにできた `-wal`/`-shm` の帰属。アプリが閉じた状態で再現確認が必要。調査で生じたものなら、ツール側は immutable かコピー方式を必須にする。

## OpenAI Codex（CLI / IDE 拡張 / app-server）

- 調査日: 2026-11-17
- 調べたソース: openai/codex `main` のコミット `885a1df5ee5f18172233b12d6c94544a24e7b338`（2026-11-17T00:39Z）。最新リリースタグは `rust-v0.169.0`。リリース版はこの main より古く、型名やフィールドが一部違う可能性がある。
- 公式ドキュメント: リポジトリ内スナップショット `codex-docs/output/llms-full.txt`（2026-08-29 取得）。
- この PC には実データが無い。`~/.codex`・`%USERPROFILE%\.codex`・`CODEX_HOME`（未設定）・`%APPDATA%`/`%LOCALAPPDATA%` 配下に codex 関連は見当たらず、`codex` コマンドも PATH に無い。以下はすべて公式ドキュメントとソースから確定したもので、実ログでは確かめていない。

### 所在

- ルートは `CODEX_HOME`（既定 `~/.codex`）。Windows は `%USERPROFILE%\.codex`、POSIX/macOS は `$HOME/.codex`。CLI・IDE 拡張・app-server で共通（公式記載）。`CODEX_HOME` を指定する場合は事前にディレクトリが必要。
- SQLite の置き場所は `CODEX_SQLITE_HOME`、または config の `sqlite_home`（こちらが優先）。既定は `CODEX_HOME`（公式記載）。
- ルート配下の主なファイル（ソース由来。公式文書は `config.toml`/`auth.json`/`history.jsonl` しか挙げていない）:

| パス                                                                    | 内容                                                                          |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `sessions/YYYY/MM/DD/rollout-YYYY-MM-DDThh-mm-ss-<thread_uuid>.jsonl`   | セッション本体（rollout）                                                     |
| 同上 `rollout-<ts>-<thread_uuid>_<rollout_uuid>.jsonl`                  | revert（巻き戻し）したスレッドの別 rollout                                    |
| 同上 `*.jsonl.zst`                                                      | 7 日以上前の rollout を zstd 圧縮したもの                                     |
| `archived_sessions/rollout-*.jsonl[.zst]`                               | アーカイブ済み。日付ディレクトリは無く平置き                                  |
| `history.jsonl`                                                         | ユーザー入力だけの履歴                                                        |
| `session_index.jsonl`（+`.lock`）                                       | スレッド名の索引                                                              |
| `state_5.sqlite`                                                        | threads メタ（cwd・title・model・tokens_used 等）                             |
| `thread_history_1.sqlite`                                               | paginated モードの turn/item 投影                                             |
| `logs_2.sqlite`                                                         | 診断ログ（tracing）                                                           |
| `goals_1`/`memories_1`/`queue_1.sqlite`                                 | 本調査の対象外                                                                |
| `log/codex-tui.log`                                                     | 平文 TUI ログ。現行は opt-in で、`log_dir` を明示したときだけ書く（公式記載） |
| `thread-writer-locks/<thread_id>.lock`、`.tmp/rollout-compression.lock` | ロックファイル                                                                |

### 形式とレコード構造

**rollout（JSONL、1 行 1 オブジェクト）**の外枠は `{"timestamp": "<UTC ISO, ミリ秒, Z>", "ordinal"?: <u64>, "type": "<snake_case>", "payload": {...}}`。`ordinal` は paginated モードで付き、legacy では省略されうる。`timestamp`/`type`/`payload` は常にある。

| type                                                                                                                                    | payload の要点                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `session_meta`                                                                                                                          | 必須: `id`（thread UUID）・`timestamp`・`cwd`・`originator`・`cli_version`・`model_provider`（null 可）・`base_instructions`（null 可）。任意: `session_id`（無ければ `id` で補う）・`source`・`thread_source`・`forked_from_id`・`parent_thread_id`・`agent_nickname`・`agent_role`（旧名 `agent_type`）・`agent_path`・`history_mode`（`legacy`/`paginated`、既定 legacy）・`git`（`commit_hash`/`branch`/`repository_url`）・`dynamic_tools`・`context_window` など |
| `turn_context`                                                                                                                          | 必須: `cwd`・`approval_policy`・`model`、および `permission_profile` か旧形式の `sandbox_policy` のどちらか。任意: `turn_id`・`root_turn_id`・`effort`・`summary`・`collaboration_mode` など。**モデル名はここから取る**                                                                                                                                                                                                                                               |
| `response_item`                                                                                                                         | payload は Responses API の item そのもの（`type` で分かれる。下の表）。外枠に任意の `metadata`（`history_sequence` 等）が付く                                                                                                                                                                                                                                                                                                                                         |
| `event_msg`                                                                                                                             | payload は `{"type": <EventMsg名>, ...}`。永続化されるものは下の表                                                                                                                                                                                                                                                                                                                                                                                                     |
| `compacted`                                                                                                                             | `message`（要約本文）・`replacement_history`（ResponseItem の配列、任意）・`window_id`・`latest_token_usage_record` など                                                                                                                                                                                                                                                                                                                                               |
| `token_usage_record`                                                                                                                    | `thread_id`・`turn_id`・`session_id`・`root_turn_id`・`response_id`・`usage`・`turn_token_usage`・`thread_token_usage`。それぞれの中身は TokenUsage                                                                                                                                                                                                                                                                                                                    |
| `inter_agent_communication`、`inter_agent_communication_metadata`                                                                       | サブエージェント間のメッセージ                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `world_state`（`full`, `state`）、`retained_context`、`security_risk_score`、`dynamic_tools_updated`、`realtime_item`（paginated のみ） | 補助情報。正規化では基本無視してよい                                                                                                                                                                                                                                                                                                                                                                                                                                   |

`response_item.payload.type` の種類:

- `message`: `role`（`user`/`assistant`/`developer`/`system`）、`content[]`、任意の `phase`（`commentary`/`final_answer`）。`content[]` の要素は `{type:"input_text", text}`・`{type:"output_text", text}`・`input_image` など。
- `reasoning`: `summary[]`（`{type:"summary_text", text}`）、`encrypted_content`、任意の `content`。
- `function_call`: `name`、任意の `namespace`、`arguments`（JSON 文字列）、`call_id`。
- `function_call_output`: `call_id`、`output`。`output` は文字列、または content item の配列（untagged）。
- `custom_tool_call`（`name`, `input`, `call_id`）、`custom_tool_call_output`（`call_id`, `output`）、`local_shell_call`（`call_id`, `status`, `action`）、`tool_search_call`/`tool_search_output`、`web_search_call`、`image_generation_call`、`agent_message`（`author`, `recipient`, `content`）。
- `compaction`、`context_compaction`、`additional_tools`、`configuration_update`。

rollout に書かれる `event_msg` の種類（`rollout/src/policy.rs` の `persisted_event_msg`）:

- 常に書かれる: `token_count`、`task_started`（別名 `turn_started`）、`task_complete`（別名 `turn_complete`）、`turn_aborted`、`thread_rolled_back`、`thread_goal_updated`、`thread_settings_applied`、`item_completed`（legacy では一部のみ）。
- **legacy モードのときだけ**書かれる: `user_message`（`message`, `images`）、`agent_message`（`message`, `phase`）、`agent_reasoning`、`agent_reasoning_raw_content`、`patch_apply_end`、`mcp_tool_call_end`、`web_search_end`、`image_generation_end`、`context_compacted`、`entered_review_mode`/`exited_review_mode`、`sub_agent_activity`。
- `exec_command_begin`/`exec_command_end` やストリーミングの delta は書かれない。
- paginated モードでは、コマンド実行や MCP の結果が `item_completed`（`item` は TurnItem）に入り、出力は 64KiB で切り詰められる。

`task_complete` のフィールド: `turn_id`、`last_agent_message`、任意で `started_at`/`completed_at`（epoch）・`duration_ms`・`error`。

トークン使用量:

- TokenUsage は `{input_tokens, cached_input_tokens, cache_write_input_tokens(既定0), output_tokens, reasoning_output_tokens, total_tokens}`。
- `token_count` は `{type:"token_count", info: null | {total_token_usage, last_token_usage, last_usage_includes_reasoning?, model_context_window}, rate_limits: null | {limit_id, primary:{...}, secondary, credits, plan_type, ...}}`。`total_*` はスレッドの累積、`last_*` は直前の 1 リクエスト分。
- **コスト（金額）のフィールドは無い。**

架空値で作った最小 fixture（legacy モード）:

```jsonl
{"timestamp":"2026-01-02T03:04:05.678Z","type":"session_meta","payload":{"id":"00000000-0000-7000-8000-000000000001","timestamp":"2026-01-02T03:04:05.678Z","cwd":"C:\\work\\demo","originator":"codex_cli_rs","cli_version":"0.0.0","source":"cli","model_provider":"openai","base_instructions":null,"git":{"branch":"main"}}}
{"timestamp":"2026-01-02T03:04:06.000Z","type":"turn_context","payload":{"turn_id":"t1","cwd":"C:\\work\\demo","approval_policy":"on-request","sandbox_policy":{"type":"read-only"},"model":"<model>","effort":"medium"}}
{"timestamp":"2026-01-02T03:04:06.100Z","type":"event_msg","payload":{"type":"task_started","turn_id":"t1"}}
{"timestamp":"2026-01-02T03:04:06.200Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"<text>"}]}}
{"timestamp":"2026-01-02T03:04:06.210Z","type":"event_msg","payload":{"type":"user_message","message":"<text>","images":[]}}
{"timestamp":"2026-01-02T03:04:07.000Z","type":"response_item","payload":{"type":"function_call","name":"shell","arguments":"{\"command\":[\"<cmd>\"]}","call_id":"call_1"}}
{"timestamp":"2026-01-02T03:04:08.000Z","type":"response_item","payload":{"type":"function_call_output","call_id":"call_1","output":"<output>"}}
{"timestamp":"2026-01-02T03:04:09.000Z","type":"response_item","payload":{"type":"message","role":"assistant","content":[{"type":"output_text","text":"<text>"}],"phase":"final_answer"}}
{"timestamp":"2026-01-02T03:04:09.100Z","type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120},"last_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":20,"reasoning_output_tokens":5,"total_tokens":120},"model_context_window":200000},"rate_limits":null}}
{"timestamp":"2026-01-02T03:04:09.200Z","type":"event_msg","payload":{"type":"task_complete","turn_id":"t1","last_agent_message":"<text>"}}
{"timestamp":"2026-01-02T03:05:00.000Z","type":"compacted","payload":{"message":"<summary>"}}
```

fixture の補足:

- `sandbox_policy` 内部の正確な形と `source` のシリアライズ表現は、テストで確かめる必要がある。
- `source` はサブエージェントだと `{"subagent":{"thread_spawn":{"parent_thread_id":"…","depth":1}}}` の形になる（推定）。

**history.jsonl**: 1 行が `{"session_id":"<uuid>","ts":<unix秒>,"text":"<入力>"}`。ユーザー入力だけを記録する。`[history] persistence = "none"` で無効化でき、`max_bytes` を超えると古い行を落として上限の 80% まで縮める。

**session_index.jsonl**: 1 行が `{"id":"<thread uuid>","thread_name":"<名前>","updated_at":"<ISO>"}`。追記型なので、同じ id の最後の行が有効。

**state_5.sqlite の `threads` 表**: `id`、`rollout_path`、`created_at[_ms]`、`updated_at[_ms]`、`source`、`model_provider`、`cwd`、`title`、`sandbox_policy`、`approval_mode`、`tokens_used`、`has_user_event`、`archived`、`archived_at`、`git_sha`/`git_branch`/`git_origin_url`、`cli_version`、`first_user_message`、`agent_nickname`/`agent_role`/`agent_path`、`model`、`reasoning_effort`、`thread_source`、`preview`、`recency_at[_ms]`、`history_mode`、`name`、`project_id`。

- `thread_spawn_edges(parent_thread_id, child_thread_id, status)` で親子関係が取れる。
- `projects` と `project_roots(path)` もある。

**thread_history_1.sqlite**: `thread_turns(thread_id, turn_id, rollout_ordinal, status, started_at, completed_at, duration_ms, …)`、`thread_items(thread_id, turn_id, item_id, rollout_ordinal, created_at_ms, item_json)`。

**logs_2.sqlite**: `logs(ts, ts_nanos, level, target, message, module_path, file, line, thread_id, process_uuid, …)`。

### セッション⇔プロジェクト対応

- パスのエンコードやハッシュは使っていない。cwd は rollout 先頭の `session_meta.payload.cwd` に絶対パスの生値で入っている。ターンごとに `turn_context.cwd` も入り、セッション中に変わりうる。
- `state_5.sqlite` の `threads.cwd` と `threads.rollout_path` から一覧を高速に作れる（インデックス `idx_threads_archived_cwd_recency_at_ms` あり）。
- git 情報は `session_meta.payload.git` または `threads.git_*` にある。
- ディレクトリの日付とファイル名の時刻は**ローカル時刻**（`now_local()`）。行の `timestamp` は UTC。ファイル名を解析する側（`RolloutFileName::parse`）は UTC と仮定しているので、ファイル名を開始時刻の正本にしないこと。

### 読み取り安全性・保持期間・秘密情報

- rollout は書き込み中に追記される。末尾が途中まで書かれた JSON になりうるので、最終行のパース失敗は読み飛ばす。
- 書き込みは `thread-writer-locks/<id>.lock` で排他しているが、読み取り側はロック不要（推定）。
- 圧縮ワーカーは、7 日以上前の rollout を `.jsonl.zst` に置き換え、元の `.jsonl` を消す（起動時、6 時間マーカー付き）。走査中に元ファイルが消えることがあるので、`FileNotFoundError` が出たら `.zst` 側で開き直す。
- legacy から paginated への**移行**（起動時、または `codex migrate-rollouts --apply`）は、rollout を書き直して差し替える。差し替え中は `.pending` ジャーナルが残る。
- SQLite は WAL・`busy_timeout` 5 秒で開かれている。読むときは `mode=ro`、失敗したら `immutable=1`。ただし immutable だと WAL 内の未チェックポイント分が見えない。
- 保持期間: rollout に自動削除は無い。圧縮だけされる。削除は `thread/delete` など明示操作のみ。`history.jsonl` は `max_bytes` で切り詰められる。`logs_2.sqlite` にはパーティションの剪定がある（詳細は未確認）。
- 秘密情報が入りうるフィールド:
  - `function_call.arguments` と出力: コマンド・環境変数・ファイル内容。
  - `message.content[].text`、`history.jsonl` の `text`。
  - `session_meta.base_instructions`（AGENTS.md の全文）。
  - `git.repository_url`。読み込み時にサニタイズされる。
  - `cwd`: ユーザー名入りのパス。
  - `reasoning.encrypted_content`。
  - `rate_limits.plan_type`。
  - `session_meta.creator_user_id`/`creator_account_id`。
  - `threads.first_user_message`/`preview`。
  - `auth.json` は対象外で、読まないこと。

### 正規化スキーマへの写像

| 正規化先    | 取り出し元                                                                                       |
| ----------- | ------------------------------------------------------------------------------------------------ |
| Session.id  | `session_meta.payload.id`（ファイル名の UUID と一致。revert の場合は `_` の前の部分）            |
| tool        | `"codex"`。下位区分は `source`（cli/vscode/exec/mcp/subagent…）と `originator`                   |
| project/cwd | `session_meta.payload.cwd`                                                                       |
| started_at  | `session_meta.payload.timestamp`                                                                 |
| ended_at    | 最終行の `timestamp`、または最後の `task_complete.completed_at`                                  |
| model       | 最初（または最後）の `turn_context.payload.model`。ターンごとに変わりうる                        |
| title       | `session_index.jsonl` の `thread_name` → `threads.name`/`title` → 最初の user message の順で探す |
| 親子関係    | `parent_thread_id`／`source.subagent.thread_spawn.parent_thread_id`、`forked_from_id`            |

Event への写像（ts はすべて行の `timestamp`）:

| 元のレコード                                                            | Event                                                                                                                      |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `response_item` の `message`                                            | kind=message、role=`payload.role`、text=`content[].text` を連結                                                            |
| `function_call`/`custom_tool_call`/`local_shell_call`/`web_search_call` | kind=tool_call、tool_name=`name`（または type 名）                                                                         |
| `*_output`                                                              | kind=tool_result。`call_id` で呼び出しと突き合わせる                                                                       |
| `reasoning`                                                             | kind=reasoning、text=`summary[].text`                                                                                      |
| `compacted`                                                             | kind=summary                                                                                                               |
| `event_msg.token_count`                                                 | kind=usage。tokens_in=`last_token_usage.input_tokens`、tokens_out=`output_tokens`（+`reasoning_output_tokens` は別に持つ） |

取れないフィールド: cost（料金表から自分で計算するしかない）、メッセージ単位の model（turn_context から引き継ぐ）、`function_call_output` の終了コード（文字列に埋め込まれていることがある）。

### アダプタ実装の注意

1. **重複**: legacy モードでは、同じ発話が `response_item.message` と `event_msg.user_message`/`agent_message` に二重に書かれる。正本は `response_item` 側に寄せる。paginated には event 側が無い。
2. `role=developer`/`system` のメッセージと、AGENTS.md・環境情報を差し込んだ user メッセージ（`<environment_context>` 等のタグで始まる。推定）はノイズなので除外を検討する。
3. **トークンの二重計上**: `token_count` は累積値なので、合計は最後の `total_token_usage` を使い、`last_*` を足し上げない。`info` が null の行は飛ばす。同じ値が連続することもありうる。新しい形式では `token_usage_record`（response 単位）が正確なので、あればそちらを優先する。
4. `.jsonl.zst` の読み込み: zstd は Python 3.14 から `compression.zstd` で標準ライブラリに入った。それより前の Python では外部依存（`zstandard`）が要る。読めないときはスキップして警告する設計にする。
5. 未知の `type` やフィールドは無視して先へ進む（`#[serde(other)]` があり、仕様が頻繁に変わる）。`type` の旧名にも対応する: `task_started`/`turn_started`、`agent_type`→`agent_role`、`session_id` が無い旧形式。
6. 浮動小数を含む行がある。`json.loads` で問題ないが、行の全体が dict であることを確かめる。
7. `arguments` は JSON 文字列なので二度パースする。`output` は文字列か配列のどちらか。
8. `sessions/` と `archived_sessions/` の両方を走査する。圧縮や移行の一時ファイル（`.tmp`、`.pending`、staged）は除外する。
9. Windows では cwd が `C:\\...` の形で入る。プロジェクトキーへ正規化するときは大文字小文字とスラッシュを揃える。
10. 一覧はまず `state_5.sqlite` から作り、DB が無いか壊れていれば rollout の先頭行（`session_meta`）だけ読んで代わりにする。ファイル全体は読まない。

### 根拠

- 公式ドキュメント:
  - https://developers.openai.com/codex/llms-full.txt（スナップショットは `skills/plugins/ai-tools-knowledge/skills/codex-docs/output/llms-full.txt`）
    - 「Config and state locations」は 9880 行付近、「History persistence」は 10523 行付近、環境変数 `CODEX_HOME`/`CODEX_SQLITE_HOME` は 13261 行付近、「codex-tui.log は opt-in」は 13325 行付近。
    - `log_dir` と `sqlite_home` の config キーは 11094〜11100 行付近、`history.persistence` は 11977 行付近。
  - リポジトリ内スキル: `skills/plugins/ai-tools-knowledge/skills/codex-settings/references/config-reference.md:116-117`、`codex-hooks/references/hooks.md:308-317`（`transcript_path` の形式は安定インターフェースではないと明記）。
- ソース（コミット 885a1df）。URL の形は `https://github.com/openai/codex/blob/885a1df5ee5f18172233b12d6c94544a24e7b338/<path>`:
  - `codex-rs/rollout/src/lib.rs`: `decode_rollout_line`、`SESSIONS_SUBDIR`/`ARCHIVED_SESSIONS_SUBDIR`
  - `codex-rs/rollout/src/rollout_file_name.rs`: ファイル名の規則
  - `codex-rs/rollout/src/recorder.rs:1701-1722`: 日付ディレクトリはローカル時刻、`:975-980`: UTC の timestamp
  - `codex-rs/rollout/src/compression.rs:26,371-377`: `.zst`、7 日、ロックマーカー
  - `codex-rs/rollout/src/policy.rs`: 永続化される item/event
  - `codex-rs/history/src/lib.rs:295-` と `rollout_payload.rs:37-`: RolloutItem と wire 形式の `type`/`payload`
  - `codex-rs/protocol/src/protocol.rs`: SessionMeta(:3517)、SessionMetaLine(:3637)、TurnContextItem(:3696)、TokenUsage(:2573)、TokenUsageRecord(:2596)、TokenUsageInfo(:2608)、TokenCountEvent(:2674)、EventMsg(:1564、task_started/task_complete の rename)、SessionSource(:3220)、ThreadHistoryMode(:979)
  - `codex-rs/protocol/src/models.rs`: `ResponseItem`、`ContentItem`
  - `codex-rs/message-history/src/lib.rs:3-8,52-57`: history.jsonl
  - `codex-rs/rollout/src/session_index.rs:23-31`
  - `codex-rs/state/src/sqlite.rs`（grep.app 経由）: DB ファイル名と WAL
  - `codex-rs/state/migrations/*.sql`、`thread_history_migrations/0001`、`logs_migrations/0001`
  - `codex-rs/thread-store/src/local/rollout_migration.rs`（legacy→paginated の書き換え）、`archive_thread.rs:83-103`（平置きで移動）
- 実データからの推定: 無し（実データが存在しない）。fixture の値はすべて架空で、`sandbox_policy`・`source`・`originator` の具体的な表現は推定。

### 未解決・要追加確認

- 新規スレッドの既定が legacy か paginated か（feature/config での切り替え条件）と、自動移行がいつ走るか。
- 圧縮ワーカーが既定で有効か（`compression_enabled` の出どころ）。main とリリース版で差があるか。
- `SessionSource` と `sandbox_policy` の JSON 上の実際の表現。実ログ、または `codex-rs/app-server-protocol/schema/json` の生成スキーマで確かめる。
- 環境注入用の user メッセージを見分けるタグ名の一覧（`<environment_context>`、`<user_instructions>` 等）。
- `logs_2.sqlite` の保持期間と剪定の閾値。`log/` 配下に既定で何が書かれるか（TUI ログ以外）。
- IDE 拡張（VS Code）が同じ `CODEX_HOME` を使うことは公式に書かれているが、WSL 上で動く場合の所在（Linux 側の `~/.codex`）。
- rollout ファイルが作られるタイミング（最初のユーザー入力まで遅延するか）。
