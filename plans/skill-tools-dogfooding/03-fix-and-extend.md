---
type: Plan Step
status: planning-research
---

# Step 3: 洗い出した問題の修正・追加機能

> [02-dogfood-install.md](02-dogfood-install.md) の続き。Step2 の調査結果で本文を書き直してから `ready` にする。

## やること

Step2 の調査結果から直すものを選び、`tools/skill-tools` を修正する。README・`skill-tools-cli` スキルを追従させる。

現時点の候補（プラン作成時に気づいたもの。Step2 で実害を確かめてから採否を決める）:

- **宣言的なスキル同期**: 設定に入れたいスキルを列挙し（例: `skills.install` のような一覧）、manifest をそれに揃えるコマンド（`hooks sync` のスキル版）。clone 直後に `skill-tools.example.yaml` をコピーして 1 コマンドで揃えられるようにする
- **二重配置の警告**: プロジェクトに入れるスキルがグローバル（`~/.claude/skills`）やプラグインにも既にあるとき知らせる
- **未登録領域のスキル**: `maintenance/plugin/skills/` を入れられないことへの対応（入れられるようにするか、エラー時に「プラグインとして有効化する」案内を出すだけにするか）

## 読むべきファイル・実行推奨Grep

（Step2 の結果で確定する。現時点の見当）

**既存の同種実装（優先度: 高）**

- 読む: `tools/skill-tools/skill_tools/hooks/` の `hooks sync` の実装 — スキル同期を作るならこれに揃える
- 読む: `tools/skill-tools/skill_tools/install/` と `skill_tools/cli/` — install/update/remove の流れと manifest の扱い

**規約（優先度: 中）**

- 読む: `maintenance/plugin/skills/changing-skills-and-tools/SKILL.md` — ツール・スキル変更時の手順
- 読む: `tools/skill-tools/README.md` の Development 節 — テストの実行方法

## 触るファイル

（Step2 の結果で確定する）

- 変更: `tools/skill-tools/skill_tools/**`、`tools/skill-tools/tests/**`
- 変更: `tools/skill-tools/README.md`
- 変更: `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`（使い方が変わる場合。`meta.version` を上げる）
- 変更: `skill-tools.example.yaml`（宣言的同期を作った場合、入れるスキルの一覧を書く）、`README.md`（セットアップ手順）

## 決定事項・注意点／落とし穴

- `tools/` はサブモジュール。サブモジュール内でコミットしてからアンブレラで `git add tools` する 2 段階。作業前に detached HEAD なら `git switch main`（作業ブランチ運用に合わせる）。
- `skill-tools` は `.venv` の editable install（`C:\C\ai\.venv\Scripts\skill-tools`）で動いているので、修正はそのまま反映される。グローバルの `uv tool` 版とどちらが PATH で先かに注意する。
- 宣言的同期を作る場合、同期で「外す」動作は manifest 管理のスキルだけに限る（手で置いたスキルを消さない）。`hooks sync` と同じ安全策（drift で中止、`--force` は明示時のみ）に揃える。

## ルール更新ポイント

- `tools/skill-tools/README.md` の Commands 節: 追加・変更したコマンドの挙動
- `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`: 利用者が知るべき使い方の変更

## 進め方

- **実行主体**: メインエージェント。直す問題が互いに独立していて 3 件以上なら、問題ごとに `general-purpose` サブエージェントへ委譲（同じファイルを触るなら worktree isolation）。
- **TODO化**: 直す問題 1 件 = 1 TODO = 1 コミット（サブモジュール内）。最後にアンブレラでポインタ更新を 1 コミット。
