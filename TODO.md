# Hermes Telegram Overlay Todo

更新时间：2026-05-05

- `[completed]` 1. 梳理 Hermes 插件接口、6551 MCP 接口、旧 bot 复用点
- `[completed]` 2. 创建 `hermes-telegram-overlay` 仓库骨架和 Python 包配置
- `[completed]` 3. 实现 `/tw` `/twsearch` `/twuser` `/news` `/hotnews` `/tg` 的 Hermes 插件命令
- `[completed]` 4. 实现 `tg-history-mcp` 和 Telethon 历史读取逻辑
- `[completed]` 5. 补齐 `SOUL.md`、`dev-macos` / `prod-devbox` profile 模板、bootstrap/status/deploy 脚本
- `[completed]` 6. 编写关键单元测试并完成本地验证

当前结论：

- 已创建 overlay repo 骨架并补齐核心实现
- 已完成插件命令层、`tg-history-mcp`、profile 渲染与 profile 安装脚本
- 已补 `render_deploy.py`，可渲染 systemd / Windows watchdog / status 模板
- 已确认 `render_profile.py`、`bootstrap_profile.py`、`status.py` 在 macOS 本地可运行
- 已确认 `bootstrap_env.py` 自动选择 `Python 3.13`，并成功安装 overlay + 6551 MCP 依赖
- 已在 `.venv` 内跑通 `pytest tests`，当前 11 个测试全部通过
