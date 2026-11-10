# 08 実行記録（サブモジュール単体で開くための Junction・指示ファイル）

## コミット

| リポジトリ      | コミット                                   | 内容                                                                                                                                         |
| --------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| アンブレラ      | `10ff4e7`                                  | `just sub-agent-hooks-install`／`sub-agent-hooks-update`（`claude_hooks` 変数を `hooks-install` と共有）、repo-layout と exploring-this-repo |
| AI-skills       | `f7b7f16`                                  | `.links.yaml`・`.claude/skill-tools.hooks.yaml`・`.gitignore`・`AGENTS.md`・`CLAUDE.md`（新規）                                              |
| AI-tools        | `eff21d0`                                  | 同上（`AGENTS.md` は既存に追記）                                                                                                             |
| AI-agent-compat | `1c50de6`                                  | 同上（`AGENTS.md` は既存に追記）                                                                                                             |
| AI-site         | `578b11e`                                  | 同上（`AGENTS.md`・`CLAUDE.md` は新規）                                                                                                      |
| アンブレラ      | `eb4edf6`・`807d8a8`・`cbfea08`・`e47ef6b` | 各サブモジュールのポインタ更新                                                                                                               |

## 決めたこと

- **見せるもの**（正本は各 `.links.yaml`）: 全サブモジュールに `committing`。スキルを扱う `skills/`・`tools/` に `changing-skills-and-tools`、`tools/` にだけ `writing-skill`（`skills/` では自分の中にあり、自分の中を指す Junction は禁止なのでファイルとして読む）。`site/` 以外に `meta` と `_umbrella/maintenance-docs`。`_umbrella/registry` は全部。`agent-compat/` に `_umbrella/ai-tools-knowledge`、`site/` に `_umbrella/skills`。`exploring-this-repo`・`discovering-skills` は見せない（索引と skill-search エージェントがアンブレラ前提）。
- **指示ファイル**: サブモジュールの `CLAUDE.md` は `@./AGENTS.md` だけ。`AGENTS.md` は責務と「このフォルダだけを開いたとき」の固有事項だけにし、共通手順は repo-layout の「サブモジュールを単体で開く」へリンク（`../maintenance/docs/...` の相対リンク。アンブレラから見ても正しいリンクになる）。
- **フック**: 各サブモジュールの `.claude/skill-tools.hooks.yaml` は source `../..`（アンブレラ）。skill-tools は cwd を project にするので、`git submodule foreach` で実行する。入れるフックはアンブレラの claude 用と同じ 5 つ（すべて `distributable: true`）。生成物は各サブモジュールの `.gitignore` に追加（`.claude/settings*.json`・`.claude/hooks/`・`.claude/tasks/`・`.skill-tools/`）。

## 計画との差分

- 全サブモジュール向けの `links-sync` レシピは不要（04 で判明済み）。代わりにフック用のレシピを足した。
- アンブレラで開いたときの遅延ロード（下記）を見つけた。04 の設計は変えず、repo-layout に記録した。

## 検証

- `just links-sync` → `just links-check` がすべて ok。各サブモジュールの `git status --short -uall` に Junction・フックの生成物が出ない。
- `claude -p`（2.1 系、haiku）を各サブモジュールで起動:
  - スキル一覧が宣言どおり（skills: committing・changing-skills-and-tools・meta／tools: 左記＋writing-skill／agent-compat: committing・meta／site: committing）。
  - サブモジュールの `AGENTS.md`（`CLAUDE.md` 経由）と親の `CLAUDE.md` が読み込まれた。
  - フック: 各サブモジュールの `.claude/hooks/state/` がセッション後に作られた（`${CLAUDE_PROJECT_DIR}` がサブモジュールを指す）。
- アンブレラで起動: 起動時の一覧に `committing` 等は 0 件。`skills/`・`tools/` のファイルを Read すると `skills:committing`・`tools:committing`・`skills:meta`・`tools:meta`・`writing-skill` などがディレクトリ別スキルとして追加された。
- 参照先が消えた Junction を `.claude/skills/` に置いたフォルダ（scratchpad）でも `claude -p` は正常終了した。
- コミット時の lefthook（アンブレラ・各サブモジュール）がすべて通った。

## 残課題（09 へ）

- README の「取得」節にフックのインストール手順が無い（09 に追記済み）。
- `agents-rules` の再生成対象の確認（09 に追記済み）。
