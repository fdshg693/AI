---
type: AI Tool
title: Claude Code へのプラグイン導入方法
description: Explains how to add this repository's skills/plugins/ marketplace (seiwan-marketplace) to a user's own Claude Code environment — via /plugin marketplace add (GitHub or a local clone path), installing individual plugins, and auto-provisioning teammates via .claude/settings.json's extraKnownMarketplaces/enabledPlugins. Use when installing or updating this repo's Claude Code plugins into an external environment.
tags: [claude-code]
generated: { by: reference_agent/claude-sonnet-5, at: 2026-08-09T15:58:38Z }
status: stable
---

# Claude Code へのプラグイン導入方法

このレポジトリの [`skills/plugins/`](../../skills/plugins/) 以下にある自作プラグイン（skills, subagents など）を、自分の Claude Code 環境に取り込む方法を記載する。

配信は [`.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json) で定義されたマーケットプレイス経由で行う。
マーケットプレイス名は `seiwan-marketplace`、リポジトリは https://github.com/fdshg693/AI 。

## 1. マーケットプレイスを追加する

Claude Code 内のスラッシュコマンドで実行する場合:

```
/plugin marketplace add fdshg693/AI
```

CLI から実行する場合:

```shell
claude plugin marketplace add fdshg693/AI
```

### ローカルにクローン済みの場合（直接パス指定）

このレポジトリを既にローカルに `git clone` 済みなら、GitHub 経由で取得し直さずローカルパスを直接指定してマーケットプレイスを追加できる。マーケットプレイス名（`seiwan-marketplace`）は `marketplace.json` の内容から決まるため、追加元がリモートでもローカルパスでも変わらない。

```
/plugin marketplace add /path/to/AI
```

CLI から実行する場合:

```shell
claude plugin marketplace add /path/to/AI
```

以降の手順（インストール・確認・管理）はリモート追加時と同じ。

プラグイン本体はサブモジュールのリポジトリ（[fdshg693/AI-skills](https://github.com/fdshg693/AI-skills)・[fdshg693/AI-tools](https://github.com/fdshg693/AI-tools)）にあり、`marketplace.json` の各エントリは `git-subdir` でそれらを指す。そのため、ローカルパスで追加しても、プラグインは各リポジトリの GitHub 上の既定ブランチから取得される。手元で編集中のスキルを試すには、サブモジュール側で push するか、`claude --plugin-dir skills/plugins/<name>` で直接読み込む。

## 2. プラグインをインストールする

`marketplace.json` には次のプラグインが登録されている。必要なものだけを選んでインストールすればよい。

インストールは `/plugin install <プラグイン名>@seiwan-marketplace` の形式で行う。

```
/plugin install <plugin-name>@seiwan-marketplace
```

CLI から特定スコープ（例: プロジェクト単位）にインストールする場合:

```shell
claude plugin install <plugin-name>@seiwan-marketplace --scope project
```

### 2026-11 のプラグイン名・名前空間の変更

リポジトリ再編でプラグインの置き場所が `claude-plugins/` から `skills/plugins/` と `tools/_plugin/` に移り、次の名前が変わった。以前にインストールした利用者は、旧プラグインをアンインストールして新しい名前で入れ直す（スキルの呼び出し名 `<plugin>:<skill>` も変わる）。

| 旧                                         | 新                                 |
| ------------------------------------------ | ---------------------------------- |
| `meta`                                     | `cc-knowledge`                     |
| `my-tools-no-install`（web-lookup）        | `web-lookup`                       |
| `my-tools-no-install`（doc-transcription） | `doc-tools`                        |
| `my-tools:tav-lit`                         | `web-lookup:tav-lit`               |
| `coding:task-tracker`                      | `my-tools:task-tracker`            |
| `coding:parallel-agent-worktree`           | `my-tools:parallel-agent-worktree` |

ほかのプラグイン名（`cicd`・`coding`・`my-tools`・`no-code`・`others`・`special`・`subagents`・`topics`）は変わらない。

Codex・Cursor・Antigravity・Cline・Kilo・Copilot の使い方を説明するスキル（`codex-docs`・`cursor-skill-use` など）は、新しいプラグイン `ai-tools-knowledge` として Claude Code からも入れられる。Codex・Copilot のマーケットプレイスでも、旧 `meta` プラグインに代わってこのプラグインを配布する。

## 3. 確認・管理

```
/plugin list
/plugin disable <plugin-name>@seiwan-marketplace
/plugin uninstall <plugin-name>@seiwan-marketplace
```

マーケットプレイス側（`marketplace.json`）が更新された場合は次で反映する。

```
/reload-plugins
```

## チーム・複数プロジェクトへの自動導入（任意）

プロジェクトの `.claude/settings.json` に `extraKnownMarketplaces` / `enabledPlugins` を書いておくと、リポジトリを clone したメンバーに自動でマーケットプレイス追加・インストールが促される。

```json
{
  "extraKnownMarketplaces": {
    "seiwan-marketplace": {
      "source": { "source": "github", "repo": "fdshg693/AI" }
    }
  },
  "enabledPlugins": {
    "<plugin-name>@seiwan-marketplace": true
  }
}
```

## 補足: `my-tools` プラグインの前提ツール

`my-tools` プラグイン（`tools/_plugin/my-tools`）内の skill は 自作 CLI のインストール済を前提にしていることが多い。
事前に [cli-tools](cli-tools.md) の手順でインストールしておくこと。

## 関連

- [cli-tools](cli-tools.md) — `my-tools` プラグインが前提とする `aim`/`tav` CLI 自体のインストール手順
- [codex](codex.md) / [cline](cline.md) — 他のAIツールへの同種の導入手順
