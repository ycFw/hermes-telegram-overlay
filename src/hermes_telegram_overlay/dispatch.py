"""Helpers for calling Hermes tools from overlay plugin commands."""

from __future__ import annotations

import json
from typing import Any


class ToolCallError(RuntimeError):
    """Raised when a Hermes tool returns an error payload."""


def _decode_result(raw: Any) -> dict:
    if isinstance(raw, dict):
        decoded = raw
    elif isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ToolCallError(f"Tool returned non-JSON payload: {raw}") from exc
    else:
        raise ToolCallError(f"Unsupported tool result type: {type(raw).__name__}")

    if not isinstance(decoded, dict):
        raise ToolCallError(f"Tool returned non-object payload: {decoded!r}")
    if decoded.get("error"):
        raise ToolCallError(str(decoded["error"]))
    return decoded


def dispatch_json(ctx: Any, tool_name: str, args: dict[str, Any]) -> dict:
    """Call a Hermes tool and decode the response as a JSON object."""
    return _decode_result(ctx.dispatch_tool(tool_name, args))

