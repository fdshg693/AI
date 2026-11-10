---
type: Plan Step
status: implementing-done
---

# Step 7: 履歴付きでサブモジュールへ切り出す

> [00-overview.md](00-overview.md) の続き。04（links ツールと Junction 安全な走査）、05・06（意味的再編）が完了していること。00 の未決事項 1（GitHub リポジトリ名の詳細と、既存 `fdshg693/AI` を上書きするか）の回答が揃っていること。

## やること

- `skills/`、`tools/`、`agent-compat/`、`site/` を、`git filter-repo --subdirectory-filter`（05 で移動した履歴も辿れるように `--path` と `--path-rename` の組み合わせを検討）で履歴付きの別リポジトリに切り出す。アンブレラは `git init` から始めた（ユーザー回答）ので履歴は短い。`filter-repo` を使わず、各フォルダの中身を新しいリポジトリの初回コミットにしてもよい。簡単なほうを選ぶ。
- ユーザーの確認後に GitHub リポジトリを作成して push し、アンブレラ側では該当フォルダを `git submodule add` に置き換える。
- アンブレラとサブモジュールの両方で、lefthook・CI・ワークスペースが動く状態にする。

## 読むべきファイル

### 切り出しの前提

- 01 の調査結果（観点 D・E）
- `.github/workflows/*.yml`（`skill-site.yml`、`tools-site.yml`、`tool-release.yml`、`pr-agent.yml`、issue triage 系）と `.github/workflows/justfile`
- `lefthook.yml`、`tools/internal/precommit/__main__.py`（05 の後は `maintenance/scripts/precommit/`）
- `pyproject.toml`、`pnpm-workspace.yaml`、`mise.toml`、`package.json`
- `CONTRIBUTING.md`（OWNER/COLLABORATOR 限定の自動化の説明）

### 生成物の所有権

- 05・06 で更新した生成器の出力先一覧（どの生成物がどのリポジトリに属するか）

## 触るファイル

- 新規: 各サブモジュールの `.gitignore`（ルートの `.gitignore` はサブモジュールに効かない。`.env`、`*.pem`、`logs/`、`fb/`、`.venv/` などを必ず含める）
- 決める: リポジトリ単位の設定（`.gitattributes`、`.secretlintrc.json`、`commitlint.config.js`、`.prettierrc.json`、`.python-version`、`mise.toml`）を各サブモジュールに複製するか、アンブレラのものを参照させるか
- 新規: `.gitmodules`、各サブモジュールの `lefthook.yml`（アンブレラの設定を `extends` するか、サブモジュール専用の軽い設定）、`.github/workflows/`（サブモジュール側で必要なもの）
- 変更: アンブレラの `.github/workflows/*.yml`（`actions/checkout` に `submodules: recursive`、`paths:` フィルタをサブモジュールのポインタ更新に合わせる）
- 変更: `lefthook.yml`（アンブレラ側は集約生成物の再生成とポインタ更新の検査だけにする）
- 変更: `pyproject.toml`／`pnpm-workspace.yaml`（members はアンブレラに残す。01 の結果で、サブモジュール単体の開発用 `pyproject.toml` を別に持つか決める）
- 変更: `CONTRIBUTING.md`、`README.md`（clone 手順を `git clone --recurse-submodules` と `just links-sync` に）
- 変更: `maintenance/scripts/plugin_meta/**`（marketplace 生成器。Claude・Codex は `git-subdir`、Copilot は `github`+`path` を出力）
- 変更: `tools/skill-tools/skill_tools/source/__init__.py`（`GitHubSource` のサブモジュール対応）とそのテスト
- 変更: `.github/workflows/tool-release.yml` と `repo-tools.yaml`／tools-site の公開インストール手順（タグと URL を `AI-tools` 側へ）

## 決定事項・注意点／落とし穴

