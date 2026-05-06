"""FastMCP server exposing Telegram channel history tools."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from .constants import TG_HISTORY_SERVER_NAME
from .tg_history import TelegramHistoryConfig, TelegramHistoryConfigError, TelegramHistoryService

try:
    from mcp.server.fastmcp import Context, FastMCP
except ImportError:  # pragma: no cover
    Context = Any  # type: ignore[assignment]
    FastMCP = None  # type: ignore[assignment]


if FastMCP is not None:
    @asynccontextmanager
    async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, TelegramHistoryService]]:
        service = TelegramHistoryService(TelegramHistoryConfig.from_env())
        try:
            await service.ensure_client()
            yield {"service": service}
        finally:
            await service.close()


    mcp = FastMCP(
        TG_HISTORY_SERVER_NAME,
        instructions=(
            "Read Telegram public channel history via Telethon. "
            "Use get_channel_posts for sorting, date filtering, and top-post queries."
        ),
        lifespan=app_lifespan,
    )


    @mcp.tool()
    async def get_channel_posts(
        channel: str,
        ctx: Context,
        limit: int = 1000,
        since_date: str = "",
        until_date: str = "",
        min_views: int = 0,
        sort_by: str = "date",
        sort_order: str = "desc",
        query: str = "",
        top_n: int = 0,
        min_reactions: int = 0,
        min_emoji_count: int = 0,
        has_media: bool | None = None,
    ) -> dict:
        """Get Telegram channel posts with filtering and sorting.

        Args:
            channel: Telegram username, `@name`, or `https://t.me/name`.
            limit: Max messages to fetch from Telethon history. Default 1000.
            since_date: Inclusive start date in `YYYY-MM-DD`.
            until_date: Inclusive end date in `YYYY-MM-DD`.
            min_views: Minimum views threshold.
            sort_by: `date`, `views`, `reaction_count`, `emoji_count`, or `engagement` (`views + 10*reactions`).
            sort_order: `asc` or `desc`.
            query: Optional substring filter on message text.
            top_n: Final slice after filtering and sorting. `0` means no slice.
            min_reactions: Minimum reaction_count threshold.
            min_emoji_count: Minimum (unicode + custom) emoji count per post.
            has_media: If True, only posts with media; if False, only without; None = no filter.

        Each returned post includes `emoji_count`, `emoji_unique`, `custom_emoji_count`, `has_media`.
        """
        service = ctx.request_context.lifespan_context["service"]
        try:
            return await service.get_channel_posts(
                channel=channel,
                limit=limit,
                since_date=since_date,
                until_date=until_date,
                min_views=min_views,
                sort_by=sort_by,
                sort_order=sort_order,
                query=query,
                top_n=top_n,
                min_reactions=min_reactions,
                min_emoji_count=min_emoji_count,
                has_media=has_media,
            )
        except TelegramHistoryConfigError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:  # pragma: no cover
            return {"success": False, "error": str(exc) or repr(exc)}


def main() -> None:
    """Run tg-history-mcp over stdio."""
    if FastMCP is None:
        raise SystemExit("mcp is not installed. Install overlay dependencies first.")
    mcp.run()

