---
type: Plan Step
status: implementing-done
---

# Step3: スキルの危うさランキングを出す照会スクリプト

## やること

対象の `SKILL.md`（4 ルート `skills/plugins/`・`tools/_plugin/`・`agent-compat/_plugin/`・`maintenance/plugin/` の前方一致、祖先にも `SKILL.md` がある入れ子を除く。現在 130 件）を列挙し、要因ごとの値と合成点を計算して、危うい順に表（既定）または JSON で出す読み取り専用スクリプトを `maintenance/scripts/skill/query/` に足す。just レシピから呼べるようにし、テストを書く。

出力の 1 行に含めるもの:

- スキルの canonical ID（`.../SKILL.md`）、`meta.status`
- 最後の変更日（git）と経過日数、変更頻度（直近 30 日の実質コミット数）。取り込み以降に実質的な変更がないものは「基準日（2026-11-10 以前）」と出し、経過日数は基準日から数える
- 最後のドッグフーディング日と判定（台帳 `maintenance/skill-risk/dogfood.yaml`。無ければ「未実施」）
- 変化しやすさ（規則 `maintenance/skill-risk/volatility.yaml`。overrides → 最長 prefix → default の順。default に落ちたら「規則なし」）
- 依存先の変化: 最後の変更より後に変わった依存先（`requires_repo_tools`・`requires_skills`）の一覧
- 未対応 fb の件数（最後のドッグフーディングより新しい `--fb` ファイル。保存先はスキル名のディレクトリ `fb/skills/<name>/` なので名前で照合する。fb ディレクトリが無い端末では 0 として扱い、その旨を出す。カタログ未登録のスキルは「対象外」）
- 台帳の孤立エントリ（キーの `SKILL.md` が存在しない＝移動・改名された）の警告
- 合成点と、点を押し上げた上位の要因（1 行の理由）

## 読むべきファイル

- 列挙と frontmatter の読み方（最優先）
  - `maintenance/scripts/skill/query/list_skill_tool_impact.py` — 同じ `query/` の前例（引数、出力、エラー）
  - `maintenance/scripts/skill/util/skill_frontmatter.py`（`find_skill_md_files` を再利用する。生成コピーなどの除外は実装済み）・`skill_tool_graph.py` — `SKILL.md` の列挙と依存グラフ
  - `maintenance/scripts/skill/util/repo_tools_registry.py`・`skill/check/check_skill_repo_tools.py` の docstring — `requires_repo_tools` の値の解決と、`maintenance/plugin` 配下での意味の違い
- git の扱い
  - `maintenance/scripts/repo_git.py`・`skill/util/skill_version_bump_check.py` — サブモジュールをまたいだ git 呼び出しの前例
  - `maintenance/docs/repo-layout.md` の Junction 節 — 走査で Junction を辿らないこと
- 実行とテスト
  - `maintenance/scripts/justfile`・`maintenance/docs/justfile-conventions.md` — レシピの書き方
  - `maintenance/scripts/tests/test_repo_git.py` — 一時的なアンブレラとサブモジュールの git リポジトリを作るテストの前例

## 触るファイル

- 新規: `maintenance/scripts/skill/query/rank_skill_risk.py` — ランキング本体
- 新規: `maintenance/scripts/tests/test_rank_skill_risk.py` — 合成点、依存先の変化、台帳・fb が無い場合
- 変更: `maintenance/scripts/justfile` — `skill-risk` レシピ（`--top N`・`--json` を渡せる）
- 変更: `maintenance/scripts/skill/AGENTS.md` — `query/` の列挙に追加

## 決定事項・注意点／落とし穴

