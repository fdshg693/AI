---
# Claude CLI と Claude Code の取得スクリプト、および同ディレクトリ配下の他スキルに依存する。
# 取得とファイル変更を伴うため、ユーザーが明示的に呼び出した場合だけ使う。
name: skill-maintenance
description: Maintains the Claude-related skills under `.claude/skills` by refreshing the Claude CLI help snapshot and Claude Code documentation snapshot, inspecting semantic changes, and updating affected skills. Use when explicitly checking whether those skills are stale after a Claude CLI or Claude Code documentation update.
disable-model-invocation: true
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/*.py *)
meta:
  requires_repo_tools: tools/internal/plugin_meta/generate/generate_skills_catalog_md.py
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: claude-cli-docs, claude-code-docs
  status: experimental
  description: no description
  version: 1.0.2
---

!`python ${CLAUDE_SKILL_DIR}/scripts/refresh_and_diff.py`

# スキルメンテナンス

`.claude/skills` 配下の Claude 関連スキルを、現在の Claude CLI と Claude Code 公式ドキュメントに追随させる。対象のスナップショットを更新し、意味のある差分に関係するスキルだけを修正する。

## 手順

1. **取得と差分生成の結果を確認する**

   スキル起動時に次の動的コンテキストが実行される。

   ```text
   python ${CLAUDE_SKILL_DIR}/scripts/refresh_and_diff.py
   ```

   このスクリプトは、次の2本を `--force` 付きで実行し、実行後の内容を Python で比較する。

   - `${CLAUDE_SKILL_DIR}/../claude-cli-docs/generate_claude_help_yaml.py`
   - `${CLAUDE_SKILL_DIR}/../claude-code-docs/download_claude_code_reference.py`

   比較対象の「変更前」は実行直前の `output/` の内容ではなく、`.claude/skills/skill-maintenance/state/` に保存されている「前回このスクリプトを実行した時点」のスナップショットである。`output/` が別経路（生成スクリプトの直接実行、手動編集、git checkout 等）で更新されていても、このスナップショットは本スクリプトの実行時にしか書き換わらないため影響を受けない。そのぶん、別経路での更新が既に反映済みの変更を再度差分として拾う可能性があるが、これは許容する。スナップショットは毎回の実行後に最新内容へ更新される（`state/` 配下は git 管理対象外）。

   取得時刻だけの差分は除外し、ソースごとの完全な unified diff を `temp/skill-maintenance/diff/` フォルダ配下に対象ごとの個別ファイルとして書き出す（例: `claude-cli-help.diff`, `claude-code-reference.diff`, `claude-code-full-reference.diff`）。動的コンテキストの出力には、書き出されたファイル一覧と差分の有無だけが表示される。**この差分ファイルは自分で直接読まない。** 差分は巨大になりやすく、そのままコンテキストに載せると以降の作業を圧迫する。

2. **取得失敗を切り分ける**

   どちらかの生成スクリプトが失敗した場合、そのソースを最新とみなさない。失敗理由（`claude` CLI の未導入、ネットワーク、依存パッケージなど）を報告し、成功したソースの差分だけを処理する。両方とも失敗した場合はスキル更新を行わず、原因と再実行条件を報告する。

3. **差分をサブエージェントに要約させる**

   `temp/skill-maintenance/diff/` に書き出された差分ファイルごとに、Agent ツール（`general-purpose` 等、通常の新規サブエージェント）を1つ起動し、そのファイルを読ませて要約させる。要約対象は、意味のある変更点（追加・変更・削除されたフラグ、サブコマンド、設定名、機能名、ドキュメント URL/slug）に限定し、差分そのものの引用や整形上のノイズは含めないよう指示する。複数ファイルがある場合は並列に起動してよい。

   サブエージェントへの指示に最低限含めるもの:
   - 読ませる差分ファイルの絶対パス（`temp/skill-maintenance/diff/*.diff`）
   - 「差分全体を引用せず、影響範囲の特定に使える変更点だけを箇条書きで返す」という要件
   - どのソース（Claude CLI / Claude Code ドキュメント）由来の差分かという文脈

4. **影響を受けるスキルを特定する**

   サブエージェントの要約（差分ファイルそのものではない）に現れたフラグ、サブコマンド、設定名、機能名、ドキュメント URL/slug を手がかりに、`.claude/skills` 配下の `SKILL.md` と参照ファイルを検索する。

   - CLI の差分は `claude-cli-docs` と `claude-cli-use`、および `claude` コマンドの仕様を直接記述するスキルを確認する。
   - Claude Code ドキュメントの差分は、該当 URL/slug や機能名を参照するスキルを確認する。
   - 関係のないスキルは変更しない。スナップショットの変更だけで説明・手順が変わらない場合も変更しない。
   - 要約だけでは影響範囲を判断できない場合に限り、該当箇所を絞った上で差分ファイルの該当部分だけを読む（ファイル全体は読まない）。

5. **関連スキルを更新する**

   更新対象のスキルを読み、古い仕様、例、コマンド、参照先、制約だけを差分に基づいて修正する。公式ドキュメントにない仕様を推測して追加しない。既存のユーザー変更を保持し、編集には通常のファイル編集手段を使う。

   `CATALOG.md` は生成物なので直接編集しない。スキルの追加・削除・frontmatter変更が発生した場合だけ、リポジトリルートから次を実行して再生成する。

   ```text
   uv run --directory tools/internal python -m plugin_meta.generate.generate_skills_catalog_md
   ```

6. **検証して報告する**

   変更した `SKILL.md` の frontmatter と参照パスを確認し、サブエージェントの要約に対応していることを再確認する。最後に、取得結果、要約内容の要点、変更したスキル、更新しなかった理由、残った失敗や確認事項を簡潔に報告する。

## 制約

- 取得時刻だけの差分を更新理由にしない。
- `output/help_result.yaml`、`output/llms.txt`、`output/llms-full.txt` は生成スクリプトの出力であり、手編集しない。
- 既存スキルを一括で書き換えず、差分から影響範囲を説明できるものだけ更新する。
- `temp/skill-maintenance/diff/` の各ファイルは自分で全文を読まず、必ずサブエージェントの要約を経由する。要約で判断できない場合だけ、該当箇所に絞って読む。
- `temp/skill-maintenance/` は作業用の差分置き場であり、コミット対象にしない。
- `.claude/skills/skill-maintenance/state/` は前回実行時点のスナップショットを保持するための内部状態であり、手編集・コミット対象にしない（`.gitignore` 済み）。
