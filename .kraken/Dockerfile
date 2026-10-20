FROM kraken/tentacle-base
USER root
ARG DEBIAN_FRONTEND=noninteractive
# build-essential: tree-sitter build, node-gyp and cargo's cc; python3: node-gyp (the tools run in
# the uv venv below); libicu: .NET aborts without it; xz-utils: the Node tarball
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential pkg-config python3 jq libicu-dev ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/*
# The tree-sitter CLI the owner generates with (parser.c must match it), from the release binary
ARG TREE_SITTER_VERSION=0.27.0
RUN curl -fsSL https://github.com/tree-sitter/tree-sitter/releases/download/v$TREE_SITTER_VERSION/tree-sitter-linux-x64.gz \
      | gunzip > /usr/local/bin/tree-sitter && chmod +x /usr/local/bin/tree-sitter && tree-sitter --version
# Python 3.13 as CI pins it, in a venv on PATH, so `python -m tools...` finds the requirements;
# uv also gives uvx for serena
ENV UV_INSTALL_DIR=/usr/local/bin UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN curl -fsSL https://astral.sh/uv/install.sh | sh \
    && uv venv --python 3.13 /opt/venv \
    && curl -fsSL https://raw.githubusercontent.com/SShadowS/tree-sitter-al/main/tools/query_coverage/requirements.txt -o /tmp/req.txt \
    && uv pip install --python /opt/venv/bin/python -r /tmp/req.txt && rm /tmp/req.txt
ENV PATH=/opt/venv/bin:$PATH
# Rust for `cargo test --features traversal` (no rust-toolchain.toml: stable)
ENV RUSTUP_HOME=/opt/rustup
RUN curl -fsSL https://sh.rustup.rs | CARGO_HOME=/opt/cargo sh -s -- -y --profile minimal --no-modify-path
ENV PATH=/opt/cargo/bin:$PATH
# .NET 10 and the AL tool (`al`): tools/alc_probe, config_oracle's probes and b7_audit compile with it
RUN curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && bash /tmp/dotnet-install.sh --channel 10.0 --install-dir /opt/dotnet && rm /tmp/dotnet-install.sh
ENV DOTNET_ROOT=/opt/dotnet PATH=/opt/dotnet:/opt/al-tool:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1
ARG AL_TOOL_VERSION=18.0.41.62505
RUN mkdir -p /tmp/build-home && export HOME=/tmp/build-home \
    && dotnet tool install microsoft.dynamics.businesscentral.development.tools \
      --version $AL_TOOL_VERSION --tool-path /opt/al-tool \
    && al --version && rm -rf /tmp/build-home
# Node for npm test (node-gyp) and the pi coding agent behind pi-mcp
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
RUN HOME=/tmp/build-home npm install -g --cache /tmp/npm-cache @earendil-works/pi-coding-agent \
    && HOME=/tmp/build-home pi --version && rm -rf /tmp/npm-cache /tmp/build-home
ENV PI_CODING_AGENT_DIR=/home/dev/.config/pi
# Login shells (bash -l: kraken's setup, ssh sessions) rebuild PATH from /etc/profile, so ENV alone is not enough
RUN printf '%s\n' 'export PATH=/opt/venv/bin:/opt/cargo/bin:/opt/dotnet:/opt/al-tool:$PATH' \
      'export DOTNET_ROOT=/opt/dotnet' 'export RUSTUP_HOME=/opt/rustup' 'export DOTNET_CLI_TELEMETRY_OPTOUT=1' \
      'export UV_PYTHON_INSTALL_DIR=/opt/uv-python' 'export PI_CODING_AGENT_DIR=/home/dev/.config/pi' \
      > /etc/profile.d/tsal-tools.sh \
    && chown -R dev:dev /opt/rustup /opt/cargo /opt/venv
# ends as root: the base entrypoint drops to dev
