---
type: Design Decision
title: tools/aimファミリーによる軽量AI自動化
description: Explains this repository's preference for automating repetitive, judgment-light text tasks (summarizing files, batch-answering the same question across many files, filling in SKILL.md metadata) with the lightweight tools/aim family (aim, aim-ask, aim-summarize) instead of a full AI coding tool session, and when fanning a prompt out across many paths in parallel is the right lever. Use when a task is "run the same simple prompt over N files/dirs" or "pick a model tier for a one-shot text task" and a full agentic session would be overkill.
tags: [tools, repo-meta]
generated: { by: reference_agent/cline-glm-5.2, at: 2026-08-09T14:39:30Z }
status: stable
---

# tools/aimファミリーによる軽量AI自動化

このリポジトリは、判断の軽い反復的なテキストタスク（ファイルの要約、複数ファイルへの同一質問、`SKILL.md`メタデータの補完）を、AIコーディングツールのセッションを1つ立ち上げるのではなく、`tools/aim`ファミリー（`aim` / `aim-ask` / `aim-summarize`）で処理する方針を取る。エージェント的なオーバーヘッド（ツール呼び出し、複数ターンの文脈保持）が要らないタスクにはこちらの方が軽く速い。

## 3つのツールの役割分担

- **`aim`**（[claude-plugins/my-tools/skills/aim-cli](../../claude-plugins/my-tools/skills/aim-cli/SKILL.md)） — systemプロンプトもマルチターンも扱わない、単発のuserメッセージ1件→応答テキスト1件のみのCLI。モデル選択は`minimax-m3`を基本線に、簡単すぎるタスクは`gpt-oss-120b`、`minimax-m3`で不十分なら`glm-5.2`/`gpt-5.6-luna`へエスカレーションする（表と判断基準は当該スキル参照）
- **`aim-ask`**（[claude-plugins/my-tools/skills/aim-ask](../../claude-plugins/my-tools/skills/aim-ask/SKILL.md)） — `aim`を使い、**同一プロンプト**を複数ファイル/ディレクトリへ`--jobs`の範囲で並列に投げ、パスと応答の対応を返す。ステートレスで1回きりの結果が欲しい場合に使う（例: ms-digestスキルが`mslearn`の大量検索結果を並列にAI抽出させる用途）
- **`aim-summarize`**（[claude-plugins/my-tools/skills/aim-summarize](../../claude-plugins/my-tools/skills/aim-summarize/SKILL.md)） — `aim-ask`と同様の並列ファン・アウトだが、結果を`.aim-use/summaries.db`（SQLite）へ永続化し、変更されたファイルだけ再要約する。使い捨てでなく蓄積したい要約タスク向け

## このリポジトリ自身も実際に使っている

`skill_meta_field_fill.py`（[skill-meta-fields](/repo-meta/skill-meta-fields.md)）は、各`SKILL.md`をエージェントに1件ずつ読ませて判断させる代わりに、`aim-ask`でスキルディレクトリ単位に投げて`meta:`の値を埋める。

## 使い分けの目安

- **aimファミリーへ**: タスクがステートレス（前のターンを覚える必要がない）、プロンプトが対象間でほぼ同一、必要な判断が1回のモデル呼び出しに収まる
- **エージェント/サブエージェントへ**: ツール呼び出しが要る、中間結果に依存する多段推論が要る、ファイルの書き込み・編集そのものを行わせたい

## モデル階層の選び方

固定のデフォルトではなくコスト/精度のトレードオフとして選ぶ。`minimax-m3`から始め、本当に簡単で精度を求められないタスクだけ`gpt-oss-120b`に下げ、`minimax-m3`の応答が明らかに不十分な場合にのみ`glm-5.2`/`gpt-5.6-luna`へ上げる。詳細な表は[aim-cli](../../claude-plugins/my-tools/skills/aim-cli/SKILL.md)を参照。

## 関連

- [claude-plugins/my-tools/skills/aim-cli](../../claude-plugins/my-tools/skills/aim-cli/SKILL.md) — `aim`自体の使い方・モデル選択表
- [claude-plugins/my-tools/skills/aim-ask](../../claude-plugins/my-tools/skills/aim-ask/SKILL.md) — 並列ファン・アウトの使い方
- [claude-plugins/my-tools/skills/aim-summarize](../../claude-plugins/my-tools/skills/aim-summarize/SKILL.md) — DB永続化つき要約の使い方
- [skill-meta-fields](/repo-meta/skill-meta-fields.md) — このリポジトリ自身がaim-askを使っている例

## このドキュメントの位置づけ

`repo-meta/`はこのリポジトリ自身のメンテナンス用であり、ユーザー向けプラグインではない。既存方針に従い、この内容を`ai-tools.yaml`へ登録しないこと。詳細は[ai-tools-config](/repo-meta/ai-tools-config.md)参照。