- **外部向けの操作**: GitHub リポジトリの作成・push・公開範囲の決定は、実行直前にユーザーの確認を取る。誤って private な内容（`.env`、`site/skills-site/.azure/`、ログ類）を push しないよう、切り出し後の各リポジトリで `git ls-files` と secretlint を走らせてから push する。
- **作業する clone**: `c:\C\ai` 自身で行う（ユーザー回答）。ただし `git filter-repo` は元のリポジトリを書き換えるので、切り出しは `c:\C\ai` から作った一時的なミラー clone（スクラッチ領域）で行い、`c:\C\ai` 側では `git submodule add` だけを行う。
- **追跡外ファイルの退避**: フォルダをサブモジュールの clone に置き換えると、ignore 対象（`.env`、`logs/`、`fb/`、`state/`、sqlite 等）が消える。置き換え前に `git status --ignored` で列挙して退避し、clone 後に戻す。
- **集約生成物のずれ**: サブモジュールで SKILL.md を変えても、アンブレラの `skill-catalog.json` 等はポインタを更新するまで古いまま。アンブレラの pre-commit（ポインタ更新時）と CI で再生成・検査する。
- **サブモジュールの detached HEAD**: 作業前に各サブモジュールでブランチを checkout する手順を README に書く。`just` レシピ（例: `just sub-status`、`just sub-sync`）を用意して、全サブモジュールの状態確認と更新を 1 コマンドにする。
- **並行作業**: 切り出しの間はアンブレラへの他の push を止めてもらう。終了後、他のエージェント・ユーザーの未 push の作業は新構成への移植が必要になる。事前に告知する。
- **CI の権限**: サブモジュールはすべて public（ユーザー回答）なので checkout 用のトークンは不要。Azure Static Web Apps のデプロイと `tool-release.yml` のタグ付けがどちらのリポジトリで動くかを決める。
- **marketplace の source（01-D）**: 集約 marketplace はアンブレラが生成・所有し、各エントリはサブモジュール側リポジトリを直接指す。Claude Code（`.claude-plugin/marketplace.json`）と Codex（`.agents/plugins/marketplace.json`）は `{"source":"git-subdir","url":"https://github.com/fdshg693/AI-skills.git","path":"plugins/<name>"}`、Copilot（`.github/plugin/marketplace.json`）は `{"source":"github","repo":"fdshg693/AI-skills","path":"plugins/<name>"}`。相対パス＋サブモジュールも Claude Code v2.1.295 以降なら動くが、古い版・update 時の同期漏れ・EDR による `--recurse-submodules` 拒否があるので使わない。`owner/repo` 形式は SSH を試みるので https URL で書く。`ref`／`sha` で固定するかは本ステップで決める（固定するならポインタ更新時に生成器が書き換える）。
- **Cursor（01-D）**: Cursor の marketplace は他リポジトリを指せない。現状ルートに Cursor 用 marketplace は無いので影響は無いが、作る場合はサブモジュール側に置く。
- **skill-tools の GitHub ソース（01-D）**: `GitHubSource` は Trees API の `type: commit`（サブモジュール）を黙って捨てるため、切り出した瞬間に `skills/`・`tools/_plugin` 配下が GitHub ソースから見えなくなる。**`skills/` を切り出す前に**、`.gitmodules` を読んでサブモジュール側リポジトリのツリー・blob を gitlink の SHA で取りに行く対応と、未対応時にエラーにする変更、テストを入れる。リポジトリが増えて API 呼び出しも増えるので、トークン（`GITHUB_TOKEN`）対応も検討する。
- **CI（01-D）**: サイトのビルドとリリースの `actions/checkout` に `submodules: recursive`。アンブレラ側の `paths:` はサブモジュールのパス自体（`skills`、`tools`、`site`）を列挙する（中身のパターンは gitlink 更新では発火しない見込み）。サブモジュール側への push だけではサイトが更新されないので、サブモジュール側から `repository_dispatch` で通知するかポインタ更新で足りるかを決める。`tool-release.yml` のタグは `AI-tools` 側に移すのが素直。公開インストール手順 `git+https://github.com/fdshg693/ai#subdirectory=tools/<name>` は `AI-tools` を指す URL に変える。
- **ワークスペース（01-E）**: `pyproject.toml`／`pnpm-workspace.yaml` の members はアンブレラにだけ置き、サブモジュール直下には `pyproject.toml`・`pnpm-workspace.yaml`・lockfile を置かない（置くと無警告で別の `.venv`／lockfile ができて二重管理になる）。未初期化のサブモジュールではメンバーが黙って無視され lock から落ちるので、lock の前に `git submodule update --init` を必須にし、CI で `uv lock --check` を走らせる。`uv tool install --editable <sub>/<pkg>` はそのまま動く。
- **lefthook（01-E）**: アンブレラのフックはサブモジュールのコミットで発火しない。各サブモジュールに薄い `lefthook.yml` を置き、`extends` でアンブレラ側の共通設定（例: `../maintenance/lefthook/common.yml`）を取り込む（単体 clone では黙って無視されるので方針と合う）。共通設定のジョブはルート相対パスに依存しない書き方にする。`git submodule foreach lefthook install` を just レシピにする。
- **実験 TODO（01-D で未確認）**: テスト用 public リポジトリで、(1) gitlink の変更で `paths:` が発火するか、(2) `git-subdir` のエントリで `/plugin install` が通るか、(3) `uv tool install git+...#subdirectory=` がサブモジュールを初期化するか、を確かめてから本番の切り出しに入る。

