---
name: "tools/get-settings instructions"
description: "Instructions for files in tools/get-settings/"
applyTo: "tools/get-settings/**"
---

# AIコーディングツール設定取得ツール

様々なAIコーディングツール（Claude, Codex, ..）のユーザーレベル設定を取得するためのツール群。（レポジトリレベルの設定は拾わない）
これによって、ついつい忘れがちな全体設定を簡単に確認・編集できるようにすることが目的。

同階層にあるPythonスクリプトによって、これらの設定の取得(設定ファイル＋関連する環境変数)（ `settings/` フォルダにロード）や、変更して反映（ `settings/` フォルダを編集した上で、反映）を行うことができるようにするのが目的。

## 参考資料

設定ファイルの場所などを取得するための参考資料は以下
**実際に調査する中で資料が間違っているまだは不十分な箇所がある場合は、必ず参考資料側も更新すること**

- **設定項目は多くなく、些細なものが多い為、今回のスクリプトでは対象外とするツール**
  - [Cline](https://docs.cline.bot/getting-started/config)
  - [Cursor](https://cursor.com/docs/cli/reference/configuration)
  - [Antigravity](https://antigravity.google/docs/settings)

- Claude Code 設定
  - [Claude Code 設定](.claude\skills\claude-settings\SKILL.md)
  - [全体ドキュメント](.claude\skills\claude-cli-docs\SKILL.md)
- Codex 設定
  - [Codex 設定](codex-plugins\meta\skills\codex-settings\SKILL.md)
  - [全体ドキュメント](codex-plugins\meta\skills\codex-docs\SKILL.md)
