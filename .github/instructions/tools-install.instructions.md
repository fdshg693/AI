---
name: "tools/install instructions"
description: "Instructions for files in tools/install/"
applyTo: "tools/install/**"
---

# ツールインストール方法

各ツールのインストール方法をまとめる。同階層の `justfile` から実行可能。

```bash
just aim-local   # aim CLI (tools/aim) をエディタブルインストール
just tavily-local  # tav-cli の tav CLI をエディタブルインストール
just cline-personal-info  # cline-personal-info plugin (tools/cline-wrapper, cline-plugins/meta) を Cline にインストール
```

APIキー設定など、インストール後のセットアップは各ツールの README を参照（例: `tools/aim/README.md`、`tools/tav-cli/README.md`、`integrations\CLINE.md`）。

`cline-personal-info` は内部で Git Bash 経由に `cline plugin install` を叩く。PowerShell/cmd から `cline plugin install` を直に打つと `error: ENOENT: no such file or directory, uv_spawn 'npm'` で失敗するため（詳細は `integrations\CLINE.md`）。
