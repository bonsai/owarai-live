#!/usr/bin/env python3
"""Seed-and-expand comedy live search agent.

The agent starts from high-signal hubs such as 下北GRIP / 下北GRIP DASH,
then expands through performers, venues and related event sources.
It deliberately separates discovery from verification and keeps a small
JSONL memory so later runs can compare what changed.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"
EVENTS = DATA / "events.json"
MEMORY = DATA / "agent-memory.jsonl"

SEEDS = [
    {"kind": "event_hub", "name": "下北GRIP", "url": "https://www.shimokitagrip2020.com/"},
    {"kind": "event_hub", "name": "下北GRIP DASH", "url": "https://www.shimokita-dash.com/"},
]

EXPANSION_QUERIES = [
    "{performer} お笑い ライブ 2026",
    "{performer} 出演 ライブ",
    "{venue} お笑い ライブ 2026",
    "{venue} イベント 2026",
]

EXCLUDE_HARD = ["下北GRIP", "下北GRIP DASH"]  # seeds, never discarded

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

def save_memory(records):
    with MEMORY.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    events = load_events()
    performers = sorted({a for e in events for a in e.get("artists", []) if a})
    venues = sorted({e.get("venue") for e in events if e.get("venue")})

    queries = []
    for p in performers:
        queries.extend(q.format(performer=p) for q in EXPANSION_QUERIES[:2])
    for v in venues:
        queries.extend(q.format(venue=v) for q in EXPANSION_QUERIES[2:])

    snapshot = []
    for e in events:
        snapshot.append({
            "event_key": event_key(e),
            "title": e.get("title"),
            "date": e.get("date"),
            "venue": e.get("venue"),
            "source_url": e.get("source_url"),
        })

    memory = {
        "timestamp": now(),
        "seeds": SEEDS,
        "discovery": {
            "performer_count": len(performers),
            "venue_count": len(venues),
            "generated_queries": len(queries),
            "queries": queries[:300],
        },
        "snapshot": snapshot,
        "rule": "discover broadly -> normalize -> dedupe -> verify -> retain source -> compare changes",
    }
    save_memory([memory])
    print(json.dumps({"ok": True, "events": len(events), "performers": len(performers), "venues": len(venues), "queries": len(queries)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
