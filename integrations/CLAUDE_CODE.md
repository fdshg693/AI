# Claude Code へのプラグイン導入方法

このレポジトリの [`claude-plugins/`](../claude-plugins/) 以下にある自作プラグイン（skills, subagents など）を、自分の Claude Code 環境に取り込む方法を記載する。

配信は [`.claude-plugin/marketplace.json`](../.claude-plugin/marketplace.json) で定義されたマーケットプレイス経由で行う。
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

## 補足: `my-tool` プラグインの前提ツール

`my-tool` プラグイン内の skill は 自作 CLI のインストール済を前提にしていることが多い。
事前に [CLI_TOOLS.md](CLI_TOOLS.md) の手順でインストールしておくこと。
