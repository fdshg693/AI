# Step 2: リリースCIワークフロー + ドキュメント実装

✅完了

> [01-uv-workspace-source-research.md](01-uv-workspace-source-research.md) の続き。Step1で確定した対象パッケージ範囲を前提に実装する。

## 計画との差分

- `uv build` は対象パッケージのディレクトリ（workspaceメンバー）内で実行しても、`dist/` はそのディレクトリ配下ではなく**リポジトリルート直下**に出力されることを実装時に実機確認した（ローカルで `cd tools/aim && uv build` を検証）。そのため `gh release create` に渡すアセットパスは `${{ matrix.dir }}/dist/*` ではなく、リポジトリルート基準の `dist/*` にした。

## やること

Step1で確定した対象パッケージについて、mainブランチへのpush時にバージョン変更を検知し、パッケージごとに `<name>-v<version>` タグを打ってGitHub Releaseを発行するワークフロー（`.github/workflows/tool-release.yml`）を追加する。あわせて、ピン留めインストール手順を `tools/install/AGENTS.md` に追記する。

## 読むべきファイル・実行推奨Grep

**既存ワークフローのスタイル（権限設定・concurrency・トリガー）を踏襲するため（優先度: 高）**

- 読む: `.github/workflows/skill-site.yml` — `contents: write` 権限、`concurrency` グループ、`paths:` トリガーの書き方の基準
- 読む: `.github/workflows/pr-agent.yml` — `contents: write` を使う別ジョブの例
- Grep（`.github/workflows/` 配下）: `setup-uv` / `astral-sh` — Python/uvを使うCIが既存に無いことの確認（今回が初のPython系ワークフローになる想定の裏取り。無ければ `astral-sh/setup-uv` の導入が本ステップで新規になる）

**影響範囲を確認するため（優先度: 低）**

- 読む: `tools/install/justfile` — 既存の `aim-git`/`tavily-git` レシピとの役割分担（本プランではjustfileへのピン留め専用レシピ追加は対象外とする方針。`tools/install/AGENTS.md` 側でコマンド例を直接案内する）

## 触るファイル

### 新規

- `.github/workflows/tool-release.yml` — Step1で確定した対象パッケージのmatrixジョブ。各ジョブで対象ディレクトリの `uv version --output-format json`（`package_name`/`version` を一括取得できることを確認済み）を読み取り、対応するタグが `git ls-remote --exit-code --tags origin "refs/tags/<tag>"` で未検出なら `uv build` → `gh release create <tag> --target <sha> dist/*` でタグ作成とRelease発行を1コマンドで行う

### 変更

- `tools/install/AGENTS.md` — 「タグ+Releaseによるバージョン管理」節を追記（トリガー条件、タグ命名規則、`uv tool install "git+<repo_url>@<tag>#subdirectory=tools/<dir>"` によるピン留めインストール手順、対象パッケージ一覧）

## 決定事項・注意点／落とし穴

| 決定                                                                                                                       | 理由                                                                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| タグ・Release作成は `gh release create <tag> --target <sha>` 一発で行い、`git tag`+`git push` を別ステップに分けない       | タグ作成とRelease発行を1コマンドに寄せることで、タグだけ作られてReleaseが作られない中途半端な状態を避けられる。`gh` はGitHub Actionsランナーにプリインストール済みで追加アクション依存が不要                                                         |
| バージョン重複判定は `git ls-remote --tags origin` によるタグ存在チェックのみで行う（pathsフィルタでの差分検知は使わない） | pathsトリガーだけで判定しようとすると誤検知（同一pushで複数ファイルが変わったが実はバージョン未変更、等）が起きうる。タグ存在チェックの方が判定基準として単純で確実。`git ls-remote` はリモート参照なので `fetch-depth`/`fetch-tags` の調整も不要    |
| ワークフロー初回実行時、対象全パッケージに一斉に初回タグ+Releaseが作られる                                                 | 現バージョンに対応するタグが1つも存在しないため。想定内の挙動として実行前に認識しておく（意図しないRelease大量発行に驚かないための注意）                                                                                                             |
| `tools/install/justfile` へのピン留め専用レシピ追加は今回やらない                                                          | パッケージ名とディレクトリ名が一致しない箇所がある（例: `tav-cli` ディレクトリだが既存レシピ名は `tavily-git`）ため、汎用レシピ化すると命名マッピングの管理コストが増える。まずは `AGENTS.md` 側にコマンド例を書く形で運用し、需要が出てから検討する |
| バージョンを上げ忘れてmainにマージした場合、Releaseはサイレントにスキップされる                                            | Step1決定の「バージョン差分検出」方式の必然的な挙動。`$GITHUB_STEP_SUMMARY` に「スキップした」旨を1行出力し、Actions画面で確認だけはできるようにする                                                                                                 |

## ルール更新ポイント

`tools/install/AGENTS.md`（既存ファイルへの追記。対象パスに変更が無いためフロントマター不要、セクション見出しで対象を示す方式）:

- 見出し「## タグ+Releaseによるバージョン管理」を追加し、以下を記載する
  1. リリースはmainへのバージョン変更マージをトリガーに自動発行されること（スケジュール実行ではない）
  2. タグ命名規則 `<pyproject name>-v<version>`
  3. `uv tool install "git+<repo_url>@<tag>#subdirectory=tools/<dir>"` によるピン留めインストールのコマンド例
  4. 対象パッケージ一覧（Step1で確定した範囲）
