# AIツール使用量可視化ツール — ラフプラン（調査結果）

## やりたいこと（再掲）

Claude Code / Cursor / Antigravity / Codex / Cline(Pass) の5ツールについて、各ツールの「5時間制限」「週間制限」相当の消費率を、細かい内訳は不要でシンプルに可視化したい。単位はツールごとに違って良い。

## 調査結果サマリ（ツール別サブエージェント調査、各エージェント独立実行）

| ツール             | 5h/週間相当の制限は存在するか                                | ローカルスクリプトから読めるか                                                                                                                                       | 実現性                 |
| ------------------ | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| Claude Code        | あり（`five_hour` / `seven_day`、`used_percentage`）         | ◯ `statusLine`フックのJSON stdinから取得可（要ライブセッション）                                                                                                     | **実現可能**           |
| Codex              | あり（`primary` / `secondary`ウィンドウ）                    | ◯ `codex app-server`をサブプロセス起動しJSON-RPC `account/rateLimits/read`を叩けば取得可                                                                             | **実現可能**           |
| Cline (Cline Pass) | あり（5時間／週間／月間の3ウィンドウ、ドキュメント確認済み） | △ CLI・ローカルファイルには無し。認証API `api.cline.bot/api/v1/users/{id}/usages` はあるが、5h/週/月の内訳を返すかは未検証（ドキュメントはダッシュボードUIのみ案内） | **要検証（未確定）**   |
| Cursor             | **無し**（月次クレジットプールのみ、時間窓型ではない）       | × 個人ユーザー向けAPIなし。Admin APIはEnterprise/Team管理者限定で、しかも集計spend/token、%消費率ではない                                                            | **無理**               |
| Antigravity        | あり（Ultra/Proは5時間+週間、その他は週間のみ）              | × CLIの`/usage`等はTUI専用（非JSON）。裏では内部API`cloudcode-pa.googleapis.com`(v1internal, 未公開)を叩いているのを確認したが、非公式・ToSリスクがありハック扱い    | **無理**（ハック除く） |

### 詳細（各サブエージェント報告より）

**Claude Code**

- `.claude/settings.json` の `statusLine` フックに登録したスクリプトが、セッション中stdinで受け取るJSONに `rate_limits.five_hour.used_percentage` / `rate_limits.seven_day.used_percentage`（+ `resets_at`）が含まれる（v2.1.80以降、`code.claude.com/docs/en/statusline` で確認）。
- 制約: Pro/Max/Team/Enterprise契約が必要（APIキー利用時は出ない）。セッション開始直後ではなく最初のAPI応答後に初めて値が入る。
- 収集方針: statusLineスクリプト自身がこのJSONを毎回どこか（ローカルファイル等）に書き出すログ役を兼ねる。可視化ツールはそのログファイルを読むだけで済む。ライブセッションが動いていないと値が更新されない点に注意（`claude -p`で軽く叩けば更新可能）。

**Codex**

- `codex app-server` をローカルでサブプロセスとして起動し、JSON-RPCで `initialize` → `account/rateLimits/read` を呼ぶと `primary`/`secondary`（`usedPercent`, `windowDurationMins`, `resetsAt`）が返る（`codex-plugins/meta/skills/codex-docs/output/llms-full.txt` で確認）。
- `primary`=5時間, `secondary`=週間、という対応はプロダクト説明文からの推測であり、スキーマ上明記はされていない。実装時は `windowDurationMins`（5h≈300, 週≈10080）を見て動的に判定するのが安全。
- 既存の`codex`認証（ChatGPTプラン/APIキー）をそのまま再利用できる。追加の資格情報配線は不要。

**Cline (Cline Pass)**

- ドキュメント上は5時間/週間/月間の3ウィンドウ制限が明記されているが、CLIにもローカル設定ファイル（`~/.cline/data/settings/*.json`、VS Code globalStorage）にも消費率は一切キャッシュされていない。公式には「ダッシュボード（app.cline.bot）で確認」とだけ案内。
- `api.cline.bot/api/v1/users/{id}/usages`（個人APIキーで認証、Bearerトークン）という公開APIエンドポイントは存在するが、レスポンスが5h/週/月の内訳を返すのか、それとも汎用のトークン使用履歴だけなのかはドキュメントからは確認できず、実際に叩いて検証しないと分からない。
- 調査中、このエージェントはローカルの `providers.json` / `global-settings.json`（認証情報が含まれうる設定ファイル）の構造を確認しており、ハーネスから「認証情報ストア探索」の注意フラグが出た。指示範囲内の調査だったとエージェントは報告しているが、実装時にこのファイルへ触れる場合は改めて安全側で扱う。

**Cursor**

- 時間窓型の制限が存在しない（月次クレジットプールのみ）ため、そもそも「5時間/週間消費率」という形の可視化に載せる数字自体がない。
- Admin APIはTeam/Enterprise管理者専用で、個人Pro/Pro Plus/Ultraユーザーは使えない上、返るのも集計spend/tokenでパーセンテージではない。
- ダッシュボード（`cursor.com/dashboard/spending`）のみがリアルタイム消費を見られる場所で、公開APIも公式エクスポートも無い。

**Antigravity**

- CLI (`agy`) の `/usage` `/quota` `/credits` はインタラクティブTUIコマンドのみで、JSON等の機械可読出力を持たない。`agy --help` のトップレベルサブコマンドにも無し。
- 裏側では `https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist` という非公開の内部APIをOAuthで叩いているのをローカルログから確認したが、これは非公式リバースエンジニアリングでありToSリスクがある。ユーザーからは「無理なハックを考える必要はない」と明言されているため、採用候補から除外する。

## 論点・決定が必要な点

1. **v1のスコープをどうするか。**
   - 確実に作れるのは Claude Code と Codex の2ツールのみ。
   - Cline は「作れるかもしれないが未検証」— 実装前に実際にAPIキーで`/usages`を1回叩いて中身を確認する検証ステップが要る。
   - Cursor と Antigravity は今回の調査範囲では技術的に無理（ハック無しでは）。この2つは「対応不可」として明記し、ツール一覧には載せるが「ダッシュボードで確認してください」的なプレースホルダー表示に留める、あるいは最初からスコープ外にする、の二択。
2. **Claude Codeのデータ収集方式。** `statusLine`フックはライブセッション前提。可視化のたびに最新値が欲しいなら、`statusLine`スクリプト側で毎回ログファイルに追記させておき、可視化ツールはそのログの最新行を読む設計になる（セッションが動いていない間は値が更新されない=多少古いスナップショットになる点は許容できるか確認したい）。
3. **可視化の見せ方。** CLIで数字を出すだけで良いか、簡単なダッシュボード（例: ローカルHTML）にしたいか。ユーザーの要望は「シンプルに」なので、まずはCLI/ターミナル表示（テーブルやバー）で十分そうだが確認したい。
4. **既存スキルへの組み込み方。** 各ツールの `meta` スキル配下（`codex-plugins/meta/skills/codex-cli-use` 等）に置くのか、独立した新規ツール（`tools/internal/ai-usage-dashboard/` のような）として作るのか。後者が既存パターン（`tools/mslearn` 等）に近い。

## 次のアクション

- 上記論点をユーザーに確認し、方針が決まったら `.claude/plans/` に詳細プラン（Claude Code + Codex を確実に実装、Cline は検証ステップを挟む、Cursor/Antigravityの扱いを決定）を起こす。
