# Hermes Telegram Overlay Todo

Last updated: 2026-05-05

- `[completed]` 1. Survey the Hermes plugin interface, the 6551 MCP interface, and reusable parts of the old bot
- `[completed]` 2. Create the `hermes-telegram-overlay` repo skeleton and Python package config
- `[completed]` 3. Implement the Hermes plugin commands `/tw` `/twsearch` `/twuser` `/news` `/hotnews` `/tg`
- `[completed]` 4. Implement `tg-history-mcp` and the Telethon history-reading logic
- `[completed]` 5. Fill in `SOUL.md`, the `dev-macos` / `prod-devbox` profile templates, and the bootstrap/status/deploy scripts
- `[completed]` 6. Write the key unit tests and complete local verification

Current status:

- The overlay repo skeleton is created and the core implementation is in place
- The plugin command layer, `tg-history-mcp`, profile rendering, and the profile installation script are complete
- `render_deploy.py` is added and can render the systemd / Windows watchdog / status templates
- `render_profile.py`, `bootstrap_profile.py`, and `status.py` have been confirmed to run locally on macOS
- `bootstrap_env.py` has been confirmed to automatically pick `Python 3.13` and successfully install the overlay + 6551 MCP dependencies
- `pytest tests` runs successfully inside `.venv`; all 11 tests currently pass
