# Step1 調査ログ（2026-11-19）

使い捨ての調査スクリプトは `%TEMP%` に置き、リポジトリには残していない。数値は 2026-11-19 時点。

## 1. 最後の変更と変更頻度（git）

### 履歴の起点

- アンブレラの最初のコミットは `71336a9 2026-11-10T14:45 chore(repo): import existing working tree as initial commit`（1696 ファイル、SKILL.md 129 件）。
- `skills`・`tools`・`agent-compat` の各サブモジュールも 2026-11-10 の移動・取り込みコミットから始まる（`42b8c2a`・`3063e7c`・`b31177e`）。
- 取り込み前の履歴は旧 `fdshg693/AI` にあったが、`plans/repo-restructure` の決定（`git show 8f76b39`）どおり履歴なしの新リポジトリで置き換えたため、ローカルにも GitHub にも残っていない。
- そのため「再編より前の履歴をアンブレラの旧パスからつなぐ」案は成り立たない。アンブレラ側でつなげるのは 2026-11-10 の 14:45〜20:51（取り込み〜サブモジュール分割）の約 6 時間分だけ。

### パス変換

- `maintenance/scripts/repo_git.py` の `owner(root, rel_posix)` が、アンブレラ相対パス → (所有リポジトリ, リポジトリ内パス) を返す。`submodule_paths()` は `.gitmodules` を直接読み、未チェックアウトのサブモジュールを飛ばす。新しく書く必要はない。

### 一括書き換えコミット

SKILL.md を含むコミットを見ると、conventional commit の type だけでは分けられない。

| コミット                                                                                                 | ファイル数 | SKILL.md | 実体               |
| -------------------------------------------------------------------------------------------------------- | ---------- | -------- | ------------------ |
| `ed9c81a refactor(repo): move generic Claude Code plugins`                                               | 1060       | 126      | 移動               |
| `5838a13 refactor(tools): group CLIs into llm, coding-agent and web-research folders`（tools）           | 453        | 14       | パス書き換え       |
| `b41e052 refactor(repo): serve other-tool knowledge skills from one ai-tools-knowledge plugin`（skills） | 143        | 42       | 移動               |
| `7ec85da docs(skills): sync cc-knowledge skills with Claude CLI 2.1.319 docs`                            | 32         | 13       | **本物の内容更新** |
| `9a6ed6f fix(skills): drop stale repo-layout notes from ai-tools-knowledge skills`                       | 18         | 15       | 本物の修正（小）   |
| `e2fec4a docs(skills): point references at the regrouped tools/ category paths`                          | 8          | 1        | 小さなパス追随     |

- 除外規則「件名が `refactor(repo)` か `chore(repo): import` で始まる、またはファイル数 > 100」で、移動・取り込み・大きなパス書き換えは落ち、`7ec85da` は残る。閾値を 50 にしても差は 4 件（`7e9abee` など 23〜53 ファイルの本物の変更が落ち始める）なので 100 にする。
- 小さなパス追随（`e2fec4a`・`975d4cf` など）は残る。人が触った＝最低限の追随はしたので「変更」として数えてよい。

### 結果（4 ルート 136 件、除外規則あり）

- 取り込み以降に実質的な変更がないスキル: **67 件**（最終変更 = 「2026-11-10 以前・不明」）
- 最終変更日の分布: 11-10: 18 / 11-11: 12 / 11-12: 3 / 11-15: 8 / 11-16: 11 / 11-17: 13 / 11-18: 4
- 実質コミット数の分布: 0 件 67 / 1 件 48 / 2 件 13 / 3 件 3 / 5 件 1 / 8 件 3 / 9 件 1
- 全リポジトリで `git log --no-renames --name-only` を 1 回ずつ流し、依存先の計算まで含めて **約 1.6 秒**。動的コンテキストに載せても問題ない速さ。

## 2. 変更の入りやすさ

### 依存先

