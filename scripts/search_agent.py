#!/usr/bin/env python3
"""OWARAI MUSEN discovery agent.

Discover -> score -> expand -> normalize -> dedupe -> verify -> remember.
The historical event DB is preserved and used as a discovery seed.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"
EVENTS = DATA / "events.json"
MEMORY = DATA / "agent-memory.jsonl"
CONFIG = ROOT / "config" / "search-seeds.json"


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


def build_queries(events, config):
    performers = sorted({a for e in events for a in e.get("artists", []) if a})
    venues = sorted({e.get("venue") for e in events if e.get("venue")})
    genres = config.get("genres", [])
    templates = config.get("query_templates", [])
    queries = []

    for template in templates:
        for genre in genres:
            for venue in venues[:100]:
                queries.append({"kind": "genre_venue", "query": template.format(genre=genre, venue=venue)})
        for performer in performers[:100]:
            queries.append({"kind": "performer", "query": template.format(genre="お笑い", venue=performer)})
        for hub in config.get("event_hubs", []):
            queries.append({"kind": "hub", "query": template.format(genre="講談・浪曲", venue=hub["name"])})
    return queries


def discovery_score(query, events, previous_events):
    current = {event_key(e) for e in events}
    previous = {event_key(e) for e in previous_events}
    new_count = len(current - previous)
    free_count = sum(1 for e in events if norm(e.get("price")) in {"0円", "無料", "0"})
    score = new_count * 10 + free_count * 5
    if "無料" in query:
        score += 3
    if any(term in query for term in ("講談", "浪曲")):
        score += 5
    return score, new_count, free_count


def main():
    events = load_events()
    history = load_memory()
    config = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    previous_snapshot = history[-1].get("events", []) if history else []

    queries = build_queries(events, config)
    ranked = []
    for item in queries:
        score, new_count, free_count = discovery_score(item["query"], events, previous_snapshot)
        ranked.append({**item, "score": score, "new_events": new_count, "free_events": free_count})
    ranked.sort(key=lambda x: (-x["score"], x["query"]))

    memory = {
        "timestamp": now(),
        "seed": {"path": str(EVENTS.relative_to(ROOT)), "preserve": True},
        "discovery": {"generated_queries": len(queries), "ranked_queries": ranked[:300]},
        "events": events,
        "rule": "historical-db -> seed -> discover -> score -> expand -> normalize -> dedupe -> verify -> remember -> prioritize",
    }
    save_memory(memory)

    print(json.dumps({"ok": True, "events": len(events), "queries": len(queries), "top_queries": ranked[:10]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
