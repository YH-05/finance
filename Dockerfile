# finance - フルDocker開発環境
# Python 3.12 + Claude Code + GitHub CLI + uv

FROM python:3.12-slim

# ===== システムパッケージ =====
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    ca-certificates \
    gnupg \
    openssh-client \
    make \
    && rm -rf /var/lib/apt/lists/*

# ===== GitHub CLI =====
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

# ===== Node.js 20.x（Claude Code に必要）=====
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# ===== Claude Code =====
RUN npm install -g @anthropic-ai/claude-code

# ===== uv（Python パッケージマネージャ）=====
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# ===== 作業ディレクトリ =====
WORKDIR /app

# ===== Python 依存関係のインストール =====
COPY pyproject.toml uv.lock ./
COPY src/utils_core ./src/utils_core/
RUN uv sync --frozen --all-extras

# ===== ソースコードコピー =====
COPY . .

# ===== 環境変数 =====
ENV PYTHONPATH="/app/src"
ENV LOG_LEVEL="INFO"
ENV PROJECT_ENV="development"
ENV TERM="xterm-256color"

# ===== デフォルトコマンド =====
CMD ["bash"]
