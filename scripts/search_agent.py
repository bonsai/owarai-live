#!/usr/bin/env python3
"""OWARAI MUSEN discovery agent.

Discover -> score -> expand -> remember.
The agent learns which query patterns produce new events and prioritizes
high-yield paths on later runs.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"
EVENTS = DATA / "events.json"
MEMORY = DATA / "agent-memory.jsonl"

SEEDS = [
    {"kind": "event_hub", "name": "下北GRIP", "url": "https://www.shimokitagrip2020.com/"},
    {"kind": "event_hub", "name": "下北GRIP DASH", "url": "https://www.shimokita-dash.com/"},
]

QUERY_PATTERNS = [
    ("performer", "{performer} お笑い ライブ 2026"),
    ("performer", "{performer} 無料 お笑い ライブ 2026"),
    ("performer", "{performer} 出演 ライブ 2026"),
    ("venue", "{venue} お笑い ライブ 2026"),
    ("venue", "{venue} 無料 お笑い ライブ 2026"),
    ("venue", "{venue} TIGET お笑い"),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()


def event_key(e):
    raw = "|".join(norm(e.get(k)) for k in ("date", "venue", "title", "start_at"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def load_events():
    if not EVENTS.exists():
        return []
    return json.loads(EVENTS.read_text(encoding="utf-8"))


def load_memory():
    if not MEMORY.exists():
        return []
    records = []
    for line in MEMORY.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def save_memory(record):
    with MEMORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def discovery_score(query, events, previous_events):
    current = {event_key(e) for e in events}
    previous = {event_key(e) for e in previous_events}
    new_count = len(current - previous)
    free_count = sum(1 for e in events if norm(e.get("price")) in {"0円", "無料"})
    score = new_count * 10 + free_count * 5
    if "無料" in query:
        score += 3
    return score, new_count, free_count


def main():
    events = load_events()
    history = load_memory()
    previous_snapshot = history[-1].get("events", []) if history else []

    performers = sorted({a for e in events for a in e.get("artists", []) if a})
    venues = sorted({e.get("venue") for e in events if e.get("venue")})

    queries = []
    for kind, template in QUERY_PATTERNS:
        values = performers if kind == "performer" else venues
        for value in values:
            queries.append({"kind": kind, "query": template.format(**{kind: value})})

    ranked = []
    for item in queries:
        score, new_count, free_count = discovery_score(item["query"], events, previous_snapshot)
        ranked.append({**item, "score": score, "new_events": new_count, "free_events": free_count})
    ranked.sort(key=lambda x: (-x["score"], x["query"]))

    memory = {
        "timestamp": now(),
        "seeds": SEEDS,
        "discovery": {
            "performer_count": len(performers),
            "venue_count": len(venues),
            "generated_queries": len(queries),
            "ranked_queries": ranked[:300],
        },
        "events": events,
        "rule": "discover -> score -> expand -> normalize -> dedupe -> verify -> remember -> prioritize",
    }
    save_memory(memory)

    print(json.dumps({
        "ok": True,
        "events": len(events),
        "performers": len(performers),
        "venues": len(venues),
        "queries": len(queries),
        "top_queries": ranked[:10],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
