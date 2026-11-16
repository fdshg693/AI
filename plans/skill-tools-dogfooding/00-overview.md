---
type: Plan
status: planning-breakdown
---

## 実装ステータス

- [x] [01-repo-setup.md](01-repo-setup.md) — アンブレラにプロジェクト用 `skill-tools.yaml` の受け皿を作る（example・gitignore・local-configs）
- [ ] [02-dogfood-install.md](02-dogfood-install.md) — スキルを実際に入れて使い、使い勝手の問題を洗い出す
- [ ] [03-fix-and-extend.md](03-fix-and-extend.md) — 洗い出した問題の修正・追加機能（02 の結果で確定）

# skill-tools ドッグフーディング 実装プラン - 概要

## 要件

- [tools/skill-tools/README.md](../../tools/skill-tools/README.md) の手順どおりに、このリポジトリ（アンブレラ `C:\C\ai`）へ Claude Code 用スキルをプロジェクト単位で入れる。まず `install-skills self`（`skill-tools-cli`）。
- このリポジトリの作業でよく使いそうなスキルを選んで追加で入れる。選定自体も `skill-tools search` / `list-skills` / `workflow` で行い、CLI の検索・選定体験も評価対象にする。
- 入れる・確認する・更新する・外すの一連を使い、詰まった点を記録する。必要なら skill-tools を修正・機能追加する。

## 実装ステップ

1. [01-repo-setup.md](01-repo-setup.md) — `skill-tools.example.yaml` をコミットし、実体の `skill-tools.yaml` と配置先 `.claude/skills/` を gitignore、`registry/local-configs.yaml` に宣言する
2. [02-dogfood-install.md](02-dogfood-install.md) — 調査ステップ。スキルを選んで入れ、一連のコマンドを使って問題を記録する（`skill-tools --fb` にも残す）
3. [03-fix-and-extend.md](03-fix-and-extend.md) — 02 の結果をもとに直すものを決め、`tools/skill-tools` を修正する（サブモジュール内コミット → アンブレラでポインタ更新）

## 主要な決定事項

| 決定                                                                                                               | 理由                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 配置先は Claude Code（`.claude/skills/`）だけ。`--target` の複数指定は今回試さない                                 | ユーザー判断。`.agents/` は既存のマーケットプレイス定義と同居するため                                                                            |
| `.claude/skills/` と実体の `skill-tools.yaml` はどちらも gitignore し、`skill-tools.example.yaml` だけコミットする | ユーザー判断。スキル実体はプラグインに 1 か所だけ置く原則（ルート README）と、ローカル設定は example だけコミットする規約（AGENTS.md）に合わせる |
| 配置方式は既定の `copy` から始め、`--mode link` は 02 で比較のために試す程度にとどめる                             | ドッグフーディングの主目的は通常の利用者の経路を通すこと                                                                                         |
| 修正対象は 02 で記録した問題から選ぶ。02 より前に機能を作り込まない                                                | 実際に使って困ったことだけを直す（想定で機能を足さない）                                                                                         |

## 変更/新規ファイル一覧

（各ファイルの役割・読むべき既存ファイルは各ステップを参照。03 の分は 02 の結果で確定する）

### 新規

- `skill-tools.example.yaml`（アンブレラ直下）
- `plans/skill-tools-dogfooding/progress/02-dogfood-log.md`

### 変更

- `.gitignore`
- `registry/local-configs.yaml`
- `README.md`（「取得」節のセットアップ手順に 1 行）
- `tools/skill-tools/**`（03。サブモジュール）

## ルール更新ポイント

- `AGENTS.md`（Step1）: 「ローカル設定ファイル」の箇条に `skill-tools.yaml` を足すかは、`registry/local-configs.yaml` への宣言で足りるなら足さない（宣言側が SSOT）。
- `tools/skill-tools/README.md`（Step3）: 追加・変更した挙動を Commands 節へ。
- `tools/_plugin/my-tools/skills/skill-tools-cli/SKILL.md`（Step3）: CLI の使い方が変わったら更新し、`meta.version` を上げる。

## 進め方

- **TODO化**: ステップ一覧の各項目を 1 TODO にする。各ステップの実行主体は各ステップファイルの「進め方」節に書く。
- 03 は 02 が完了するまで `planning-research` のまま置き、02 の結果で本文を書き直してから `ready` にする。
