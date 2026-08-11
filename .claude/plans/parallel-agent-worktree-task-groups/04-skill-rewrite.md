---
type: Plan Step
status: ready
---

# Step 4: `SKILL.md`/`README.md`の書き換え

> [01](01-issue-shape-and-project-config.md)〜[03](03-linear-cli-extension.md)の仕様・拡張を前提に、実際のオーケストレーションフローへ組み込む最終ステップ。

## やること

`claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md`を新方式に書き換える。

- 未着手issue検索を`.linear-cli/config.json`の`project`既定値によるグループ絞り込み前提にする（アクティブグループのみが検索対象になる）
- claim前に`show`で依存issue（`depends_on`）の完了確認を行い、未完了があれば見送って別候補を探す
- ブランチ解決ロジックを追加: ①対象`branch`のworktreeが`git worktree list`に既に存在する場合は再利用（トラッキングissueで占有中でないことを再確認した上で`EnterWorktree({path})`）／②存在せず`base_branch`がdefaultブランチと同じ場合は`EnterWorktree({name})`／③存在せず`base_branch`がdefaultと異なる場合は`git worktree add`で手動作成後`EnterWorktree({path})`
- 完了時、`search --label branch:<slug>`で同じブランチに未完了issueが残っているか確認し、残っていればpush済みでもworktreeを`keep`する（従来の「push済みならremove」を上書きする条件を追加）
- 次タスクグループへ進める手順（`.linear-cli/config.json`の`project`書き換え）を新設の節として追加。ユーザーの明示指示がある場合のみエージェントが実行する

`README.md`には設計意図（なぜラベルでなくProject+configか、なぜ`git worktree list`を正とするか）を追記し、[issue-shape.md](../../../claude-plugins/coding/skills/parallel-agent-worktree/issue-shape.md)・[issue-authoring.md](../../../claude-plugins/coding/skills/parallel-agent-worktree/issue-authoring.md)・本プランへのリンクを追加する。

## 読むべきファイル・実行推奨Grep

**既存フローを維持しつつ差分を入れるため（優先度: 高）**

- 読む: `claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md`全文 — 「全体の流れ」「Claim」「claim失敗時の後始末」「ExitWroktreeを能動的に呼ばない理由」「環境不足の可視化」の各節は骨格を維持し、差分だけ入れる
- 読む: [issue-shape.md](../../../claude-plugins/coding/skills/parallel-agent-worktree/issue-shape.md) / [issue-authoring.md](../../../claude-plugins/coding/skills/parallel-agent-worktree/issue-authoring.md) — Step1・2で確定したラベル名・descriptionヘッダ書式・config.json運用を正確に参照する
- ツール説明を再取得（ToolSearch `select:EnterWorktree,ExitWorktree`）— `path`/`name`の排他条件・「既に別worktreeセッションに入っている状態からのname新規作成不可」制約の正確な文言をSKILL.md本文に転記するため

**設計判断の書き方の前例として（優先度: 中）**

- 読む: `claude-plugins/coding/skills/parallel-agent-worktree/README.md` — 既存の「経緯」節の書き方（トラッキングissue方式への変更理由等）を踏襲して新規決定を追記する

## 触るファイル

### 変更

- `claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md`
- `claude-plugins/coding/skills/parallel-agent-worktree/README.md`

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                          | 理由                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 依存issue未完了時は当該issueを見送り、検索結果の別候補へ切り替える（待機はしない）                                                                                                            | 既存の「claimはベストエフォート・厳密な排他制御なし」という自律境界を踏襲する。1セッション=1タスクで完結する設計上、依存待ちのブロッキングは避け「今すぐ着手できるものを選ぶ」挙動に統一する     |
| worktree再利用の直前に、トラッキングissueのコメント一覧を確認し、対象worktree/branchが現在占有中でないことを再確認する                                                                        | `git worktree list`はディスク上の存在有無しか分からず、「別セッションが今まさにそこで作業中」かは分からない。二重書き込み事故を防ぐための最終チェックとして既存のトラッキングissue機構を流用する |
| `base_branch`がdefaultブランチと同じ場合のみ`EnterWorktree({name})`の単純経路を使う。異なる場合は`git worktree add`手動作成＋`EnterWorktree({path})`に切り替える                              | [00-overview.md](00-overview.md)の決定事項どおり、`worktree.baseRef`のグローバル設定切り替えを避けるため                                                                                         |
| 完了時のブランチ残issueチェックは「対象branchラベルを持つ全issueを取得し、完了扱いのissueを除いて何か残っているか」をエージェント側で判定する（`search`にステータス否定フィルタは追加しない） | Step3で追加する`--label`フィルタのみで実現でき、CLI側に新しいフィルタ演算子（否定条件）を増やさずに済む。最小限の拡張で足りる箇所は増やさない                                                    |
| 次タスクグループへの切り替え（`config.json`の`project`書き換え）はユーザーの明示指示がある場合のみエージェントが実行し、自動ループ化しない                                                    | 既存の「`ExitWorktree`を能動的に呼ばない理由」節と同じ自律境界の思想（ユーザー確認を経ない自動進行はスコープ外）を維持する                                                                       |

## ルール更新ポイント

`SKILL.md`のfrontmatter変更を伴うため、リポジトリ直下[AGENTS.md](../../../AGENTS.md)のSSOT規約に従い`meta.version`をbumpすること。コミット時のpre-commitフックの挙動・落とし穴は[docs/repo-meta/skill-md-commits.md](../../../docs/repo-meta/skill-md-commits.md)を参照。それ以外の別立てルールファイル更新は無い。

## 推奨の進め方

- **実行主体**: メインエージェント単独（実質2ファイルの書き換えで、既存の骨格を維持しながら差分を入れる作業のため分割の意味が薄い）。
- **TODO化**: SKILL.mdの変更箇所（検索条件・依存チェック・ブランチ解決・完了時判定・次グループ切り替え）を節単位でTODO化し、最後にREADME.mdの設計意図追記を1項目にする。
- **関連スキル**: 特になし。
