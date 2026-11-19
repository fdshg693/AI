---
type: Plan Step
status: planning-breakdown
---

# Step3: スキルの危うさランキングを出す照会スクリプト

## やること

全 `SKILL.md` を列挙し、要因ごとの値と合成点を計算して、危うい順に表（既定）または JSON で出す読み取り専用スクリプトを `maintenance/scripts/skill/query/` に足す。just レシピから呼べるようにし、テストを書く。

出力の 1 行に含めるもの:

- スキルの canonical ID（`.../SKILL.md`）、`meta.status`
- 最後の変更日（git）と経過日数、変更頻度（例: 直近 90 日のコミット数）
- 最後のドッグフーディング日と判定（台帳。無ければ「未実施」）
- 変化しやすさ（規則 yaml）
- 依存先の変化: 最後の変更より後に変わった依存先（`requires_repo_tools`・`requires_skills`）の一覧
- 未対応 fb の件数（最後のドッグフーディングより新しい `--fb` ファイル。fb ディレクトリが無い端末では 0 として扱い、その旨を出す。カタログ未登録のスキルは「対象外」）
- 台帳の孤立エントリ（キーの `SKILL.md` が存在しない＝移動・改名された）の警告
- 合成点と、点を押し上げた上位の要因（1 行の理由）

## 読むべきファイル

- 列挙と frontmatter の読み方（最優先）
  - `maintenance/scripts/skill/query/list_skill_tool_impact.py` — 同じ `query/` の前例（引数、出力、エラー）
  - `maintenance/scripts/skill/util/skill_frontmatter.py`（`find_skill_md_files` を再利用する。生成コピーなどの除外は実装済み）・`skill_tool_graph.py` — `SKILL.md` の列挙と依存グラフ
  - `maintenance/scripts/skill/util/repo_tools_registry.py`・`skill/check/check_skill_repo_tools.py` の docstring — `requires_repo_tools` の値の解決と、`maintenance/plugin` 配下での意味の違い
  - `maintenance/scripts/reorg/tables/*.json` — 再編より前の旧パスをつなぐ場合（Step1 の結論しだい）
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
- git の呼び出しはスキル数 × 依存数になる。リポジトリ（各サブモジュール、旧パスをつなぐならアンブレラも）ごとに `git log --name-only` を 1 回だけ流してパスごとの最終日と件数を作る方式にし、件数に比例した起動をしない（Windows ではプロセス起動が遅い）。一括書き換えのコミットの除外規則と再編より前の扱いは Step1 の結論に従う。
- `requires_skills` の名前から canonical ID への変換で同じ名前が複数あれば、どちらかに決め打ちせず「曖昧」と出す。
- 生成コピー（目印 `.agent-compat-copy` のあるディレクトリ）と Junction の先を列挙に含めない。同じスキルを 2 回数えると順位が歪む。
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
