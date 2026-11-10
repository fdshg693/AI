set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

site_dir := "site/skills-site"
infra_dir := site_dir + "/infra"
azure_location := env_var_or_default("AZURE_LOCATION", "japaneast")
azure_resource_group := env_var_or_default("AZURE_RESOURCE_GROUP", "rg-ai-skill-catalog")
azure_static_site := env_var_or_default("AZURE_STATIC_SITE_NAME", "ai-skill-catalog")
github_repository := env_var_or_default("GITHUB_REPOSITORY", "fdshg693/AI")

default:
    @just --list

py-format:
    uv run ruff format .

py-format-check:
    uv run ruff format --check .

py-lint:
    uv run ruff check .

py-check: py-format-check py-lint

skills-site-check: skills-site-build skills-site-validate skills-site-test

skills-site-build:
    pnpm --filter ai-skill-catalog-site run build

skills-site-validate:
    pnpm --filter ai-skill-catalog-site run validate

skills-site-test:
    pnpm --filter ai-skill-catalog-site run test

infra-validate:
    az bicep build --file "{{infra_dir}}/main.bicep" --stdout > $null

azure-provision: infra-validate
    az deployment sub create --location "{{azure_location}}" --template-file "{{infra_dir}}/main.bicep" --parameters location="{{azure_location}}" resourceGroupName="{{azure_resource_group}}" staticSiteName="{{azure_static_site}}"

azure-token:
    az staticwebapp secrets list --resource-group "{{azure_resource_group}}" --name "{{azure_static_site}}" --query properties.apiKey --output tsv

azure-set-github-secret:
    az staticwebapp secrets list --resource-group "{{azure_resource_group}}" --name "{{azure_static_site}}" --query properties.apiKey --output tsv | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo "{{github_repository}}"

azure-url:
    az staticwebapp show --resource-group "{{azure_resource_group}}" --name "{{azure_static_site}}" --query defaultHostname --output tsv

# Self-install this repository's hooks with the bundled skill-tools.
# Sources live in agent-tooling; installed copies are gitignored. See .claude/hooks/AGENTS.md.
hooks_cli := "uv run --project tools/skill-tools skill-tools hooks"
hooks_config := ".claude/skill-tools.hooks.yaml"
claude_hooks := "agent_sessions long_run_collector long_run_statement_collector stop_alert task_tracker_session"

hooks-install *flags:
    {{hooks_cli}} install --config {{hooks_config}} --agent claude {{claude_hooks}} {{flags}}
    {{hooks_cli}} install --config {{hooks_config}} --agent codex nested_agents_md scoped_rules agent_sessions {{flags}}
    {{hooks_cli}} install --config {{hooks_config}} --agent kilo agent_sessions {{flags}}

hooks-update *flags:
    {{hooks_cli}} update --config {{hooks_config}} {{flags}}

hooks-installed:
    {{hooks_cli}} installed

# Gitignored copies of skills for tools that only read the workspace root
# (.cline/skills, .kilo/skills, _agents/plugins/antigravity-meta). Declared by
# workspace_copies in registry/ai-tools.yaml. Run after cloning and after editing
# skills/plugins/ai-tools-knowledge; pre-commit also refreshes them.
agent-compat-sync:
    uv run --directory maintenance/scripts python -m plugin_meta.generate.generate_workspace_copies

# Junctions declared in .links.yaml. Never delete a junction with rm -rf /
# Remove-Item -Recurse; use links-clean. See maintenance/docs/repo-layout.md.
links-sync *args:
    just --justfile maintenance/scripts/justfile links-sync {{args}}

links-check *args:
    just --justfile maintenance/scripts/justfile links-check {{args}}

links-clean *args:
    just --justfile maintenance/scripts/justfile links-clean {{args}}

# --- submodules (skills / tools / agent-compat / site). See maintenance/docs/repo-layout.md ---

# Clone/checkout every submodule at the commit the umbrella records (run after clone and pull)
sub-init:
    git submodule update --init --recursive

# Branch, pointer and working-tree state of every submodule
sub-status:
    git submodule status
    git submodule foreach "git status --short --branch"

# Check out main in every submodule and fast-forward it from origin (leaves detached HEAD behind)
sub-sync:
    git submodule foreach "git switch main && git pull --ff-only"

# Install lefthook in every submodule (hooks come from maintenance/lefthook/submodule.yml)
sub-hooks-install:
    git submodule foreach lefthook install

# Install the umbrella's Claude Code hooks into every submodule, so a session opened in the
# submodule alone runs them too (config: <submodule>/.claude/skill-tools.hooks.yaml; the
# installed files are gitignored there). Pass --overwrite to reinstall.
sub-agent-hooks-install *flags:
    git submodule foreach 'uv run --project "$toplevel/tools/skill-tools" skill-tools hooks install --config .claude/skill-tools.hooks.yaml --agent claude {{claude_hooks}} {{flags}}'

sub-agent-hooks-update *flags:
    git submodule foreach 'uv run --project "$toplevel/tools/skill-tools" skill-tools hooks update --config .claude/skill-tools.hooks.yaml {{flags}}'

# --- branches: the same branch name across the umbrella and every submodule ---
# Umbrella branches never create/switch/delete submodule branches; these do it in one step.
# Every recipe takes --only SUB... to limit submodules. See maintenance/docs/repo-layout.md.

# Branch, upstream ahead/behind, dirty count and pointer state of every repository
branch-status *args:
    just --justfile maintenance/scripts/justfile branch-status {{args}}

# Local branches across repositories (* marks the current one)
branch-list *args:
    just --justfile maintenance/scripts/justfile branch-list {{args}}

# Create a branch and switch to it everywhere (--from BASE)
branch-new name *args:
    just --justfile maintenance/scripts/justfile branch-new {{name}} {{args}}

# Switch everywhere, tracking origin/<name> when only the remote has it (--create, --no-fetch)
branch-switch name *args:
    just --justfile maintenance/scripts/justfile branch-switch {{name}} {{args}}

# Delete a branch wherever it exists; refuses main and unmerged branches (--force, --remote)
branch-delete name *args:
    just --justfile maintenance/scripts/justfile branch-delete {{name}} {{args}}

# Push current branches with upstream set, submodules before the umbrella
branch-push *args:
    just --justfile maintenance/scripts/justfile branch-push {{args}}

# Fast-forward current branches from their upstream without leaving them (unlike sub-sync)
branch-pull *args:
    just --justfile maintenance/scripts/justfile branch-pull {{args}}
