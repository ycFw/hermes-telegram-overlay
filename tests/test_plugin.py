from hermes_telegram_overlay.plugin import OverlayCommands, register


class DummyContext:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.commands = {}
        self.calls = []

    def dispatch_tool(self, tool_name, args):
        self.calls.append((tool_name, args))
        return self.responses[tool_name]

    def register_command(self, name, handler, description=""):
        self.commands[name] = {"handler": handler, "description": description}


def test_register_adds_all_overlay_commands():
    ctx = DummyContext()
    register(ctx)
    assert set(ctx.commands) == {"tw", "twsearch", "twuser", "news", "hotnews", "tg"}


def test_tg_command_formats_channel_posts():
    tool_name = "mcp_tg_history_mcp_get_channel_posts"
    ctx = DummyContext(
        responses={
            tool_name: {
                "success": True,
                "channel_title": "durov",
                "data": [
                    {
                        "message_id": "1",
                        "date": "2026-05-05T08:00:00+00:00",
                        "text": "hello world",
                        "views": 12345,
                        "reaction_count": 321,
                        "link": "https://t.me/durov/1",
                    }
                ],
            }
        }
    )
    router = OverlayCommands(ctx)

    output = router.handle_tg("durov 5")

    assert "Telegram 频道 durov 热门帖子" in output
    assert "浏览 12.3K" in output
    assert "https://t.me/durov/1" in output

