"""Telethon-backed Telegram history reader used by tg-history-mcp."""

from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, AsyncIterator, Iterable

import emoji as _emoji_lib

DEFAULT_FETCH_LIMIT = 1000


class TelegramHistoryConfigError(ValueError):
    """Raised when Telethon runtime config is invalid."""


def normalize_channel_ref(raw: str) -> str:
    """Normalize `@name` / `https://t.me/name` into `name`."""
    candidate = (raw or "").strip()
    if not candidate:
        raise TelegramHistoryConfigError("Telegram channel is required.")

    match = re.search(r"t\.me/(?:s/)?([A-Za-z0-9_]+)", candidate)
    if match:
        return match.group(1)
    return candidate.lstrip("@")


def parse_optional_date(raw: str | None) -> date | None:
    """Parse a YYYY-MM-DD date if present."""
    candidate = (raw or "").strip()
    if not candidate:
        return None
    return date.fromisoformat(candidate)


@dataclass(frozen=True)
class TelegramHistoryConfig:
    """Telethon runtime configuration."""

    api_id: int
    api_hash: str
    session_dir: Path
    session_name: str = "telethon-user"

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "TelegramHistoryConfig":
        env = env or dict(os.environ)
        api_id_raw = (env.get("TG_HISTORY_API_ID") or "").strip()
        api_hash = (env.get("TG_HISTORY_API_HASH") or "").strip()
        session_dir_raw = (env.get("TG_HISTORY_SESSION_DIR") or "").strip()
        session_name = (env.get("TG_HISTORY_SESSION_NAME") or "telethon-user").strip()

        if not api_id_raw:
            raise TelegramHistoryConfigError("TG_HISTORY_API_ID is required.")
        if not api_hash:
            raise TelegramHistoryConfigError("TG_HISTORY_API_HASH is required.")
        if not session_dir_raw:
            raise TelegramHistoryConfigError("TG_HISTORY_SESSION_DIR is required.")

        try:
            api_id = int(api_id_raw)
        except ValueError as exc:
            raise TelegramHistoryConfigError("TG_HISTORY_API_ID must be an integer.") from exc

        return cls(
            api_id=api_id,
            api_hash=api_hash,
            session_dir=Path(session_dir_raw).expanduser().resolve(),
            session_name=session_name,
        )


@dataclass(frozen=True)
class ChannelPost:
    """Normalized Telegram channel post."""

    message_id: str
    date: str
    text: str
    views: int
    reaction_count: int
    link: str
    emoji_count: int = 0
    emoji_unique: tuple[str, ...] = ()
    custom_emoji_count: int = 0
    has_media: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "date": self.date,
            "text": self.text,
            "views": self.views,
            "reaction_count": self.reaction_count,
            "link": self.link,
            "emoji_count": self.emoji_count,
            "emoji_unique": list(self.emoji_unique),
            "custom_emoji_count": self.custom_emoji_count,
            "has_media": self.has_media,
        }


def _iso_datetime(value: Any) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.isoformat()
        return value.astimezone().isoformat()
    return ""


def _reaction_total(message: Any) -> int:
    reactions = getattr(message, "reactions", None)
    if not reactions or not getattr(reactions, "results", None):
        return 0
    return sum(int(getattr(item, "count", 0) or 0) for item in reactions.results)


def build_post_link(channel_username: str | None, message_id: str) -> str:
    """Build a public Telegram message link when the channel has a username."""
    if not channel_username:
        return ""
    return f"https://t.me/{channel_username}/{message_id}"


def filter_posts(
    posts: Iterable[ChannelPost],
    *,
    since_date: str = "",
    until_date: str = "",
    min_views: int = 0,
    query: str = "",
    min_reactions: int = 0,
    min_emoji_count: int = 0,
    has_media: bool | None = None,
) -> list[ChannelPost]:
    """Filter posts by date, view threshold, free-text query, reactions, emoji count, and media."""
    since_value = parse_optional_date(since_date)
    until_value = parse_optional_date(until_date)
    lowered_query = query.strip().lower()
    result: list[ChannelPost] = []

    for post in posts:
        post_date = datetime.fromisoformat(post.date).date() if post.date else None
        if since_value and post_date and post_date < since_value:
            continue
        if until_value and post_date and post_date > until_value:
            continue
        if int(post.views) < int(min_views):
            continue
        if int(post.reaction_count) < int(min_reactions):
            continue
        total_emoji = int(post.emoji_count) + int(post.custom_emoji_count)
        if total_emoji < int(min_emoji_count):
            continue
        if has_media is not None and bool(post.has_media) != bool(has_media):
            continue
        if lowered_query and lowered_query not in post.text.lower():
            continue
        result.append(post)
    return result


