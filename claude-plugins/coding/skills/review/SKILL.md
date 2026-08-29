---
name: review
description: コードの差分を読み取り専用でレビューする。(1) 現在のブランチから指定したマージ先ブランチへPRを作成したと仮定してのブランチ間差分レビュー、または (2) まだコミットしていない変更(staged/unstaged/untrackedファイル)のレビューに対応する。実際のgit操作(checkout/merge/commit/push/add/stash等、状態を変更する操作)は一切行わない。「このブランチをmainにマージする想定でレビューして」「PRの差分を確認して」「mainへのマージ前チェックをして」のようにマージ先ブランチが分かっている差分レビュー、および「今の変更をレビューして」「コミット前にチェックして」「未コミットの変更を確認して」「git diffを見てレビューして」のような作業ツリーの変更レビュー、どちらの依頼にも使う。
argument-hint: [merge先ブランチ名 (省略可。未コミット変更のレビューでは不要)]
arguments: [target]
allowed-tools: Bash(python plugins/review/skills/review/*.py *)
# Python依存: pathspec (`.diffignore` で除外パターンを指定する場合のみ必要。事前に `pip install pathspec` でグローバルインストールしておくこと)
meta:
  tag: []
  requires_repo_tools: git, python
  requires_env: none
  dependencies: pathspec
  requires_install: pathspec
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.0
---

コードの差分をレビューする。**実際にgit状態を変更する操作(checkout/merge/commit/push/add/stashなど)は一切行わない。行うのは既存の状態の読み取り(diff/status/show)のみ。**

## レビュー種別を判定する

依頼内容から、以下のどちらかを判定する。判断がつかない場合はユーザーに確認する(推測で決めない)。

- **ブランチ間差分レビュー**: 現在のブランチ(マージ元)から指定したブランチ(マージ先)へPRを作成したと**仮定**した場合の差分をレビューする。マージ先ブランチが分かっている/指定されている、または「PRの差分」「マージ前チェック」のように依頼されている場合。
  → 詳細手順は同階層の `branch-diff.md`(`${CLAUDE_SKILL_DIR}/branch-diff.md`)を参照して従う。

- **未コミット変更レビュー**: 現在の作業ツリーにある、まだコミットしていない変更(staged/unstaged/untrackedファイル)をレビューする。マージ先ブランチの指定がなく、「今の変更を見て」「コミット前にレビューして」のように依頼されている場合。
  → 詳細手順は同階層の `uncommitted-diff.md`(`${CLAUDE_SKILL_DIR}/uncommitted-diff.md`)を参照して従う。

## 両レビューに共通する事項

- 差分取得スクリプトは読み取り専用のgitコマンドのみを使う。
- 差分は `temp/review/` 配下に出力される。分割ファイルが複数生成された場合は、まず `INDEX.md` を読んで全体像(ファイル別のstatus/行数)を把握してから、必要な `diff_XXXX.diff` だけを個別に読む。1ファイルのみで済んだ場合は標準出力に差分本文がそのまま出るため、追加でファイルを読む必要はない。
- 同階層の `.diffignore` に記載したパターン(`.gitignore` と同じ書式)にマッチするファイルは、レビュー対象から自動的に除外される。
- 取得した差分は、通常のコードレビューと同じ観点でレビューする(バグ・既存動作への影響・命名やスタイルの一貫性・テストの有無・意図しないファイルの混入など)。`original_lines` / `new_lines` は変更規模の把握に使う。
- 結果を報告する際は、以下を明記する。
  - どちらの種別のレビューか、および実際にgit状態を変更する操作は行っていないこと
  - 差分ファイルの出力先ディレクトリのパス
  - `.diffignore` によって除外されたファイルがあれば、その件数
