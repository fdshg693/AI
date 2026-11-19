---
type: Plan Step
status: implementing-done
---

# Step1: 危うさの判断に使える既存シグナルの調査

## やること

ランキングの入力に使えるシグナルが、このリポジトリで実際にどこまで取れるかを確かめ、Step2〜4 の未決事項を決める材料を揃える。コードは書かない。

## 調査観点

優先度順。

1. **最後の変更と変更頻度（git）**
   - サブモジュールの中のスキルディレクトリについて `git -C <submodule> log -1 --format=%cI -- <dir>` で日付が取れるか。アンブレラ側からのパス変換（`skills/plugins/...` → サブモジュール `skills` の `plugins/...`）は既存のどこかにあるか（`maintenance/scripts/repo_git.py`、`skill/util/skill_version_bump_check.py`）。
   - サブモジュールの履歴は再編（2026-11-10 の `refactor(repo): move ...`）から始まるので、`--follow` では再編より前に戻れない。再編より前の履歴はアンブレラに旧パスで残っている。旧パスを `maintenance/scripts/reorg/tables/*.json` で新パスにつなぐか、再編日より前を切り捨てて再編コミットを「変更なし」とみなすかを決める。
   - 一括書き換えのコミットを除外するか。対象は `chore(...)`、`skill-version-bump`、`refactor(repo)` のパス書き換えなど。conventional commit の type と、変わったファイル数で判定できるか。
   - 変更頻度の指標。例: 直近 90 日のコミット数、`fix` 系コミットが続いているか。
2. **変更の入りやすさ**
   - `meta.requires_repo_tools`（`repo-tools.yaml` のキーかパス。`skill/util/repo_tools_registry.py` で解決する。`maintenance/plugin` 配下では「説明するファイル」の意味）・`meta.requires_skills`（スキル名。名前→canonical ID の変換と同じ名前が複数ある場合の扱いが要る）と `skill/util/skill_tool_graph.py` で、スキル→依存先が引けるか。依存先の最後の変更日がスキルより新しい件数（＝依存先の変化に追随していない可能性）が出せるか。
   - プラグインごとに題材の変化しやすさを分けられるか（外部ツールの知識: `ai-tools-knowledge`・`cc-knowledge`・`web-lookup` など / 自作ツールの使い方: `tools/_plugin`・`agent-compat/_plugin` / 普遍的な手順: `coding` など）。136 件のプラグイン別件数。
   - `skill-maintenance` の `state/` や差分（`temp/skill-maintenance/diff/`）を「上流が変わった」シグナルとして読めるか。
3. **既存の品質・フィードバック**
   - `meta.status`（draft / experimental / stable / deprecated）の分布。deprecated を対象外にする、draft を高めにするなどの扱い。
   - `skill-tools --fb` の保存先（`tools/skill-tools/fb/skills/<name>/`）の件数と中身の形式。対応済みかどうかを区別する手段が無いこと（frontmatter を足さない仕様）をどう扱うか。カタログ未登録のスキル（`maintenance/plugin/`・`templates/.claude/skills/`）で `--fb` が終了コード 2 になることを確認する。
   - ランキングの対象範囲。`skill/util/skill_frontmatter.py` の `find_skill_md_files` が返す全件（`templates/.claude/skills/` を含む）と、4 つのルートの件数を比べる。
   - `audit-skills` ワークフローの出力を入力にできるか（費用が大きいので常時の入力にはしない想定）。
4. **利用頻度（任意）**
   - `agent-logs search "<skill名>" --kind tool_call` や `agent-logs stats --by tool-name` で、Claude Code の Skill ツール呼び出しをスキル別に数えられるか。数えられない場合は利用頻度を入れない。
5. **ドッグフーディングの実行方法**
   - `writing-skill-complex`（サブエージェントによる TDD 的検証）の手順のうち、ドッグフーディングに流用できる部分。
   - サブエージェントでスキルの自動起動を再現できるか（このリポジトリの `.claude/skills/` に入っていないスキルは起動しない。`skill-tools sync-skills` の `install_skills` との関係）。起動を確かめられないスキルは「スキル本文を渡して手順どおりに作業させる」に切り替える必要があるか。

## 調査結果

詳細ログと数値は [progress/01-research-results.md](progress/01-research-results.md)。

- **git の履歴は 2026-11-10 から始まる**（アンブレラも `71336a9 chore(repo): import existing working tree` が最初で、サブモジュールも同日の移動・取り込みから）。取り込み前の履歴はどこにも残っていないので、旧パスをつなぐ案は成り立たない。→ 切る。実質的な変更がない 67 件の最終変更日は「2026-11-10 以前（基準日）」として扱う。
- パス変換は既存の `repo_git.owner()`、列挙は `find_skill_md_files`、依存グラフは `skill_tool_graph.load_graph()` をそのまま使える。全リポジトリへの `git log --name-only` 1 回ずつで、依存先まで含めて約 1.6 秒。
- 一括書き換えは type だけでは分けられない（`refactor(tools)` の 453 ファイルのパス書き換えがある一方、`docs(skills)` の 13 SKILL.md 更新は本物）。「件名が `refactor(repo)` / `chore(repo): import` で始まる、またはファイル数 > 100」で除外すると移動・取り込みだけが落ちる。
- 依存先がスキルより新しく変わったスキルは 28 件。`maintenance/plugin` の `requires_repo_tools` はファイルパスなので、そのパスの最終変更日を使う。`superpowers:` など外部プラグインのスキルは対象外。4 ルート内に同名スキルは無い。
- `find_skill_md_files` は 153 件を返し、`.claude/skills/`（sync-skills のコピー）・`temp/`・`templates/.claude/skills/` を含む。4 ルートに絞り、`special` の入れ子 6 件（親にも `SKILL.md` がある）を外すと **130 件**。
- `meta.status` は stable 83 / experimental 45 / draft 8（うち 6 件は外す入れ子）/ deprecated 0。
- `skill-tools --fb` は 3 件しかなく今は信号にならない。保存先はスキル名単位（canonical ID ではない）。`maintenance/plugin` は終了コード 2（書き込みなし）を確認。カタログは 129 件 = 136 − `maintenance/plugin` 7 件。
- 利用頻度: `agent-logs search` で Skill ツールの呼び出しは数えられる（約 16 秒）が、30 日で 16 種・97 回、半分以上はこのリポジトリ外のスキル。Skill ツールを通らない使われ方が多く、利用頻度の代わりにならない。→ 入れない。
- ドッグフーディング: Agent ツールのサブエージェントは親と同じスキル集合しか持たないので、大半のスキルの自動起動を確かめられない。`claude -p --plugin-dir <プラグイン> --tools "...,Skill" --setting-sources "" --output-format stream-json` を scratch で実行すると、スキル名を出さない依頼で `tool_use: Skill {"skill": "topics:linear-docs"}` が出ることを確認した（haiku で $0.003）。`--tools` に `Skill` が無いと起動しない。

## 進め方

- **実行主体**: 観点 1・2・3 の既存コード確認は `Explore` サブエージェントに委任してよい。観点 4・5 は実際にコマンドを打つのでメインで行う。採否はメインで決める。
- **TODO化**: ステップ全体を 1 項目。結果を本プランの「調査結果」に要約し、overview の「未決事項」と Step2〜4 を書き換えてから完了にする。

## 実行中に判明した変更

- 2026-11-19: 観点 1・2・3 も Explore に委任せずメインで実行した（どれも数分で終わったため）。