## ルール更新ポイント

- `maintenance/docs/repo-layout.md`（本ステップ）: サブモジュール一覧、生成物の所有権、ポインタ更新の手順、clone 手順。
- `maintenance/plugin/skills/committing/SKILL.md`（本ステップ）: サブモジュール内でのコミット → アンブレラのポインタ更新の 2 段階コミット手順。`meta.version` を上げる。
- `maintenance/docs/lefthook-automation.md`・`gh-actions-lifecycle.md`（本ステップ）: サブモジュール対応。

## 進め方

- **実行主体**: メインが 1 サブモジュールずつ進める（最初は依存の少ない `site/` で手順を検証し、次に `agent-compat/`、`tools/`、`skills/`）。外部操作のたびにユーザーへ確認する。
- **TODO 化**: サブモジュールごとに (切り出し → 検査 → ユーザー確認 → push → submodule add → CI 確認) を 1 TODO。最後に lefthook と CI の全体確認を 1 TODO。
- **コミット**: skill-tools の GitHub ソースのサブモジュール対応は、`skills/` を切り出す前に単独で 1 コミット。サブモジュールごとに、(a) 新リポジトリ側の初回コミット（切り出し直後、push 前）と、(b) アンブレラ側の 1 コミット（フォルダ削除 + `submodule add` + `.gitmodules` + 参照・CI の追従を同じコミットにする。分けると間の状態でパスが消える）。lefthook・CI の全体調整は最後に 1 コミット。ステップ完了時にプラン更新を 1 コミット（[コミット方針](00-overview.md#コミット方針全ステップ共通)）。

## 実行中に判明した変更

- 2026-11-10（01 完了時）: 01-D の go/no-go は GO。marketplace の source 形式、skill-tools `GitHubSource` のサブモジュール対応（切り出し前に必須）、CI・リリースの追従、ワークスペースと lefthook の置き方、事前の実験 TODO を「決定事項」「触るファイル」に反映した。サブモジュールは public なので CI トークンは不要と修正した。
- 2026-11-10（05 完了時）: SSOT yaml は `registry/` に移り、ルートに旧 skill-tools 向けの生成コピー（`ai-tools.yaml`・`repo-tools.yaml`・`repo-workflows.yaml`・`repo-hooks.yaml`）がある。サブモジュールからは `registry/` を Junction で参照する前提。`tools/` サブモジュールには `tools/_plugin/my-tools`（Claude Code プラグイン）と `tools/ai-usage` が含まれる。互換コピーをいつ消すか（skill-tools の利用者が `registry/` 対応版に上がった後）は切り出し時に決める。
- 2026-11-10（06 完了時）: [progress/06-agent-compat-results.md](progress/06-agent-compat-results.md)。切り出しに効く事実は次のとおり。
  - 他ツールのマニフェスト（`.codex-plugin/`・`.cursor-plugin/`・ルートの `plugin.json`）は `skills/plugins/ai-tools-knowledge/` の中にあり、手で保守する。`skills` サブモジュールが持ち、アンブレラは書き換えない。
  - アンブレラが生成するのは `.agents/plugins/marketplace.json`・`.github/plugin/marketplace.json` だけ。どちらも今は `./skills/plugins/ai-tools-knowledge` を local パスで指す。切り出し時に、`git-subdir`（Codex）・`github`+`path`（Copilot）へ変えるかを決める。
  - `.cline/skills/`・`.kilo/skills/`・`_agents/plugins/antigravity-meta/` は gitignore 済みの生成コピー（`just agent-compat-sync`）。サブモジュール化しても参照先（`skills/`）はアンブレラ配下にある。
  - `agent-compat/` には `agent-tooling/`・`formats/`（目印 `.format-samples`）・`docs/differences/`・README・AGENTS.md・CLAUDE.md がある。uv workspace の member は `agent-compat/agent-tooling`。
- 2026-11-10（07 完了時）: [progress/07-submodule-results.md](progress/07-submodule-results.md)。ユーザー回答: リポジトリ名は案どおり、検査が通れば都度 push してよい、事前の実験リポジトリは作らず本番で確認する、切り出し中は並行作業を止めた。`git filter-repo` の代わりに `git subtree split` を使った。計画外で、skill-tools の local source と、サイトの GitHub リンクのサブモジュール対応が要った。marketplace の `ref` は固定しない。`tool-release.yml` は AI-tools へ移した。残課題（`paths:` の発火、Tool release の再実行、アンブレラのシークレット、skill-tools の表示 URL）は progress に記載。