def sort_posts(
    posts: Iterable[ChannelPost],
    *,
    sort_by: str = "date",
    sort_order: str = "desc",
) -> list[ChannelPost]:
    """Sort posts by date, views, reaction_count, emoji_count, or engagement."""
    field_name = (sort_by or "date").strip().lower()
    descending = (sort_order or "desc").strip().lower() != "asc"

    def sort_key(post: ChannelPost) -> Any:
        if field_name == "views":
            return post.views
        if field_name == "reaction_count":
            return post.reaction_count
        if field_name == "emoji_count":
            return post.emoji_count + post.custom_emoji_count
        if field_name == "engagement":
            return post.views + 10 * post.reaction_count
        return post.date

    return sorted(list(posts), key=sort_key, reverse=descending)


async def collect_channel_posts(
    client: Any,
    entity: Any,
    *,
    channel_username: str | None,
    limit: int = 0,
) -> list[ChannelPost]:
    """Read message history from a Telethon client-like object."""
    posts: list[ChannelPost] = []
    effective_limit = limit if limit > 0 else None

    async for message in client.iter_messages(entity, limit=effective_limit):
        text = getattr(message, "text", None) or getattr(message, "message", None) or ""
        if not text:
            continue
        message_id = str(getattr(message, "id"))
        text_str = str(text)
        emoji_unique = tuple(_emoji_lib.distinct_emoji_list(text_str))
        emoji_count = _emoji_lib.emoji_count(text_str)
        entities = getattr(message, "entities", None) or []
        custom_emoji_count = sum(
            1 for e in entities if type(e).__name__ == "MessageEntityCustomEmoji"
        )
        has_media = getattr(message, "media", None) is not None
        posts.append(
            ChannelPost(
                message_id=message_id,
                date=_iso_datetime(getattr(message, "date", None)),
                text=text_str,
                views=int(getattr(message, "views", 0) or 0),
                reaction_count=_reaction_total(message),
                link=build_post_link(channel_username, message_id),
                emoji_count=emoji_count,
                emoji_unique=emoji_unique,
                custom_emoji_count=custom_emoji_count,
                has_media=has_media,
            )
        )
    return posts


class TelegramHistoryService:
    """Telethon-backed service used by the overlay MCP server."""

    def __init__(self, config: TelegramHistoryConfig):
        self.config = config
        self._client: Any | None = None

    async def __aenter__(self) -> "TelegramHistoryService":
        await self.ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def ensure_client(self) -> Any:
        """Initialize and connect the Telethon client lazily."""
        if self._client is not None:
            if not self._client.is_connected():
                await self._client.connect()
            return self._client

        self.config.session_dir.mkdir(parents=True, exist_ok=True)
        try:
            from telethon import TelegramClient
        except ImportError as exc:
            raise TelegramHistoryConfigError("telethon is required for tg-history-mcp.") from exc

        session_path = self.config.session_dir / self.config.session_name
        client = TelegramClient(str(session_path), self.config.api_id, self.config.api_hash)
        await client.connect()
        self._client = client
        return client

    async def close(self) -> None:
        """Disconnect Telethon if connected."""
        if self._client is None:
            return
        if self._client.is_connected():
            await self._client.disconnect()
        self._client = None

    async def get_channel_posts(
        self,
        *,
        channel: str,
        limit: int = DEFAULT_FETCH_LIMIT,
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
    ) -> dict[str, Any]:
        """Read, filter, sort, and normalize Telegram channel history."""
        client = await self.ensure_client()
        channel_ref = normalize_channel_ref(channel)

        try:
            entity = await client.get_entity(channel_ref)
        except Exception as exc:
            raise TelegramHistoryConfigError(f"Unable to resolve Telegram channel '{channel_ref}': {exc}") from exc

        posts = await collect_channel_posts(
            client,
            entity,
            channel_username=getattr(entity, "username", None),
            limit=limit,
        )
        posts = filter_posts(
            posts,
            since_date=since_date,
            until_date=until_date,
            min_views=min_views,
            query=query,
            min_reactions=min_reactions,
            min_emoji_count=min_emoji_count,
            has_media=has_media,
        )
        posts = sort_posts(posts, sort_by=sort_by, sort_order=sort_order)
        if top_n > 0:
            posts = posts[:top_n]

        return {
            "success": True,
            "channel": getattr(entity, "username", None) or channel_ref,
            "channel_title": getattr(entity, "title", None) or getattr(entity, "username", None) or channel_ref,
            "count": len(posts),
            "data": [post.as_dict() for post in posts],
        }


def login_interactive() -> None:
    """Interactive Telethon session login. Run once before systemd starts."""
    from telethon import TelegramClient

    config = TelegramHistoryConfig.from_env()
    config.session_dir.mkdir(parents=True, exist_ok=True)
    session_path = config.session_dir / config.session_name
    client = TelegramClient(str(session_path), config.api_id, config.api_hash)
    client.start()
    me = client.loop.run_until_complete(client.get_me())
    print(f"Logged in as: {getattr(me, 'username', None) or me.id}")
    print(f"Session saved to: {session_path}.session")
    client.disconnect()


if __name__ == "__main__":
    login_interactive()

