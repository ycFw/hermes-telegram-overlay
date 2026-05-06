import asyncio
from datetime import datetime, timezone

from hermes_telegram_overlay.tg_history import ChannelPost, collect_channel_posts, filter_posts, sort_posts


class FakeReaction:
    def __init__(self, count):
        self.count = count


class FakeReactions:
    def __init__(self, *counts):
        self.results = [FakeReaction(count) for count in counts]


class FakeCustomEmojiEntity:
    """Mimics Telethon's MessageEntityCustomEmoji by class name."""

    def __init__(self, document_id):
        self.document_id = document_id


class FakeBoldEntity:
    pass


# Rename class to match Telethon's actual type name
FakeCustomEmojiEntity.__name__ = "MessageEntityCustomEmoji"


class FakeMessage:
    def __init__(self, message_id, text, views, reaction_count, dt, *, entities=None, media=None):
        self.id = message_id
        self.text = text
        self.views = views
        self.reactions = FakeReactions(reaction_count)
        self.date = dt
        self.entities = entities or []
        self.media = media


class FakeClient:
    def __init__(self, messages):
        self._messages = messages

    async def iter_messages(self, entity, limit=None):
        del entity
        count = 0
        for message in self._messages:
            if limit is not None and count >= limit:
                break
            count += 1
            yield message


def test_collect_filter_and_sort_channel_posts():
    async def scenario():
        client = FakeClient(
            [
                FakeMessage(1, "alpha", 100, 10, datetime(2026, 5, 1, tzinfo=timezone.utc)),
                FakeMessage(2, "beta keyword", 300, 5, datetime(2026, 5, 3, tzinfo=timezone.utc)),
                FakeMessage(3, "gamma keyword", 200, 20, datetime(2026, 5, 2, tzinfo=timezone.utc)),
            ]
        )
        posts = await collect_channel_posts(client, object(), channel_username="durov", limit=0)
        posts = filter_posts(
            posts,
            since_date="2026-05-02",
            until_date="2026-05-03",
            min_views=150,
            query="keyword",
        )
        return sort_posts(posts, sort_by="views", sort_order="desc")

    posts = asyncio.run(scenario())

    assert [post.message_id for post in posts] == ["2", "3"]
    assert posts[0].link == "https://t.me/durov/2"
    assert posts[0].reaction_count == 5


def test_sort_posts_by_reaction_count():
    posts = [
        ChannelPost("1", "2026-05-01T00:00:00+00:00", "a", 10, 3, ""),
        ChannelPost("2", "2026-05-01T00:00:00+00:00", "b", 10, 9, ""),
    ]

    sorted_posts = sort_posts(posts, sort_by="reaction_count", sort_order="desc")

    assert [post.message_id for post in sorted_posts] == ["2", "1"]


def test_collect_extracts_unicode_and_custom_emoji():
    async def scenario():
        client = FakeClient(
            [
                FakeMessage(
                    1,
                    "rocket 🚀🚀🔥 launch",
                    100,
                    0,
                    datetime(2026, 5, 1, tzinfo=timezone.utc),
                    entities=[
                        FakeCustomEmojiEntity(document_id=12345),
                        FakeCustomEmojiEntity(document_id=67890),
                        FakeBoldEntity(),
                    ],
                ),
            ]
        )
        return await collect_channel_posts(client, object(), channel_username="x", limit=0)

    posts = asyncio.run(scenario())
    assert posts[0].emoji_count == 3
    assert set(posts[0].emoji_unique) == {"🚀", "🔥"}
    assert posts[0].custom_emoji_count == 2


def test_filter_min_reactions():
    posts = [
        ChannelPost("1", "2026-05-01T00:00:00+00:00", "a", 0, 5, ""),
        ChannelPost("2", "2026-05-01T00:00:00+00:00", "b", 0, 50, ""),
        ChannelPost("3", "2026-05-01T00:00:00+00:00", "c", 0, 100, ""),
    ]

    result = filter_posts(posts, min_reactions=50)

    assert [p.message_id for p in result] == ["2", "3"]


def test_filter_min_emoji_count_includes_custom():
    posts = [
        ChannelPost("1", "2026-05-01T00:00:00+00:00", "no emoji", 0, 0, "", emoji_count=0, custom_emoji_count=0),
        ChannelPost("2", "2026-05-01T00:00:00+00:00", "🚀", 0, 0, "", emoji_count=1, custom_emoji_count=0),
        ChannelPost("3", "2026-05-01T00:00:00+00:00", "🚀+custom", 0, 0, "", emoji_count=1, custom_emoji_count=2),
    ]

    result = filter_posts(posts, min_emoji_count=3)

    assert [p.message_id for p in result] == ["3"]


def test_filter_has_media():
    posts = [
        ChannelPost("1", "2026-05-01T00:00:00+00:00", "text", 0, 0, "", has_media=False),
        ChannelPost("2", "2026-05-01T00:00:00+00:00", "image", 0, 0, "", has_media=True),
    ]

    only_media = filter_posts(posts, has_media=True)
    only_text = filter_posts(posts, has_media=False)
    both = filter_posts(posts, has_media=None)

    assert [p.message_id for p in only_media] == ["2"]
    assert [p.message_id for p in only_text] == ["1"]
    assert len(both) == 2


def test_sort_by_engagement():
    posts = [
        ChannelPost("1", "2026-05-01T00:00:00+00:00", "a", 1000, 0, ""),  # eng=1000
        ChannelPost("2", "2026-05-01T00:00:00+00:00", "b", 500, 60, ""),  # eng=1100
        ChannelPost("3", "2026-05-01T00:00:00+00:00", "c", 100, 200, ""),  # eng=2100
    ]

    sorted_posts = sort_posts(posts, sort_by="engagement", sort_order="desc")

    assert [p.message_id for p in sorted_posts] == ["3", "2", "1"]
