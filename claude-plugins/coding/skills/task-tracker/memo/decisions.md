---
name: task-tracker-decisions
description: task-trackerスキルの設計判断とその理由（プラン作成時点のメモ）
metadata:
  type: memo
---

# 設計判断メモ

このファイルは [PLAN.md](../PLAN.md) の「決定事項・注意点」の詳細版。実装時・将来の見直し時に「なぜこうしたか」を追えるようにするためのもの。

## 1. 呼び出し形式: `/task-tracker <task-name>` 一本化

当初のユーザー指示は「ARGUMENTS[1]の内容をタスク名と認識」だった。スキルドキュメント（`writing-skill/skills-reference.md`）の `$ARGUMENTS[N]` 表記は0始まりなので、文字通り読むと「2番目の引数」を意味し `/task-tracker <何か> <task-name>` のような形式を示唆していた。

AskUserQuestionで確認したところ、実際には `/task-tracker <task-name>` のみを想定しており、「[1]」は言い間違い（1番目=最初、という自然言語的なカウント）だったことが判明。よって `$0` を素直にタスク名として扱う設計に確定。

**将来「start/resume/dumpのようなサブコマンドを増やしたい」という話が出た場合**は、`$0`をサブコマンド、`$1`をタスク名にする再設計が必要になる（このメモをその時に参照する）。

## 2. フック本体の設置場所: `.claude/hooks/` （skill frontmatter内ではない）

### ユーザーの当初要望

「スキル内にフックを定義」（skillのfrontmatterの`hooks`フィールドを使う想定だったと思われる。Claude Codeはこれを公式にサポートしている機能）。

### なぜ変更したか

このリポジトリには既に **hookを一元管理する仕組み**（[.claude/hooks/AGENTS.md](../../../../../.claude/hooks/AGENTS.md), [.claude/scripts/AGENTS.md](../../../../../.claude/scripts/AGENTS.md)）があり、「`.claude/hooks/*.py`にdocstring契約を書く → `hooks_manager.py sync` → `hooks.yml`で`enabled`管理 → `reflect`で`settings.json`に反映」という運用が確立している。この運用は「`settings.json`を手書きしない」ことを明確に目的としており、プロジェクト全体のフックがこの1箇所から見渡せることに価値がある。

skill frontmatterに直接`hooks`を書くと、この一元管理の外側に別のフック定義経路ができてしまい、「このリポジトリのフックは今何が有効か」を`hooks.yml`だけを見ても把握できなくなる（`/hooks`コマンドや`--debug hooks`では見えるが、hooks_manager側の可視性が失われる）。

### 技術的な懸念（副次的な理由）

skill frontmatterの`hooks`は「そのコンポーネントが動いている間のみ有効」という説明があり（[claude-plugins/meta/skills/writing-hooks/hooks.md](../../../meta/skills/writing-hooks/hooks.md)の「定義場所とスコープ」表）、`UserPromptExpansion`は「`/task-tracker ...`と入力された直後、SKILL.md本文がまだcontextに入る前」に発火するイベントである。「スキルが実際に動き出す前のタイミングで、そのスキル自身が定義したフックが確実に発火するか」は詳細ドキュメント上は確認しきれなかった（frontmatterのメタデータ自体はスキャン時に読まれるはずなので恐らく動くと推測されるが未検証）。

`.claude/hooks/`経由で`settings.json`に登録すれば、この発火タイミングの不確実性を考える必要がなくなる（セッション開始時から確実に登録されている）。

### 代替案（ユーザーが「やはりskill内に置きたい」と言った場合）

1. skill frontmatterに`hooks:`フィールドを書く設計に変更する
2. 実装後、**新規セッションで一発目から** `/task-tracker <name>` を叩いて `sessions.md` が生成されるか実地検証する（コールドスタート時の発火タイミングがまさに未検証ポイント）
3. 発火しない/不安定なら`.claude/hooks/`方式にフォールバックする

## 3. gitignore方針（未確定・要確認）

`sessions.md`に書かれる`session_id`は、このマシンの`~/.claude/projects/<project>/<session_id>.jsonl`を指す。他の開発者のマシンや他環境では実体を持たないローカル情報。

一方`CURRENT.md`はタスクの現状サマリであり、チームで共有する価値がある可能性がある（「このタスクは今どこまで進んでいるか」を他の開発者やAIエージェントも参照できる）。

**現時点の推奨（未確定）**: `sessions.md`と`temp/`はコミット対象外、`CURRENT.md`とその他ノートファイルはコミット対象、という非対称な運用。ただし「`.claude/tasks/`全体を非公開のスクラッチとして扱いたい」という考え方もあり得るため、実装前にユーザーに確認する。

## 4. `dump_sessions.py`を自己完結にする理由

`claude-plugins/meta/skills/claude-code-debugging/scripts/extract_log.py`に既に`transcript`サブコマンドがあり、機能的にはほぼ流用可能。しかし [writing-skill/writing.md](../../writing-skill/writing.md) のベストプラクティスに「既存スキルで代用できないか確認する」はあるが、**別スキルの実装ファイルに実行時依存する**のはスキルの自己完結性を損なう（`claude-code-debugging`スキルが将来リネーム・移動・削除された場合に`task-tracker`が壊れる）。

そのため、trascript jsonlの読み方（`~/.claude/projects/<project>/<session_id>.jsonl`、ドライブレター大小文字ゆれ対応等）という**知見だけ**を参考にし、コードは独立して持つ。
