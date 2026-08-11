---
type: Setup Guide
title: このリポジトリのCLIツールのインストール方法
description: Explains how to install this repository's own CLI tools (aim, tav-cli) that some skills/scripts assume are already present, via tools/install/justfile's *-local (editable, for a cloned checkout) and *-git (uv tool install from a git URL, no clone needed) recipe pairs. Use when a skill or script fails because a prerequisite CLI (aim, tav) isn't installed, or when deciding whether to install editable-local vs git-remote.
tags: [tools]
generated: { by: reference_agent/claude-sonnet-5, at: 2026-08-09T15:58:38Z }
status: stable
---

# CLI ツールインストール

幾つかのスキルやスクリプトで前提となっている、CLIツールのインストール方法を記載する

インストールコマンドは `tools\install\justfile` を参照。各ツールとも次の2通りのインストール方法を用意している。

- **local**（`*-local` レシピ）: リポジトリを clone 済みの開発者向け。エディタブルインストール（`uv tool install --editable`、`pip install -e` の代替）なので、ソースを編集すれば即座に反映される。
- **git**（`*-git` レシピ）: リポジトリを clone せずに手軽に入れたい場合向け。`uv tool install "git+<repo_url>#subdirectory=..."` でGitHub上のソースを直接インストールする。エディタブルではないため、更新を取り込むには同じコマンドを再実行する。`tools\install\justfile` 内の `repo_url` を実際のリポジトリURLに置き換えてから使うこと。

## 1. aim CLI

- `tools\aim\README.md` を参照。
- インストール: リポジトリルートから `just -f tools/install/justfile aim-local`（clone済み）または `just -f tools/install/justfile aim-git`（clone不要）

## 2. tav-cli

- `tools\tav-cli\README.md` を参照。Tavily SDK を利用する検索・抽出・サイトマップ・クロール・Research 用の `tav` CLI ラッパーです。
- インストール: リポジトリルートから `just -f tools/install/justfile tavily-local`（clone済み）または `just -f tools/install/justfile tavily-git`（clone不要）
- 実行前に `tools\tav-cli\.env` へ `TAVILY_API_KEY` を設定するか、環境変数に設定してください。

インストール後は、例えば次のように実行します。

```bash
tav search "Microsoft Fabric overview" --topic msfabric_overview
```

## 関連

- [claude-code](claude-code.md) — `my-tools` プラグインなど、ここでインストールしたCLIを前提にするAIツール側の導入手順
