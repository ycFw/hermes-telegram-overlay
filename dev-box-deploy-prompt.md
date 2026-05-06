# Dev Box Deployment Prompt

Copy the entire prompt below to the AI on the Dev Box (Claude Code / Codex). It will follow the steps to deploy `hermes-telegram-overlay` to WSL2 + systemd, watchdogged by Windows Task Scheduler.

> WARNING: The old bot processes have been `kill -9`ed, and the old scheduled tasks `HermesStackStart` / `HermesStackWatchdog` have been Disabled. **Do not delete the old tasks**; keep them for rollback.

---

## Prompt for the Dev Box AI (copy directly to it)

```
Please help me deploy hermes-telegram-overlay to WSL2 (Ubuntu) on this Dev Box, watchdogged from the Windows side via Task Scheduler. Run all commands step by step and report the result of each step.

Environment and constraints:
- The old bot processes have been killed; the old scheduled tasks HermesStackStart / HermesStackWatchdog are Disabled, kept (not deleted)
- The production bot token is the original CongHermesBot token; I will DM it to you separately (do not write it into any commit or log)
- TELEGRAM_ALLOWED_USERS = 7705531645
- The default WSL distro is Ubuntu; if not, change the --wsl-distro argument
- You probe the LiteLLM base_url yourself: first try http://127.0.0.1:4000/v1, and if curl /v1/models works, use it; otherwise try http://host.docker.internal:4000/v1; if neither works, tell me

Step 1 — sibling clone inside WSL (~/workspace/)
  cd ~/workspace
  # Of these 4 repos, hermes-agent / opentwitter-mcp / opennews-mcp should already exist (the old bot used them)
  # You only need to clone hermes-telegram-overlay
  git clone <I will provide this GitHub URL> hermes-telegram-overlay
  ls -d hermes-agent hermes-telegram-overlay opentwitter-mcp opennews-mcp

Step 2 — create venv and install dependencies
  cd ~/workspace/hermes-telegram-overlay
  python3 scripts/bootstrap_env.py --python /usr/bin/python3
  .venv/bin/python -m pytest tests -q   # should be 11 passed

Step 3 — render and install the prod profile
  python3 scripts/bootstrap_profile.py \
    --profile prod-devbox \
    --hermes-home ~/.hermes/profiles/hermes-telegram-prod \
    --allowed-users 7705531645 \
    --litellm-base-url <the base_url you probed>

Step 4 — fill in .env
  cp ~/.hermes/profiles/hermes-telegram-prod/.env.template ~/.hermes/profiles/hermes-telegram-prod/.env
  chmod 600 ~/.hermes/profiles/hermes-telegram-prod/.env
  # Edit this .env and fill in the following fields:
  #   TELEGRAM_BOT_TOKEN=<the production bot token I DMed you>
  #   OPENAI_API_KEY=<the master key of the local LiteLLM, the same one the old bot used>
  #   TG_HISTORY_API_ID=<my Telegram API ID>
  #   TG_HISTORY_API_HASH=<my Telegram API hash>
  # If the old bot has already used these two Telethon credentials, reuse them; if not, ask me to apply at my.telegram.org

Step 5 — first-time Telethon login (interactive, requires SMS code)
  cd ~/workspace/hermes-telegram-overlay
  set -a; source ~/.hermes/profiles/hermes-telegram-prod/.env; set +a
  .venv/bin/python -m hermes_telegram_overlay.tg_history
  # Follow the prompts: enter phone number → SMS code (→ 2FA password)
  # On success it prints "Session saved to: .../<profile>.session"

Step 6 — render Dev Box deployment templates
  python3 scripts/render_deploy.py \
    --overlay-repo ~/workspace/hermes-telegram-overlay \
    --hermes-home ~/.hermes/profiles/hermes-telegram-prod \
    --output-dir /tmp/hermes-telegram-deploy

Step 7 — install the systemd user service
  mkdir -p ~/.config/systemd/user
  cp /tmp/hermes-telegram-deploy/hermes-telegram.service ~/.config/systemd/user/
  loginctl enable-linger $USER     # let user systemd run even when there is no SSH session
  systemctl --user daemon-reload
  systemctl --user enable --now hermes-telegram.service
  systemctl --user status hermes-telegram.service
  journalctl --user -u hermes-telegram.service -n 80 --no-pager

Step 8 — Windows-side watchdog
  # In PowerShell (Administrator), run:
  $opsDir = "$env:USERPROFILE\ops"
  New-Item -ItemType Directory -Force -Path $opsDir | Out-Null
  # Copy the rendered PS1 over
  wsl.exe -d Ubuntu cp /tmp/hermes-telegram-deploy/Watch-HermesTelegram.ps1 /tmp/Get-HermesTelegramStatus.ps1 /mnt/c/Users/$env:USERNAME/ops/
  # Register the new scheduled task (keep the old HermesStack* Disabled; do not delete)
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$opsDir\Watch-HermesTelegram.ps1`""
  $trigger1 = New-ScheduledTaskTrigger -AtLogon
  $trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
  Register-ScheduledTask -TaskName "HermesTelegramWatchdog" -Action $action -Trigger @($trigger1,$trigger2) -RunLevel Highest -Force
  Get-ScheduledTask -TaskName "HermesTelegramWatchdog"

Step 9 — verification
  # 9.1 systemd active
  wsl.exe -d Ubuntu systemctl --user is-active hermes-telegram.service   # should print active
  # 9.2 Telegram private chat (user_id = 7705531645): send hi → should get a reply
  # 9.3 command smoke test: send the following 6 to the bot
  #     /tw turingou 3
  #     /twsearch ai agent
  #     /twuser elonmusk
  #     /news
  #     /hotnews
  #     /tg durov 5
  # 9.4 kill test → systemd should bring it back up within 5 seconds
  pkill -f hermes_cli.main
  sleep 6
  wsl.exe -d Ubuntu systemctl --user is-active hermes-telegram.service   # should still be active
  # 9.5 reboot the Dev Box → the service should come back online automatically

If any step fails, stop immediately and report the error to me; do not try other workarounds. Secrets such as the Telethon API_ID/HASH must never be written into git commits, logs, or any stdout output.
```

---

## What the user must do after deployment

1. **Rotate three secrets**:
   - Telegram bot token: @BotFather → `/revoke` → choose `CongHermesBot` → put the new token into the Dev Box `.env`
   - LiteLLM master key: reissue in the LiteLLM config, sync the new key to the Dev Box `.env`
   - If the Telethon `API_ID/API_HASH` was ever pasted in any chat, also rotate at my.telegram.org

2. **First-message verification**:
   - Send "hello" to the bot in Telegram → see if it replies
   - Send `/tw turingou 3` → see if the 6551 MCP works

3. **Cleanup after 2 weeks**:
   - Delete the old `HermesStackStart` / `HermesStackWatchdog` scheduled tasks only after the new deployment has been stable for 2 weeks
   - The old bot code at `~/workspace/hermes-agent/venv` can be kept for reference
