import asyncio
from datetime import datetime, timezone

from hermes_telegram_overlay.tg_history import ChannelPost, collect_channel_posts, filter_posts, sort_posts


class FakeReaction:
    def __init__(self, count):
        self.count = count


class FakeReactions:
    def __init__(self, *counts):
        self.results = [FakeReaction(count) for count in counts]


class FakeMessage:
    def __init__(self, message_id, text, views, reaction_count, dt):
        self.id = message_id
        self.text = text
        self.views = views
        self.reactions = FakeReactions(reaction_count)
        self.date = dt


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
