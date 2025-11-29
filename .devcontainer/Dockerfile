# ==============================================================================
# Development Container - Data Lineage Visualizer
# ==============================================================================
# Multi-stage Dockerfile for full-stack development
# Includes: Python 3.11, Node.js 20, ODBC drivers, development tools
# ==============================================================================

FROM mcr.microsoft.com/devcontainers/base:debian-12

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Configure apt and install base packages
RUN apt-get update && apt-get -y install --no-install-recommends \
    # Development tools
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    git \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    # Python dependencies
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    # Network tools
    net-tools \
    iputils-ping \
    dnsutils \
    # Database drivers
    unixodbc \
    unixodbc-dev \
    # Text editors for quick edits
    vim \
    nano \
    # Process management
    htop \
    procps \
    # Clean up
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 18 for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel (--break-system-packages for Debian 12 PEP 668)
RUN python3.11 -m pip install --upgrade pip setuptools wheel --break-system-packages

# Install global Python tools for development
RUN pip install --no-cache-dir --break-system-packages \
    black \
    isort \
    pylint \
    pytest \
    pytest-cov \
    ipython \
    debugpy

# Install global npm packages for frontend development
RUN npm install -g \
    npm@latest \
    pnpm \
    yarn

# Create workspace directory
RUN mkdir -p /workspace

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Create non-root user 'vscode' (if not exists)
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN if ! id -u $USERNAME > /dev/null 2>&1; then \
        groupadd --gid $USER_GID $USERNAME \
        && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
        && apt-get update \
        && apt-get install -y sudo \
        && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
        && chmod 0440 /etc/sudoers.d/$USERNAME; \
    fi

# Configure git for vscode user
RUN git config --system core.autocrlf false \
    && git config --system core.eol lf \
    && git config --system init.defaultBranch main

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Set working directory
WORKDIR /workspace

# Expose ports for backend and frontend
EXPOSE 8000 3000

# Default command
CMD ["sleep", "infinity"]
