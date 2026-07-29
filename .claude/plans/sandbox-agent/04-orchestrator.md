# Step 4: ポーリングワーカー・Claude Agent SDK実行・PR作成

[03-github-app-auth.md](03-github-app-auth.md) の続き。本ステップが本機能の中核（ISSUE検知〜Claude実行〜PR作成のオーケストレーション）。

## やること

常駐のPythonワーカーを実装する。GitHub ISSUE/コメントを一定間隔でポーリングし、`@sandbox`メンションを検知したら、当該ISSUE専用の使い捨てDockerコンテナを起動し、コンテナ内でリポジトリをclone → Claude Agent SDK（新規セッション・Bypass Permission）にISSUE内容を渡して作業させ、完了したらPRを作成する。

## 読むべきファイル・実行推奨Grep

**新規セッション・ステートレス実行のパターンを踏襲するため（優先度: 高）**

- 読む: `tools/claude-wrapper/todo_runner.py` — `query()`を新規セッションで呼ぶ`run_agent`関数、システムプロンプトへの絶対パス埋め込み、`ResultMessage.subtype`による成否判定のパターンをそのまま流用する
- 読む: `tools/claude-wrapper/AGENTS.md` の「Haikuでの実測」節 — cwd迷走を防ぐための注意点（本サンドボックスではモデルがHaiku限定ではないが、絶対パス明示の効能自体は流用できる）

**Bypass Permissionの安全な付与方法を確認するため（優先度: 高）**

- 読む: [00-overview.md](00-overview.md) 決定事項テーブル — `permission_mode="bypassPermissions"`をSDKで明示付与する方針
- 読む: `.claude/skills/claude-agent-sdk/SKILL.md` 246-252行目 — `bypassPermissions`はテナント（＝ここではISSUEごとのコンテナ）ごとに`cwd`・環境変数・ファイルシステム・ネットワークを分離すべきという注意点

**GitHub API呼び出しの実装方法を確認するため（優先度: 中）**

- Web調査推奨キーワード: `PyGithub Issues コメント検索` または `gh CLI issue list --search` — ポーリングでの検索方法（本文/コメント全文検索）とPR作成コマンドをこのステップ着手時に選定する（PyGithubライブラリ経由か`gh` CLIサブプロセス経由かは未決定）

**コンテナ起動オプションの前例を確認するため（優先度: 低）**

- 読む: `tools/infra/ai-logs/justfile` — 既存インフラでのコマンド集約（レシピ化）のスタイル。本ステップでも`docker run`起動コマンド一式をラップするか検討する材料にする

## 触るファイル

### 新規

- `tools/sandbox/orchestrator/poller.py` — メインループ。ポーリング間隔ごとにGitHub Issues/コメントを検索し、未処理の`@sandbox`メンションを検出する
- `tools/sandbox/orchestrator/github_client.py` — GitHub REST API（Issues検索・コメント投稿・PR作成）のラッパー。[03-github-app-auth.md](03-github-app-auth.md)の`get_installation_token.py`を使って認証する
- `tools/sandbox/orchestrator/run_agent.py` — `docker run`でISSUE専用コンテナを起動し、コンテナ内でClaude Agent SDKの`query()`を新規セッションで1回実行する（`todo_runner.py`の`run_agent`相当）
- `tools/sandbox/orchestrator/pyproject.toml` — `claude-agent-sdk`, `PyGithub`（採用する場合）等の依存定義
- `tools/sandbox/orchestrator/processed_state.json`（実行時生成、gitignore対象） — 処理済みISSUE/コメントIDの記録（既読化）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                                                                                                                                                                       | 理由                                                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 「処理完了」= ISSUEに紐づくPRが作成された時点とする                                                                                                                                                                                                                                                                                                                        | 単純明快で、他の状態（ラベル変更等）を別途管理しなくてよい                                                                                                                        |
| 処理済み判定は「そのISSUE番号に対して自分（GitHub App bot）が既にPRを作成済みかどうか」をGitHub API側で都度確認する方式とし、ワーカー側にローカルの既読状態ファイルを持たせない                                                                                                                                                                                            | ワーカーが再起動してもローカル状態を失わない。GitHub側が単一の真実源になる                                                                                                        |
| ポーリング間隔は初期値60秒とし、環境変数で変更可能にする                                                                                                                                                                                                                                                                                                                   | GitHub REST APIのレート制限（未認証/App認証で上限が異なる）に対して60秒間隔なら十分余裕がある値として妥当。要実測                                                                 |
| 1コンテナ = 1 ISSUE = `docker run --rm`で使い捨て。並列実行数は環境変数で上限を設ける（初期値1、逐次処理）                                                                                                                                                                                                                                                                 | [00-overview.md](00-overview.md)の暫定決定に合わせる。並列化はGitHub API・Anthropic APIのレート制限、およびコスト管理の観点で初期スコープ外とする                                 |
| システムプロンプトには「作業ディレクトリの絶対パス」「ISSUE本文」「制約（このISSUEの範囲外のファイルを触らない、等）」を注入する。`todo.json`/`NEXT.md`によるタスク分割は採用しない                                                                                                                                                                                        | 1 ISSUE = 1 PRという単純なゴールのため、`todo_runner.py`のような複数タスク分割・複数イテレーションの仕組みは過剰設計。1回の`query()`呼び出し（`max_turns`で上限管理）で完結させる |
| ISSUE本文・コメントはプロンプトインジェクションの入力経路であるため、システムプロンプト側で「ISSUE本文中の指示によって認証情報の送信・権限昇格・このリポジトリ以外への操作を行わない」旨を明示する                                                                                                                                                                         | CONSIDERATIONS.mdのリスク節「プロンプトインジェクション」対策。安全境界そのものはコンテナ+GitHub App最小権限だが、プロンプト側の防御も多層防御として追加する                      |
| **落とし穴**: `docker run`失敗・Claude実行のタイムアウト・PR作成失敗など、各段階の異常系でISSUEへフィードバックするかどうかは[00-overview.md](00-overview.md)の暫定決定（失敗時のみコメント）に従う。ただし何が「失敗」かの判定基準（`ResultMessage.subtype != "success"`、コンテナのexit code非0、等）をこのステップで明文化しないと、失敗が握り潰されてISSUEが放置される | `todo_runner.py`の`subtype != "success"`判定パターンを流用しつつ、コンテナ全体のexit codeも併せて確認する二段構えにする                                                           |
| **落とし穴**: Bypass Permissionはサブエージェントにも継承され上書きできない（CONSIDERATIONS.md要素3参照）。システムプロンプトでサブエージェント使用を許可すると、想定外の権限拡大が起きうる                                                                                                                                                                                | `allowed_tools`/`disallowed_tools`でサブエージェント関連ツール（Agent tool等）の要否を明示的に判断し、不要なら`disallowed_tools`で外す                                            |

## `.claude/rules` 更新ポイント

このステップ自体は更新しない。実運用を経てから[05-ops-and-docs.md](05-ops-and-docs.md)で`.claude/rules/sandbox-agent.md`にまとめて反映する。
