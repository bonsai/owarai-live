"""Date + live-event MCP server.

Reads the public event JSON from owarai-live and dj-event and exposes
live-event search plus a simple date planner that treats a live event as
the anchor of the date.

Run locally with: uv run --with mcp python mcp/server.py
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("live-date")

SOURCES = {
    "owarai": "https://raw.githubusercontent.com/bonsai/owarai-live/main/data/events.json",
    "dj": "https://raw.githubusercontent.com/bonsai/dj-event/main/data/events.jsonl",
}


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "live-date-mcp/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")


def _load_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        data = json.loads(_get(SOURCES["owarai"]))
        if isinstance(data, list):
            events.extend(data)
    except Exception:
        pass
    try:
        for line in _get(SOURCES["dj"]).splitlines():
            if line.strip():
                events.append(json.loads(line))
    except Exception:
        pass
    return events


def _minutes(value: str | None) -> int | None:
    if not value:
        return None
    try:
        h, m = value[:5].split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def _normalize(e: dict[str, Any]) -> dict[str, Any]:
    kind = e.get("type") or e.get("genre") or "other"
    price = e.get("fee", e.get("admission_price"))
    return {
        "id": e.get("id"),
        "date": e.get("date"),
        "start_at": e.get("start_at"),
        "end_at": e.get("end_at"),
        "title": e.get("title", ""),
        "venue": e.get("venue", ""),
        "area": e.get("area", ""),
        "address": e.get("address", ""),
        "type": kind,
        "price": price,
        "selectors": e.get("selectors", []),
        "source_url": e.get("source_url"),
    }


@mcp.tool()
def search_live_events(
    date: str,
    area: str = "",
    genre: str = "",
    max_price: int = 0,
    after: str = "12:00",
    before: str = "22:00",
) -> dict[str, Any]:
    """Find live events suitable for using as the anchor of a date.

    date is YYYY-MM-DD. area/genre are optional substring filters.
    max_price=0 means no price limit. after/before constrain start time.
    """
    lo, hi = _minutes(after), _minutes(before)
    found = []
    for raw in _load_events():
        e = _normalize(raw)
        if e["date"] != date:
            continue
        if area and area.lower() not in f'{e["area"]} {e["venue"]}'.lower():
            continue
        if genre and genre.lower() not in f'{e["type"]} {e["title"]}'.lower():
            continue
        price = e["price"]
        if max_price and isinstance(price, (int, float)) and price > max_price:
            continue
        start = _minutes(e["start_at"])
        if lo is not None and start is not None and start < lo:
            continue
        if hi is not None and start is not None and start > hi:
            continue
        found.append(e)
    found.sort(key=lambda x: (_minutes(x["start_at"]) or 9999, x["title"]))
    return {"date": date, "count": len(found), "events": found}


@mcp.tool()
def plan_date_with_live(
    date: str,
    area: str = "",
    genre: str = "",
    start_time: str = "14:00",
    end_time: str = "22:30",
    max_live_price: int = 0,
    meal_minutes: int = 75,
    buffer_minutes: int = 30,
) -> dict[str, Any]:
    """Build a lightweight date plan around the best matching live event.

    The live event is the anchor. The plan reserves time before it for a meal,
    and time after it for a cafe/walk, without pretending those businesses are
    real reservations. Actual restaurant booking should be handled separately.
    """
    events = search_live_events(date, area, genre, max_live_price, start_time, end_time)["events"]
    if not events:
        return {"date": date, "found": False, "message": "条件に合うライブがありません。時間帯・エリア・ジャンルを広げてください。"}

    start_limit = _minutes(start_time) or 840
    end_limit = _minutes(end_time) or 1350
    ranked = []
    for e in events:
        s = _minutes(e["start_at"])
        if s is None:
            continue
        # Prefer an event that leaves room for both a pre-live meal and a post-live hang.
        score = abs(s - (start_limit + 180))
        if s - meal_minutes - buffer_minutes < start_limit:
            score += 500
        ranked.append((score, e))
    if not ranked:
        return {"date": date, "found": False, "message": "開始時刻を確認できるライブがありません。"}

    _, live = min(ranked, key=lambda x: x[0])
    live_start = _minutes(live["start_at"]) or start_limit
    live_end = _minutes(live["end_at"])
    if live_end is None:
        live_end = min(end_limit, live_start + 90)

    meal_end = live_start - buffer_minutes
    meal_start = max(start_limit, meal_end - meal_minutes)
    if meal_start < start_limit:
        meal_start = start_limit

    after_start = live_end + buffer_minutes
    after_end = min(end_limit, after_start + 90)

    def hm(n: int) -> str:
        return f"{n // 60:02d}:{n % 60:02d}"

    return {
        "date": date,
        "found": True,
        "live": live,
        "plan": [
            {"time": f"{hm(meal_start)}–{hm(meal_end)}", "kind": "meal", "note": "ライブ前の食事。店は別途検索・予約"},
            {"time": f"{hm(live_start)}–{hm(live_end)}", "kind": "live", "title": live["title"], "venue": live["venue"]},
            {"time": f"{hm(after_start)}–{hm(after_end)}", "kind": "walk_or_cafe", "note": "ライブ後の散歩・カフェ候補"},
        ],
        "principle": "ライブをデートの主役にして、前後の余白を自動生成",
    }


@mcp.tool()
def list_event_sources() -> dict[str, str]:
    """Show the public event data sources used by this MCP server."""
    return SOURCES


if __name__ == "__main__":
    mcp.run()
