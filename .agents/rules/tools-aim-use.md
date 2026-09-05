---
trigger: glob
glob: tools/aim-use/**
description:
---

# aim-use — モデル呼び出しCLIツールを基盤とした便利ツール群

**関連スキル（基盤の aim CLI 自体）: `claude-plugins\my-tools\skills\aim-cli`**

aim CLI がインストールされている前提で、様々なAI機能を提供する便利ツール群。各ツールにも個別の使い方スキルがある（下記「ツール一覧」参照）。

## ツール一覧

- [aim-summarize/](aim-summarize/) — リポジトリ内のファイルをファイル単位で要約し、SQLite DBに保存するCLIツール（`aim-summarize` コマンド）。詳細は [aim-summarize/README.md](aim-summarize/README.md) 参照。関連スキル: `claude-plugins\my-tools\skills\aim-summarize`
- [aim-ask/](aim-ask/) — 指定した複数ファイルに同一プロンプトを並列に投げ、パスと応答の対応付きで結果を返すステートレスなCLIツール（`aim-ask` コマンド）。詳細は [aim-ask/README.md](aim-ask/README.md) 参照。関連スキル: `claude-plugins\my-tools\skills\aim-ask`

## メンテナンス上の注意

- 各ツールのCLIオプション・設定ファイル形式・挙動を変更した場合、対応する `claude-plugins\my-tools\skills\<tool>\SKILL.md` も同じ変更の中で更新すること。スキル側は自動追随しないため、ツールとスキルの内容が食い違ったまま放置されないようにする。
