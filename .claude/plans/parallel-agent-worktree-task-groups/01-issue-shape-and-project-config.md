---
type: Plan Step
status: implementing-done
---

# Step 1: 期待するISSUEの姿・Linear側設定（`issue-shape.md`新規作成）

## やること

`claude-plugins/coding/skills/parallel-agent-worktree/`直下に`issue-shape.md`を新規作成し、「タスクグループ対応版」のISSUEが満たすべき型（ラベル・description構造化ヘッダ）と、それを支えるLinear/linear-cli側の設定（Project運用、`.linear-cli/config.json`の`project`既定値の使い方、ラベル命名規約、トラッキングissueコメント書式の拡張）を1ファイルにまとめる。Step2・Step3・Step4はこのファイルが定める仕様を前提に進む。

## 読むべきファイル・実行推奨Grep

**現行の仕組みを把握するため（優先度: 高）**

- 読む: `claude-plugins/coding/skills/parallel-agent-worktree/SKILL.md` — トラッキングissue方式・claim手順・コメント書式の現状
- 読む: `claude-plugins/my-tools/skills/linear-cli/SKILL.md` / `tools/linear-cli/README.md` — `search`/`create`/`update`の現在の引数（`--project`が既に存在すること、`--label`系が無いこと）
- 読む: `tools/linear-cli/.linear-cli/config.json.example` — `project`既定値が現状どう解決されるか（カレントディレクトリから親方向に探索、無ければteam/project絞り込み無し）

**影響範囲を確認するため（優先度: 中）**

- 読む: `tools/linear-cli/src/search.mjs` / `create.mjs` — `project`/`description`フィルタが現状どう実装されているか（Step3への引き継ぎ確認）

## 触るファイル

### 新規

- `claude-plugins/coding/skills/parallel-agent-worktree/issue-shape.md` — 期待するISSUEの姿・Linear側設定

## 決定事項・注意点／落とし穴

| 決定                                                                                                                                                                                                                                                                                       | 理由                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| タスクグループ＝Linear Project。「現在アクティブなグループ」は`.linear-cli/config.json`の`project`既定値1つで表す（同時に複数グループはアクティブにしない）                                                                                                                                | ユーザー要件が「次のタスクに進める」という**逐次**進行を想定しているため、単一のアクティブグループで足りる。複数グループ同時進行は非対応（過剰設計を避ける）                                                              |
| ブランチ共有単位を表すラベルは`branch:<slug>`固定書式。`slug`はgitブランチ名として妥当な文字列（小文字英数字とハイフンのみ）に制限する                                                                                                                                                     | ラベル名がそのままブランチ名の一部（またはブランチ名そのもの）として使われるため、書式を揃えないと`EnterWorktree`/`git worktree add`側で無効な名前になる                                                                  |
| 依存関係・ベースブランチはissue descriptionの先頭に構造化ヘッダを書く。書式は`depends_on: <identifier>[, <identifier>...]`（無ければ省略可）／`branch: <slug>`（必須）／`base_branch: <branch名>`（省略時はリポジトリのdefaultブランチ）を1行ずつ、`---`区切りの後に自由記述の本文を続ける | SKILL.md本体のfrontmatterと同じ見た目で、パースルールを新規に覚える負担を減らす。`branch`は依存の有無に関わらず全issueに必須（依存の無い単発issueも「自分専用の1issueだけのブランチ」を持つ、という一貫したモデルにする） |
| トラッキングissueの占有コメント（`host=..., worktree=...`）に`branch=<slug>`を追記する                                                                                                                                                                                                     | 人間が一覧を見たときの可読性向上が目的。worktree再利用の可否判定の正はあくまで`git worktree list`（[00-overview.md](00-overview.md)の決定事項）であり、このコメントはそれを裏付ける表示用の情報                           |
| `base_branch`は「リポジトリのdefaultブランチと同じ」場合のみを主経路としてサポート。それ以外を指定する運用も書式上は許すが、Step4側で「手動`git worktree add`＋`EnterWorktree({path})`」という追加コストがある旨をこのファイルに明記する                                                   | `EnterWorktree`が呼び出し単位でbase refを指定できない制約（[00-overview.md](00-overview.md)参照）はISSUEの書き手にも影響するため、ここで注意喚起しておかないとStep4実装時に初めて発覚する                                 |

## ルール更新ポイント

対象ファイル自体（`issue-shape.md`）がこのスキルの規約そのものであり、別立てのルールファイル更新は無い。frontmatterは付けない（SKILL.md/README.mdと同階層の説明資料であり、`.claude/plans`のOKF frontmatter規約の対象外）。

## 推奨の進め方

- **実行主体**: メインエージェント単独。設計判断そのものが成果物であり分割の余地が薄い。
- **TODO化**: 「issue-shape.md作成」を1TODO項目にする。
- **関連スキル**: 特になし（`writing-rules`はルールファイル向けのため対象外）。
