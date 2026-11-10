---
type: Plan Step
status: planning-research
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

## 決定事項・注意点／落とし穴

- **外部向けの操作**: GitHub リポジトリの作成・push・公開範囲の決定は、実行直前にユーザーの確認を取る。誤って private な内容（`.env`、`site/skills-site/.azure/`、ログ類）を push しないよう、切り出し後の各リポジトリで `git ls-files` と secretlint を走らせてから push する。
- **作業する clone**: `c:\C\ai` 自身で行う（ユーザー回答）。ただし `git filter-repo` は元のリポジトリを書き換えるので、切り出しは `c:\C\ai` から作った一時的なミラー clone（スクラッチ領域）で行い、`c:\C\ai` 側では `git submodule add` だけを行う。
- **追跡外ファイルの退避**: フォルダをサブモジュールの clone に置き換えると、ignore 対象（`.env`、`logs/`、`fb/`、`state/`、sqlite 等）が消える。置き換え前に `git status --ignored` で列挙して退避し、clone 後に戻す。
- **集約生成物のずれ**: サブモジュールで SKILL.md を変えても、アンブレラの `skill-catalog.json` 等はポインタを更新するまで古いまま。アンブレラの pre-commit（ポインタ更新時）と CI で再生成・検査する。
- **サブモジュールの detached HEAD**: 作業前に各サブモジュールでブランチを checkout する手順を README に書く。`just` レシピ（例: `just sub-status`、`just sub-sync`）を用意して、全サブモジュールの状態確認と更新を 1 コマンドにする。
- **並行作業**: 切り出しの間はアンブレラへの他の push を止めてもらう。終了後、他のエージェント・ユーザーの未 push の作業は新構成への移植が必要になる。事前に告知する。
- **CI の権限**: private サブモジュールなら checkout 用のトークン（deploy key か PAT）が要る。Azure Static Web Apps のデプロイと `tool-release.yml` のタグ付けがどちらのリポジトリで動くかを決める。

## ルール更新ポイント

- `maintenance/docs/repo-layout.md`（本ステップ）: サブモジュール一覧、生成物の所有権、ポインタ更新の手順、clone 手順。
- `maintenance/plugin/skills/committing/SKILL.md`（本ステップ）: サブモジュール内でのコミット → アンブレラのポインタ更新の 2 段階コミット手順。`meta.version` を上げる。
- `maintenance/docs/lefthook-automation.md`・`gh-actions-lifecycle.md`（本ステップ）: サブモジュール対応。

## 進め方

- **実行主体**: メインが 1 サブモジュールずつ進める（最初は依存の少ない `site/` で手順を検証し、次に `agent-compat/`、`tools/`、`skills/`）。外部操作のたびにユーザーへ確認する。
- **TODO 化**: サブモジュールごとに (切り出し → 検査 → ユーザー確認 → push → submodule add → CI 確認) を 1 TODO。最後に lefthook と CI の全体確認を 1 TODO。
