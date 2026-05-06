"""Human-readable formatting for overlay slash commands."""

from __future__ import annotations


def truncate(text: str, limit: int = 280) -> str:
    """Truncate text without returning blank output."""
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[: limit - 3].rstrip()}..."


def format_compact_count(value: int | float | str | None) -> str:
    """Format counts into Telegram-friendly compact strings."""
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        return "0"

    if number >= 1_000_000:
        compact = f"{number / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{compact}M"
    if number >= 1_000:
        compact = f"{number / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{compact}K"
    return str(number)


def format_tweet(tweet: dict, index: int | None = None) -> str:
    """Render a tweet search result."""
    username = tweet.get("username") or tweet.get("screen_name") or ""
    name = tweet.get("name") or username
    text = truncate(tweet.get("text") or tweet.get("full_text") or "", 500)
    likes = format_compact_count(tweet.get("favorite_count") or tweet.get("likes"))
    retweets = format_compact_count(tweet.get("retweet_count") or tweet.get("retweets"))
    replies = format_compact_count(tweet.get("reply_count") or tweet.get("replies"))
    created_at = tweet.get("created_at") or ""
    tweet_id = tweet.get("id_str") or tweet.get("id") or ""

    prefix = f"{index}. " if index is not None else ""
    lines = [f"{prefix}{name} (@{username})".strip()]
    if text:
        lines.append(text)
    lines.append(f"点赞 {likes}  转推 {retweets}  回复 {replies}")
    if created_at:
        lines.append(f"时间 {created_at}")
    if username and tweet_id:
        lines.append(f"https://x.com/{username}/status/{tweet_id}")
    return "\n".join(lines)


def format_news(article: dict, index: int | None = None) -> str:
    """Render a news article result."""
    title = article.get("title") or "Untitled"
    source = article.get("source") or article.get("newsType") or ""
    coins = article.get("coins") or []
    ai_rating = article.get("aiRating") or {}
    score = ai_rating.get("score")
    signal = ai_rating.get("signal") or ""
    summary = truncate(ai_rating.get("summary") or "", 220)
    link = article.get("link") or ""

    prefix = f"{index}. " if index is not None else ""
    lines = [f"{prefix}{title}".strip()]
    if source:
        lines.append(f"来源 {source}")
    if coins:
        lines.append(f"相关币种 {', '.join(str(item) for item in coins[:5])}")
    if score not in (None, ""):
        score_line = f"AI 评分 {score}"
        if signal:
            score_line += f"  信号 {signal}"
        lines.append(score_line)
    if summary:
        lines.append(summary)
    if link:
        lines.append(link)
    return "\n".join(lines)


def format_channel_post(post: dict, index: int | None = None) -> str:
    """Render a Telegram channel post result."""
    text = truncate(post.get("text") or "", 240)
    views = format_compact_count(post.get("views"))
    reaction_count = format_compact_count(post.get("reaction_count"))
    date_value = post.get("date") or ""
    link = post.get("link") or ""

    prefix = f"{index}. " if index is not None else ""
    lines = [f"{prefix}浏览 {views}  反应 {reaction_count}".strip()]
    if date_value:
        lines.append(f"时间 {date_value}")
    if text:
        lines.append(text)
    if link:
        lines.append(link)
    return "\n".join(lines)


def render_section(title: str, rows: list[str]) -> str:
    """Render a section with blank-line-separated rows."""
    visible = [row.strip() for row in rows if row and row.strip()]
    if not visible:
        return f"{title}\n没有结果。"
    return f"{title}\n\n" + "\n\n".join(visible)
