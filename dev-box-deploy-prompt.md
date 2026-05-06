# Dev Box 部署 Prompt

把整段 prompt 复制给 Dev Box 上的 AI（Claude Code / Codex），它会按步骤把 `hermes-telegram-overlay` 部署到 WSL2 + systemd，并由 Windows Task Scheduler 看护。

> ⚠️ 旧 bot 进程已 `kill -9`，旧计划任务 `HermesStackStart` / `HermesStackWatchdog` 已 Disabled。**不要删除旧任务**，保留作 rollback。

---

## 给 Dev Box AI 的 Prompt（直接复制给它）

```
请帮我把 hermes-telegram-overlay 部署到这台 Dev Box 的 WSL2 (Ubuntu) 上，并在 Windows 侧用 Task Scheduler 看护。所有命令请逐步执行，每一步执行后告诉我结果。

环境与约束：
- 旧 bot 进程已 kill，旧计划任务 HermesStackStart / HermesStackWatchdog 已 Disabled，保留不删
- 生产 bot token 是原 CongHermesBot 的 token，我会单独私发给你（不要写进任何 commit 或日志）
- TELEGRAM_ALLOWED_USERS = 7705531645
- WSL 发行版默认是 Ubuntu，如果不是请改 --wsl-distro 参数
- LiteLLM base_url 由你自己探测：先试 http://127.0.0.1:4000/v1，curl /v1/models 通了就用它；否则试 http://host.docker.internal:4000/v1；都不通就告诉我

Step 1 — WSL 内 sibling clone (~/workspace/)
  cd ~/workspace
  # 这 4 个 repo 中 hermes-agent / opentwitter-mcp / opennews-mcp 应该已经存在（旧 bot 用过）
  # 只需 clone hermes-telegram-overlay
  git clone <我会提供这个 GitHub URL> hermes-telegram-overlay
  ls -d hermes-agent hermes-telegram-overlay opentwitter-mcp opennews-mcp

Step 2 — 建 venv 并安装依赖
  cd ~/workspace/hermes-telegram-overlay
  python3 scripts/bootstrap_env.py --python /usr/bin/python3
  .venv/bin/python -m pytest tests -q   # 应该 11 passed

Step 3 — 渲染并安装 prod profile
  python3 scripts/bootstrap_profile.py \
    --profile prod-devbox \
    --hermes-home ~/.hermes/profiles/hermes-telegram-prod \
    --allowed-users 7705531645 \
    --litellm-base-url <你探测到的可用 base_url>

Step 4 — 填 .env
  cp ~/.hermes/profiles/hermes-telegram-prod/.env.template ~/.hermes/profiles/hermes-telegram-prod/.env
  chmod 600 ~/.hermes/profiles/hermes-telegram-prod/.env
  # 编辑这个 .env 填以下字段：
  #   TELEGRAM_BOT_TOKEN=<我私发的生产 bot token>
  #   OPENAI_API_KEY=<本机 LiteLLM 的 master key，和旧 bot 用的同一个>
  #   TG_HISTORY_API_ID=<我的 Telegram API ID>
  #   TG_HISTORY_API_HASH=<我的 Telegram API hash>
  # 这两个 Telethon 凭据如果旧 bot 已经用过，直接复用；没有就让我去 my.telegram.org 申请

Step 5 — 首次 Telethon 登录（交互式，需要手机验证码）
  cd ~/workspace/hermes-telegram-overlay
  set -a; source ~/.hermes/profiles/hermes-telegram-prod/.env; set +a
  .venv/bin/python -m hermes_telegram_overlay.tg_history
  # 按提示输入手机号 → 验证码（→ 二步验证密码）
  # 成功后会打印 "Session saved to: .../<profile>.session"

Step 6 — 渲染 Dev Box 部署模板
  python3 scripts/render_deploy.py \
    --overlay-repo ~/workspace/hermes-telegram-overlay \
    --hermes-home ~/.hermes/profiles/hermes-telegram-prod \
    --output-dir /tmp/hermes-telegram-deploy

Step 7 — 安装 systemd user 服务
  mkdir -p ~/.config/systemd/user
  cp /tmp/hermes-telegram-deploy/hermes-telegram.service ~/.config/systemd/user/
  loginctl enable-linger $USER     # 让 user systemd 在没有 SSH 时也能跑
  systemctl --user daemon-reload
  systemctl --user enable --now hermes-telegram.service
  systemctl --user status hermes-telegram.service
  journalctl --user -u hermes-telegram.service -n 80 --no-pager

Step 8 — Windows 侧看护
  # 在 PowerShell（管理员）跑：
  $opsDir = "$env:USERPROFILE\ops"
  New-Item -ItemType Directory -Force -Path $opsDir | Out-Null
  # 把渲染的 PS1 拷过来
  wsl.exe -d Ubuntu cp /tmp/hermes-telegram-deploy/Watch-HermesTelegram.ps1 /tmp/Get-HermesTelegramStatus.ps1 /mnt/c/Users/$env:USERNAME/ops/
  # 注册新计划任务（旧的 HermesStack* 保持 Disabled，不删）
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$opsDir\Watch-HermesTelegram.ps1`""
  $trigger1 = New-ScheduledTaskTrigger -AtLogon
  $trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
  Register-ScheduledTask -TaskName "HermesTelegramWatchdog" -Action $action -Trigger @($trigger1,$trigger2) -RunLevel Highest -Force
  Get-ScheduledTask -TaskName "HermesTelegramWatchdog"

Step 9 — 验证
  # 9.1 systemd active
  wsl.exe -d Ubuntu systemctl --user is-active hermes-telegram.service   # 应该输出 active
  # 9.2 Telegram 私聊（user_id = 7705531645）发 hi → 应该有回复
  # 9.3 命令烟测：发以下 6 条到 bot
  #     /tw turingou 3
  #     /twsearch ai agent
  #     /twuser elonmusk
  #     /news
  #     /hotnews
  #     /tg durov 5
  # 9.4 Kill 测试 → systemd 应在 5 秒内自动拉起
  pkill -f hermes_cli.main
  sleep 6
  wsl.exe -d Ubuntu systemctl --user is-active hermes-telegram.service   # 仍应 active
  # 9.5 重启 Dev Box → 服务应自动恢复在线

如果任一步失败，立即停下来报错给我，不要尝试其他绕过方案。Telethon API_ID/HASH 之类的密钥，绝不写进 git 提交、日志或任何 stdout 输出。
```

---

## 部署完之后必须做的（用户）

1. **轮换三个秘密**：
   - Telegram bot token：@BotFather → `/revoke` → 选 `CongHermesBot` → 新 token 写进 Dev Box `.env`
   - LiteLLM master key：在 LiteLLM 配置里换发，新 key 同步到 Dev Box `.env`
   - 如果 Telethon `API_ID/API_HASH` 在任何聊天里贴过，去 my.telegram.org 也建议轮换

2. **首条消息验证**：
   - 在 Telegram 给 bot 发 "hello" → 看是否回复
   - 发 `/tw turingou 3` → 看 6551 MCP 是否通

3. **2 周后清理**：
   - 旧 `HermesStackStart` / `HermesStackWatchdog` 计划任务在新部署稳定 2 周后再删除
   - 旧 bot 代码 `~/workspace/hermes-agent/venv` 可保留备查