- `skill/util/skill_tool_graph.py` の `load_graph()` が `requires_skills`・`requires_repo_tools`・`requires_install` と `repo-tools.yaml` を索引する。`skills_by_name`（名前 → SkillNode のリスト）で同名の判定もできる。`tool_keys_mentioned()` がキーとパスの両方を解決する。
- 136 件中 `requires_repo_tools` あり 29 件、`requires_skills` あり 62 件。
- 4 ルートに絞ると **同名スキルは 0 件**（全体では `.claude/skills/` のコピーや `temp/` と重複する。下記「対象範囲」）。
- 解決できない値は 8 件。
  - `maintenance/plugin` の `requires_repo_tools` 4 件はファイルパス（`maintenance/scripts/justfile`・`lefthook.yml` など。「説明するファイル」の意味）。→ ファイルパスとして git の最終変更日を引けばよい。
  - `superpowers:...`・`elements-of-style:...` の 4 件は外部プラグインのスキル。→ 依存先の変化の対象外として扱う。
- 依存先がスキル本体より新しく変わったスキル: **28 件**。例: `agent-logs-cli`（依存する 6 つのログ形式スキルが後から更新）、`ms-learn`・`vscode-copilot-docs`（`tools/llm/aim` が後から更新）、`textgraph`（`tool:textgraph`）。信号として十分使える。

### プラグイン別件数（4 ルート、136 件）

| プラグイン                               | 件数 | 題材                                                                            |
| ---------------------------------------- | ---- | ------------------------------------------------------------------------------- |
| ai-tools-knowledge                       | 48   | 他 AI ツールの仕様（外部）                                                      |
| cc-knowledge                             | 19   | Claude Code の仕様（外部）                                                      |
| my-tools（tools/_plugin）                | 17   | 自作 CLI の使い方                                                               |
| topics                                   | 12   | 外部サービスの公式ドキュメント（`writing-mermaid-diagrams` だけ普遍的）         |
| special                                  | 8    | グループ化スキルの見本。うち 6 件は `sub_skills/`・`sub_commands/` 配下の入れ子 |
| maintenance                              | 7    | リポジトリ保守                                                                  |
| coding                                   | 7    | 普遍的な手順（`gh-pr` は外部 CLI 依存）                                         |
| browser                                  | 4    | playwright-cli（外部）                                                          |
| cicd                                     | 4    | GitHub Actions など                                                             |
| subagents                                | 3    | 普遍的な手順                                                                    |
| others                                   | 2    | `github-fetch`・`vscode-docs`                                                   |
| web-lookup                               | 2    | 外部 API（Tavily・Context7 など）                                               |
| agent-compat-tools / doc-tools / no-code | 各 1 | 自作 CLI / 文書変換 / 語学                                                      |

プラグイン単位の既定値でほぼ分けられる。個別の上書きが要りそうなのは `topics/writing-mermaid-diagrams`（low）、`coding/gh-pr`（medium）程度。

### skill-maintenance

- 差分 `temp/skill-maintenance/diff/` は実行時だけの一時ファイル（現在この端末には無い）で、入力にできない。
- コミットされるのは `maintenance/plugin/skills/skill-maintenance/state/*.snapshot` の 3 つだけで、`cc-knowledge` の一部にしか対応しない。git の最終変更日を「上流を最後に確かめた日」として使えなくはないが、対象が狭いので v1 では入れない。

## 3. 既存の品質・フィードバック

### 対象範囲

- `find_skill_md_files(repo_root)` は **153 件**を返す。4 ルート以外に、`.claude/skills/`（`skill-tools sync-skills` が入れる gitignore 済みコピー、10 件）、`temp/`（gitignore、5 件）、`templates/.claude/skills/`（2 件）を含む。
- `.claude/skills/` と `temp/` は 4 ルートのスキルと同名で、含めると二重に数える。→ 4 ルートの前方一致で絞る。`templates/.claude/skills/` はテンプレートの中身で、このリポジトリで使うスキルではないので外す。
- `special` の入れ子 6 件（親ディレクトリにも `SKILL.md` がある）は親スキルの部品なので外す。→ 対象は **130 件**。

### meta.status

