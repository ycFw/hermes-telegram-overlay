"""Hermes plugin entrypoint for Telegram overlay commands."""

from __future__ import annotations

import shlex
from datetime import datetime, timedelta, timezone

from .constants import (
    OPENNEWS_SERVER_NAME,
    OPENTWITTER_SERVER_NAME,
    PLUGIN_NAME,
    TG_HISTORY_SERVER_NAME,
)
from .dispatch import ToolCallError, dispatch_json
from .formatting import format_channel_post, format_news, format_tweet, render_section


def _mcp_tool(server_name: str, tool_name: str) -> str:
    prefix = server_name.replace("-", "_")
    return f"mcp_{prefix}_{tool_name}"


class OverlayCommands:
    """Command router for overlay slash commands."""

    def __init__(self, ctx):
        self.ctx = ctx

    @staticmethod
    def _split(raw_args: str) -> list[str]:
        raw = (raw_args or "").strip()
        if not raw:
            return []
        try:
            return shlex.split(raw)
        except ValueError:
            return raw.split()

    @staticmethod
    def _parse_int(raw: str | None, *, default: int, min_value: int, max_value: int) -> int:
        if raw in (None, ""):
            return default
        value = int(raw)
        return max(min_value, min(max_value, value))

    @staticmethod
    def _strip_handle(raw: str) -> str:
        return raw.strip().lstrip("@")

    def _call(self, server_name: str, tool_name: str, **kwargs):
        return dispatch_json(self.ctx, _mcp_tool(server_name, tool_name), kwargs)

    def handle_tw(self, raw_args: str) -> str:
        args = self._split(raw_args)
        if not args:
            return "用法: /tw <username> [days]\n示例: /tw elonmusk 3"

        username = self._strip_handle(args[0])
        days = self._parse_int(args[1] if len(args) > 1 else None, default=3, min_value=1, max_value=30)
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()

        try:
            result = self._call(
                OPENTWITTER_SERVER_NAME,
                "search_twitter_advanced",
                from_user=username,
                exclude_replies=True,
                exclude_retweets=True,
                since_date=since_date,
                product="Top",
                limit=10,
            )
            tweets = result.get("data") or []
            if not tweets:
                fallback = self._call(
                    OPENTWITTER_SERVER_NAME,
                    "get_twitter_user_tweets",
                    username=username,
                    limit=10,
                    include_replies=False,
                    include_retweets=False,
                )
                tweets = fallback.get("data") or []
            return render_section(
                f"@{username} 最近 {days} 天热门推文",
                [format_tweet(tweet, index=index) for index, tweet in enumerate(tweets[:10], 1)],
            )
        except (ToolCallError, ValueError) as exc:
            return f"/tw 执行失败: {exc}"

    def handle_twsearch(self, raw_args: str) -> str:
        keyword = (raw_args or "").strip()
        if not keyword:
            return "用法: /twsearch <keyword>\n示例: /twsearch AI agent"

        try:
            result = self._call(
                OPENTWITTER_SERVER_NAME,
                "search_twitter_advanced",
                keywords=keyword,
                exclude_retweets=True,
                product="Top",
                limit=10,
            )
            tweets = result.get("data") or []
            return render_section(
                f"X 热门推文搜索: {keyword}",
                [format_tweet(tweet, index=index) for index, tweet in enumerate(tweets[:10], 1)],
            )
        except ToolCallError as exc:
            return f"/twsearch 执行失败: {exc}"

    def handle_twuser(self, raw_args: str) -> str:
        username = self._strip_handle((raw_args or "").strip())
        if not username:
            return "用法: /twuser <username>\n示例: /twuser elonmusk"

        try:
            result = self._call(OPENTWITTER_SERVER_NAME, "get_twitter_user", username=username)
            user = result.get("data") or {}
            if not user:
                return f"没有找到 @{username}。"
            followers = user.get("followers_count") or user.get("followersCount") or 0
            following = user.get("friends_count") or user.get("followingCount") or 0
            tweets = user.get("statuses_count") or user.get("tweetsCount") or 0
            rows = [
                f"{user.get('name') or username} (@{username})",
                (user.get("description") or "").strip(),
                f"Followers {followers:,}  Following {following:,}  Tweets {tweets:,}",
                f"https://x.com/{username}",
            ]
            return render_section(f"@{username} 用户资料", rows)
        except ToolCallError as exc:
            return f"/twuser 执行失败: {exc}"

    def handle_news(self, raw_args: str) -> str:
        keyword = (raw_args or "").strip()
        try:
            if keyword:
                result = self._call(OPENNEWS_SERVER_NAME, "search_news", keyword=keyword, limit=10)
                title = f"新闻搜索: {keyword}"
            else:
                result = self._call(OPENNEWS_SERVER_NAME, "get_latest_news", limit=10)
                title = "最新新闻"
            articles = result.get("data") or []
            return render_section(
                title,
                [format_news(article, index=index) for index, article in enumerate(articles[:10], 1)],
            )
        except ToolCallError as exc:
            return f"/news 执行失败: {exc}"

    def handle_hotnews(self, raw_args: str) -> str:
        del raw_args
        try:
            result = self._call(OPENNEWS_SERVER_NAME, "get_high_score_news", min_score=70, limit=10)
            articles = result.get("data") or []
            return render_section(
                "高影响新闻",
                [format_news(article, index=index) for index, article in enumerate(articles[:10], 1)],
            )
        except ToolCallError as exc:
            return f"/hotnews 执行失败: {exc}"

    def handle_tg(self, raw_args: str) -> str:
        args = self._split(raw_args)
        if not args:
            return "用法: /tg <channel> [top_n]\n示例: /tg durov 10\n示例: /tg https://t.me/durov 20"

        channel = args[0]
        top_n = self._parse_int(args[1] if len(args) > 1 else None, default=20, min_value=1, max_value=50)
        try:
            result = self._call(
                TG_HISTORY_SERVER_NAME,
                "get_channel_posts",
                channel=channel,
                sort_by="views",
                sort_order="desc",
                top_n=top_n,
            )
            posts = result.get("data") or []
            channel_name = result.get("channel_title") or channel
            return render_section(
                f"Telegram 频道 {channel_name} 热门帖子",
                [format_channel_post(post, index=index) for index, post in enumerate(posts[:top_n], 1)],
            )
        except ToolCallError as exc:
            return f"/tg 执行失败: {exc}"


def register(ctx) -> None:
    """Register overlay slash commands inside Hermes."""
    router = OverlayCommands(ctx)
    ctx.register_command("tw", router.handle_tw, description="Get hot tweets from a user")
    ctx.register_command("twsearch", router.handle_twsearch, description="Search hot tweets by keyword")
    ctx.register_command("twuser", router.handle_twuser, description="Show an X user profile")
    ctx.register_command("news", router.handle_news, description="Get latest or keyword news")
    ctx.register_command("hotnews", router.handle_hotnews, description="Get high-score news")
    ctx.register_command("tg", router.handle_tg, description="Get top Telegram channel posts by views")

