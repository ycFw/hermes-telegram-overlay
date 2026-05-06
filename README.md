# hermes-telegram-overlay

`hermes-telegram-overlay` is a Telegram overlay repo that runs on top of the `hermes-agent` runtime. It does not fork the Hermes core; it only:

- Registers the `/tw` `/twsearch` `/twuser` `/news` `/hotnews` `/tg` commands
- Wires in `opentwitter-mcp`, `opennews-mcp`, `tg-history-mcp`
- Provides `dev-macos` / `prod-devbox` profile templates
- Provides bootstrap / status / deploy scripts

## Directory layout

The target layout is a fixed sibling clone:

```text
workspace/
├── hermes-agent
├── hermes-telegram-overlay
├── opennews-mcp
└── opentwitter-mcp
```

## Local development

1. Create the runtime environment.

The script automatically prefers `Python >= 3.10` and installs the overlay's own development dependencies (including test dependencies). If `python3` on this machine is still the system-shipped 3.9, it is recommended to pass the Homebrew Python explicitly:

```bash
python3 scripts/bootstrap_env.py --python /opt/homebrew/bin/python3.13
```

2. Render and install a Hermes profile:

```bash
python3 scripts/bootstrap_profile.py \
  --profile dev-macos \
  --hermes-home ~/.hermes/profiles/hermes-telegram-dev \
  --allowed-users "123456789"
```

3. Fill in the token / Telethon credentials in `~/.hermes/profiles/hermes-telegram-dev/.env`.

4. Start the gateway:

```bash
HERMES_HOME=~/.hermes/profiles/hermes-telegram-dev hermes gateway
```

## Dev Box template rendering

To generate deployment scripts for a Windows Dev Box / WSL, use:

```bash
python3 scripts/render_deploy.py \
  --overlay-repo /home/cong/workspace/hermes-telegram-overlay \
  --hermes-home /home/cong/.hermes/profiles/hermes-telegram-prod \
  --output-dir /tmp/hermes-telegram-deploy
```

`--overlay-repo` and `--hermes-home` here should be paths on the target runtime machine, typically WSL paths, not paths on the current macOS host.

## Key constraints

- The primary model is fixed to `claude-opus-4-7`
- The LiteLLM endpoint must explicitly use `/v1`
- The Telegram production profile only allows the private-chat allowlist
- The overlay command layer is glue only; do not duplicate 6551 MCP logic