- 136 件: stable 83 / experimental 45 / draft 8 / deprecated 0。
- draft 8 件のうち 6 件は `special` の入れ子（外すので残りは `coding` 1・`my-tools` 1）。deprecated は今は 0 件だが、既定で除外する規則は残す。

### skill-tools --fb

- 保存先 `tools/skill-tools/fb/` にあるのは 3 件だけ（スキル 1 件・ツール 2 件、すべて 2026-11-16）。今は信号としてほぼ空。
- 保存先のディレクトリ名は **スキル名**（canonical ID ではない。README の `--fb` 節）。照合はスキル名で行う必要がある。4 ルート内に同名が無いので今は衝突しない。
- `skill-tools --fb committing --fb-kind skill` と canonical ID 指定の両方で、`no skill named ...` と終了コード 2（書き込みなし）を確認した。
- `skill-tools list-skills` は 129 件 = 136 − `maintenance/plugin` 7 件。`--fb` の対象外は `maintenance/plugin` だけ（`templates/` は対象範囲から外すので考えなくてよい）。

### audit-skills

- `.claude/workflows/` のワークフローでサブエージェントを多数起動する。費用が大きく、常時の入力にはしない（overview の想定どおり）。

## 4. 利用頻度（agent-logs）

- `agent-logs stats --tool claude --since 30d --by tool-name` で `claude:Skill` は 97 回（91 セッション）。
- `agent-logs search '"skill"' --tool claude --kind tool_call -n 0 --json` の `text`（`{"skill":"<name>"}`）でスキル名ごとに数えられる。1 回 約 16 秒。
- 30 日分の結果: 16 種・97 回。`web-lookup` 34、`committing` 11、`skill-tools-cli` 6 などで、半分以上はこのリポジトリ外のスキル（`code-pm-verify` など）。22 回は名前を読めなかった。
- 130 件のうち呼び出しが記録されたのは数件だけ。多くのスキルは Skill ツールを通らず（`Read` で直接読む、他スキルから参照される）使われるため、呼び出し回数は利用頻度の代わりにならない。→ **v1 では入れない**。

## 5. ドッグフーディングの実行方法

### writing-skill-complex から流用できる部分

- 流用できるのは「新しいコンテキストのサブエージェントに現実的なシナリオを渡し、挙動をそのまま観察する」部分と、参照型スキルの検証観点（取り出し・応用・欠けている使い方）。
- 圧力シナリオ（時間・サンクコスト）と RED-GREEN-REFACTOR は規律型スキル向けで、ドッグフーディングには持ち込まない。

### 自動起動の確認

- Agent ツールのサブエージェントは親セッションと同じスキル集合（このリポジトリでは `.claude/skills/` の 10 件と有効なプラグイン）しか持たない。130 件の大半は自動起動を確かめられない。
- 代わりに `claude -p` を隔離ディレクトリで起動し、対象プラグインを `--plugin-dir` で読み込ませれば確かめられる。実際に試したコマンド（scratchpad で実行）:

  ```sh
  claude -p "Linear の公式ドキュメントを根拠に、GraphQL API で issue を作るときの認証方法を一言で教えて" \
    --model haiku --plugin-dir C:/C/ai/skills/plugins/topics \
    --tools "Read,Glob,Grep,Skill" --max-turns 6 \
    --no-session-persistence --output-format stream-json --verbose --setting-sources ""
  ```

  - `system/init` に `topics:linear-docs` などプラグインのスキルが並ぶ。
  - スキル名を出さない依頼で `tool_use: Skill {"skill": "topics:linear-docs", ...}` が出た＝ **description による自動起動を確認できた**。費用は haiku で $0.003。
  - `--tools` に `Skill` を入れないと起動しない（1 回目はこれで起動しなかった）。
  - スキル本体はエラーになった（Bash・WebFetch を外したため）。手順を最後まで試すには、外部への書き込みを止めたうえで既定のツールを渡す必要がある（Step4 で決める）。

- `--bare` は OAuth 認証を使わないので使えない。`--setting-sources ""` でユーザー・プロジェクトの設定（フック・他プラグイン）を切り離せる。
- `maintenance/plugin` も `--plugin-dir maintenance/plugin` で同じように読み込める。