- 書き込みは一切しない（`query/` の約束）。lefthook にもつながない。
- git の呼び出しはスキル数 × 依存数になる。リポジトリ（アンブレラと各サブモジュール）ごとに `git log --no-renames --name-only` を 1 回だけ流してパスごとの最終日と件数を作る方式にし、件数に比例した起動をしない（Windows ではプロセス起動が遅い）。Step1 の試作でこの方式は依存先まで含めて約 1.6 秒。
- パス変換は `repo_git.owner()`（アンブレラ相対 → 所有リポジトリとその中のパス）を使う。スキルの変更はスキルのディレクトリ配下のどれかが変わったことで判定する（`SKILL.md` だけでなく `scripts/` なども含む）。
- 一括書き換えの除外: 件名が `refactor(repo)` か `chore(repo): import` で始まる、またはファイル数 > 100 のコミットを数えない。規則はスクリプト先頭の定数にする。
- 依存先の解決: `requires_repo_tools` は `skill_tool_graph` の `tool_keys_mentioned()` でキー・登録パスを解決し、解決できない値はリポジトリ相対のファイルパスとして扱う（`maintenance/plugin` 配下は「説明するファイル」を書いているため）。存在しなければ「未解決」と出す。`requires_skills` のうち `:` を含む名前（`superpowers:...` など外部プラグイン）は対象外。
- `requires_skills` の名前から canonical ID への変換で同じ名前が複数あれば、どちらかに決め打ちせず「曖昧」と出す。
- 生成コピー（目印 `.agent-compat-copy` のあるディレクトリ）と Junction の先を列挙に含めない。`find_skill_md_files` は `.claude/skills/`（sync-skills のコピー）・`temp/`・`templates/.claude/skills/` も返すので、4 ルートの前方一致で絞る。同じスキルを 2 回数えると順位が歪む。
- `deprecated` は既定で除外し、`--include-deprecated` で出す。
- 合成点の式はスクリプトの先頭に定数でまとめ、出力に内訳を必ず出す。重みを変えても内訳から順位を説明できるようにするため。
- サブモジュールが未初期化・detached HEAD でも落とさない。日付が取れないスキルは「不明」として上位に出す（確かめられないものは危うい扱い）。
- fb は端末ローカルなので、ランキングが端末によって変わりうることを出力の注記に出す。

## ルール更新ポイント

- `maintenance/scripts/skill/AGENTS.md`（本ステップ）: `query/` の列挙に `rank_skill_risk.py` を足す。
- 合成点の考え方の説明は Step4 の `maintenance/docs/` に書く。

## 進め方

- **実行主体**: メイン。完成後に一度全件で実行し、上位 10 件をユーザーに見せて直感と合うかを確かめる（ズレたら重みか規則 yaml を直す）。テスト結果の確認は読み取り専用で委任してよい。
- **TODO化**: 「列挙と git 日付」「台帳・規則・fb の合成と出力」「テスト + justfile + AGENTS.md」の 3 項目。

## 実行中に判明した変更

- 2026-11-19（Step1）: 対象範囲・30 日の変更頻度・基準日・一括コミットの除外規則・依存先の解決規則・fb の照合キーを反映し、再編より前の履歴をつなぐ話（`reorg/tables`）を削除した。
- 2026-11-19（Step2）: 入力の置き場所が `maintenance/skill-risk/volatility.yaml`・`maintenance/skill-risk/dogfood.yaml` に決まった。
- 2026-11-19（Step3 実行）: `rank_skill_risk.py`・テスト 6 件・`skill-risk` レシピ・`AGENTS.md`（`maintenance/scripts/` と `skill/` の 2 か所）を追加した。全 130 件で約 2.8 秒。合成点は次のとおり（定数はスクリプト先頭）。
  - 経過日数は「最後の変更」と「最後のドッグフーディング」の新しい方から数え、変化しやすさの重み（high 3 / medium 2 / low 1）を掛ける。ドッグフーディングした直後のスキルが上位に残らないようにするため。
  - 加点: 直近 30 日の実質コミット 1 件につき 2（上限 5 件）、変わった依存先 1 件につき 5（上限 3 件）、未ドッグフーディング 10、台帳の判定 `needs-fix` 20（壊れていると分かっていて未修正のもの。計画には無かった）、未対応 fb 1 件につき 5、git の日付が取れない「不明」50。
  - fb を受け付けるかどうかは `.claude-plugin/skill-catalog.json` の `path` で判定する（カタログが無ければ全件受け付ける扱い）。`maintenance/plugin` の 7 件が「n/a」になる。
  - 初回の結果: high 84 / medium 33 / low 13、基準日 61 件、依存先が変わったもの 29 件、未解決・曖昧な依存先は 0 件。上位は `ai-tools-knowledge`・`cc-knowledge` の、基準日のままで依存先が変わったスキル（1 位は `claude-code-openai-gateway`）。今は全件が未ドッグフーディングで履歴も 9 日分なので、順位は主に変化しやすさ × 日数と依存先の変化で決まる。
- 2026-11-19（Step3 完了）: 上位 10 件をユーザーが確認し、重みと規則は初期値のままにした。
