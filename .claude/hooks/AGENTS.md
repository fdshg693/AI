## `.claude/hooks` 運用ルール

ここは **フックのインストール先** であり、正本ではない。`AGENTS.md` / `CLAUDE.md` 以外は gitignore 済み。

- フックの正本は `agent-tooling/agent_tooling/hooks/`（scenario ごとの `hook.yaml` とアダプタ）。ここにあるスクリプトを直接編集しない。
- 変更の流れ: agent-tooling 側を編集 → `just --justfile agent-tooling/justfile generate` → リポジトリ直下で `just hooks-update`。
- 初回（クローン直後）は `.claude/skill-tools.hooks.example.yaml` を `.claude/skill-tools.hooks.yaml`（gitignore）にコピーし、`hooks.install` で入れるフックを選んでから `just hooks-install`（`skill-tools hooks sync`）。一覧を変えたら再実行すると、足したフックが入り、外したフックが消える。
- 登録（`.claude/settings.json` の `hooks`）は skill-tools が manifest（`.skill-tools/manifest.json`）で追跡し、自分が追加したエントリだけを書き換える。`settings.json` のフックエントリを手で編集すると drift として update/remove が止まる。
- `.env`（`HOOK_LOG` 等のトグル）、`logs/`、`state/`、`config/` はフックが配置先基準で読み書きするローカル状態。skill-tools は触らない。

### 旧 hooks_manager 構成からの移行（pull 後に一度だけ）

`.claude/scripts/hooks_manager.py` と `hooks.yml` は廃止した。旧構成を使っていた環境では `settings.json` に旧エントリが残り、存在しないスクリプトを指し続ける。

1. `.claude/settings.json` の `hooks` キーから `${CLAUDE_PROJECT_DIR}/.claude/hooks/*.py` を指す旧エントリを削除する（`.codex/hooks.json` の `agent-tooling/.../generated/codex/*` を指すエントリ、`.kilo/plugin/agent_sessions.*` も同様に片付ける）。
2. `just hooks-install --overwrite` を実行する。
