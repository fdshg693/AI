---
type: Plan Step
status: planning-breakdown
---

# Step 2: スキルを入れて使い、使い勝手の問題を洗い出す

> [01-repo-setup.md](01-repo-setup.md) の続き。調査ステップ。詳細ログ → `progress/02-dogfood-log.md`（実行時に作る）

## やること

`tools/skill-tools/README.md` だけを手引きに、このリポジトリへスキルを入れて一連のコマンドを使う。詰まった点・分かりにくい点・欲しい機能を記録し、Step3 で直すものの候補にする。このステップではコードを直さない。

## 調査観点

**A. 自己インストールと選定**

- `skill-tools install-skills self --dry-run` → 本番。グローバル（`~/.claude/skills/skill-tools-cli`）にも同じスキルが入っている。プロジェクトとグローバルの二重配置を CLI が教えてくれるか
- 候補選び: `skill-tools search --query "..."`（「スキルを書きたい」「フックを書きたい」「コミットの手順」「リポジトリ内のコードを調べたい」など、このリポジトリでよくある作業の言葉で）と `list-skills` で選ぶ。index が古い・無いときの案内が分かりやすいか
- 入れる候補（検索結果で入れ替えてよい）: `writing-skill`、`writing-hooks`、`writing-rules`、`writing-plugins`、`okf-spec`、`codegraph-docs`、`gh-pr`、`systematic-debugging`、`review`、`claude-settings`

**B. 一連の操作**

- `install-skills`（名前・canonical ID・source path の各選択子）、`installed-skills`（TSV/JSON）、`update-skills --dry-run`、`remove-skills --dry-run` → 本番
- 名前が衝突するスキル（`test1`/`test2`/`test3` が `special` プラグインに 2 つずつある）を名前で指定したときのエラーと候補表示
- 配置したファイルを手で編集してから `update-skills` → drift 検出のメッセージ
- `--mode link` を 1 つだけ試し、`store list` / `store gc --dry-run` を見る
- `workflow list` / `workflow show` で、入れたスキルとの関係が分かるか

**C. 実際の使用感**

- 新しいセッションで入れたスキルが Claude Code に読み込まれるか（スキル一覧に出るか、description が発火するか）
- `maintenance/plugin/skills/`（`committing`・`exploring-this-repo`・`discovering-skills` など、このリポジトリで一番よく使うスキル）は `ai-tools.yaml` 未登録で入れられない。この制約が実害になるかを評価する（README は「未登録領域は対象にしない」と明記している）
- 入れたいスキルを宣言して揃える手段（フックの `hooks sync` に相当するもの）が無いことが、clone 直後のセットアップで困るか

**D. 記録の仕方**

- 問題ごとに `skill-tools --fb <対象> --fb-text "..."` でも残し、FB 機能自体の使い勝手も評価する

## 調査結果

（実行後に、問題の一覧を「重さ（バグ／分かりにくい／欲しい機能）・再現コマンド・Step3 で直すか」の 1 行ずつで書く。詳細ログは progress へ）

## 進め方

- **実行主体**: メインエージェント。ユーザーと相談しながら入れるスキルを決め、新しいセッションでの読み込み確認（観点 C）はユーザーに依頼する。
- **TODO化**: 観点 A〜D を 1 項目ずつ。完了時に調査結果を本文へ書き、Step3 の本文を書き直してから完了にする。
