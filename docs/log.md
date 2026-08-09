# Directory Update Log

## 2026-08-09

- **Creation**: `docs/` OKFバンドルを新設し、`repo-meta/skills/` 配下の13個のメタスキル（aim-automation, ai-tools-config, claude-code-first-skills, gh-actions-lifecycle, justfile-conventions, lefthook-automation, repo-ssot-pattern, skill-improving-meta-skills, skill-md-commits, skill-meta-fields, tool-companion-skills, tools-directory-layout, uv-workspace）を `docs/repo-meta/` 配下のOKF概念ドキュメントへ一括移行した。`repo-meta/skills/meta/` はスキルとして残し、`docs/repo-meta/` 配下のdocを取得・提示する役割に書き換えた。
- **Creation**: リポジトリ直下の `integrations/` フォルダ（`CLAUDE_CODE.md`, `CLI_TOOLS.md`, `CLINE.md`, `CODEX.md`）を `docs/integrations/` 配下のOKF概念ドキュメント（claude-code, cli-tools, cline, codex）へ移行した。同梱の `integrations/scripts`（`skill-deploy` CLI）はドキュメントではないため `tools/integration/scripts/` へ移動した。
