# hermes-telegram-overlay

`hermes-telegram-overlay` 是基于 `hermes-agent` 运行时的 Telegram overlay 仓库，不 fork Hermes 核心，只负责：

- 注册 `/tw` `/twsearch` `/twuser` `/news` `/hotnews` `/tg` 命令
- 接入 `opentwitter-mcp`、`opennews-mcp`、`tg-history-mcp`
- 提供 `dev-macos` / `prod-devbox` profile 模板
- 提供 bootstrap / status / deploy 脚本

## 目录约定

目标目录结构固定为 sibling clone：

```text
workspace/
├── hermes-agent
├── hermes-telegram-overlay
├── opennews-mcp
└── opentwitter-mcp
```

## 本地开发

1. 创建运行环境。

脚本会自动优先选择 `Python >= 3.10`，并安装 overlay 自己的开发依赖（包括测试依赖）。这台机器上如果 `python3` 还是系统自带的 3.9，建议直接传 Homebrew Python：

```bash
python3 scripts/bootstrap_env.py --python /opt/homebrew/bin/python3.13
```

2. 渲染并安装一个 Hermes profile：

```bash
python3 scripts/bootstrap_profile.py \
  --profile dev-macos \
  --hermes-home ~/.hermes/profiles/hermes-telegram-dev \
  --allowed-users "123456789"
```

3. 填好 `~/.hermes/profiles/hermes-telegram-dev/.env` 里的 token / Telethon 凭据。

4. 启动 gateway：

```bash
HERMES_HOME=~/.hermes/profiles/hermes-telegram-dev hermes gateway
```

## Dev Box 模板渲染

如果要给 Windows Dev Box / WSL 生成部署脚本，使用：

```bash
python3 scripts/render_deploy.py \
  --overlay-repo /home/cong/workspace/hermes-telegram-overlay \
  --hermes-home /home/cong/.hermes/profiles/hermes-telegram-prod \
  --output-dir /tmp/hermes-telegram-deploy
```

这里的 `--overlay-repo` 和 `--hermes-home` 应该填目标运行机上的路径，通常是 WSL 路径，不是当前 macOS 本机路径。

## 关键约束

- 主模型固定 `claude-opus-4-7`
- LiteLLM endpoint 必须显式使用 `/v1`
- Telegram 生产 profile 只开私聊白名单
- overlay 命令层只做 glue，不复制 6551 MCP 逻辑
