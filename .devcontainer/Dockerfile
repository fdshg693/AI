FROM mcr.microsoft.com/devcontainers/base:2.0.4-noble

# Node.js + pnpm (versions match mise.toml at the repo root), installed system-wide
# so they're available without shell activation (needed for non-interactive exec).
RUN curl -fsSL https://deb.nodesource.com/setup_26.x | bash - \
	&& apt-get install -y --no-install-recommends nodejs \
	&& rm -rf /var/lib/apt/lists/* \
	&& npm install -g pnpm@11.15.0

# uv (Python tooling for tools/llm/aim, etc.), installed system-wide.
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# AI agent CLIs (claude / codex).
RUN npm install -g @anthropic-ai/claude-code @openai/codex
