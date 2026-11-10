# 04 実行記録（Junction マニフェストと links ツール、スキャナの Junction 除外）

## コミット

| コミット  | 内容                                                                                                                                                                                                                                                                                                                                                    |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `4ee4248` | `.umbrella-root`、`tools/internal/links/`（`python -m links sync\|check\|clean\|post-checkout`）、`links-*` レシピ（tools/internal とルートの justfile）、lefthook `post-checkout`、`docs/repo-wide/repo-layout.md`、ルート `AGENTS.md`・`tools/internal/AGENTS.md` の規約、`tools/internal/tests/test_links.py`                                        |
| `e533f03` | Python の走査箇所: tools/internal の `find_skill_md_files` と生成器 3 本、skill-tools（`fs_links.py` を新設し `is_symlink()` 15 箇所を置き換え、git 一覧で Junction 越しのファイルを数えない、`_remove_directory` が Junction を rmtree しない）、agent-tooling（`core/fs_links.py`、`rglob` 5 箇所と `sessions.py`、generated を再生成）、agents-rules |
| `e279426` | `uv.lock`（skill-tools・agents-rules の自動 patch バンプ）                                                                                                                                                                                                                                                                                              |
| `efed799` | ルート `conftest.py`（pytest の収集で Junction を飛ばす）、`patch-csp-header.mjs`                                                                                                                                                                                                                                                                       |

## 決めたこと

- **マニフェストの置き場所**: 各リポジトリのルート直下だけ（アンブレラと、チェックアウト済みサブモジュールを再帰で）。`path` はそのリポジトリのルート相対、`target` はアンブレラのルート相対。キーは `path`・`target`・`why` のみ。
- **checkout 対策**: 手順（古いコミットの前に `links-clean`、後で `links-sync`）を repo-layout に書き、lefthook `post-checkout` で事後警告する（常に exit 0）。`check` も「Junction のパスの下に追跡ファイルがある」をエラー、「過去に追跡されていたパス」を警告にする。防止はできない（Git に pre-checkout フックが無い）。
- **共通 util は 1 か所にしなかった**: `is_link_like` を tools/internal（`links/fs.py`）、skill-tools（`skill_tools/fs_links.py`）、agent-tooling（`core/fs_links.py`）、agents-rules（`generate.py` 内）、ルート `conftest.py` に同じ実装で持つ。skill-tools・agent-tooling・agents-rules は単独配布するため、互いに依存させない。判定は `os.lstat` の `st_reparse_tag == IO_REPARSE_TAG_MOUNT_POINT`（`is_junction()` は 3.12 からで、配布物は `>=3.11`）。
- **除外設定**: prettier・ruff は不要（01 の結果どおり）。pytest は `norecursedirs` ではパターンしか書けないので、ルート `conftest.py` の `pytest_ignore_collect` にした。
- **Junction 作成**: `cmd /c mklink /J`。除去は `is_link_like` を確認してから `os.rmdir`（rmtree は使わない）。

## 計画との差分

- links ツールは最初から `maintenance/scripts/links/` には置かず、`tools/internal/links/` に置いた（05 で移す）。repo-layout も `docs/repo-wide/` に置いた（05 で移す）。
- 08 で予定していた「`links-sync` を全サブモジュールに対して実行するレシピ」は不要になった。`links` がアンブレラから再帰でサブモジュールの `.links.yaml` を読む。
- `.claude/rules` の走査は Junction を辿らない側に揃えた。Python の `rglob("**")` は本物の symlink ディレクトリにも入らないので、Junction だけ入っていた挙動の不一致を直したことになる。symlink の**ファイル**は従来どおり読む。走査の起点そのもの（`.claude/rules` や `.claude/skills` 全体）が Junction の場合は読まれることを確認した（08 で使う形）。
- 06 の「生成コピーを 04 の除外の仕組みに登録する」は、今回の仕組み（Junction 判定）では扱えない。生成コピーは実ディレクトリなので、06 でパスによる除外を別に足す必要がある（06 に追記）。
- `claude-plugins/special/skills/{skill-group,command-group}` の `glob("**/SKILL.md")` は対象のスキルフォルダ内だけを走査するので直していない。

## 検証（`temp/`、終了後に `links clean` してから削除）

- 実験リポジトリで `sync` → `check` → `git status` が空 → `git clean -fdx` で Junction だけ消え参照先は無事 → `check` が欠落を検出 → `sync` で復旧 → `clean` で参照先が無事。
- 宣言の検証: 祖先を指す・Junction の中を指す・重なり・`..`・未知キーがそれぞれエラー。宣言外の Junction を `check` が検出。
- 01-A の checkout 危険を再現（追跡していたパスへの `checkout` で参照先の `SKILL.md` が上書きされた）。`post-checkout` が警告し、`check` がエラーにした。
- スキャナ: `sub/.claude/skills`・`sub/.claude/rules` を Junction にした実験リポジトリで、`find_skill_md_files`・skill-tools `LocalSource`・agent-tooling `find_files`・agents-rules `discover_agents` がどれも 1 回だけ数えた。pytest は祖先を指す Junction があっても 1 件だけ収集した。
- テスト: tools/internal 29（+ agents-rules 8）、skill-tools 302、agent-tooling 248 passed。本リポジトリで `just links-check` が成功（宣言・Junction とも無し）。生成器の再実行で生成物に差分なし。
- 01 の実験で残っている `temp/cc-exp/` の Junction 3 つは本ステップでは触っていない。
