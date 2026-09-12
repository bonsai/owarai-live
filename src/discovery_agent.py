"""Recursive discovery orchestrator for OWARAI MUSEN."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .graph import build_graph
from .memory import append_jsonl, load_memory, score_query
from .ontology import DiscoveryRun, Event
from .search_engine import build_queries, dedupe_queries

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"
EVENTS_PATH = DATA / "events.json"
MEMORY_PATH = DATA / "agent-memory.jsonl"

WEIGHTS = {
    "new_event": 10,
    "free_event": 5,
    "under_500": 4,
    "under_1000": 2,
    "free_keyword": 3,
}


def load_events() -> list[Event]:
    if not EVENTS_PATH.exists():
        return []
    raw = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    return [Event.model_validate(item) for item in raw]


def run() -> DiscoveryRun:
    events = load_events()
    history = load_memory(MEMORY_PATH)
    previous_raw = history[-1].get("events", []) if history else []
    previous = [Event.model_validate(item) for item in previous_raw]

    performers = sorted({artist for event in events for artist in event.artists if artist})
    venues = sorted({event.venue for event in events if event.venue})
    queries = dedupe_queries(build_queries(performers, venues))

    ranked = []
    for query in queries:
        scored = score_query(query.query, events, previous, WEIGHTS)
        scored.kind = query.kind
        ranked.append(scored)
    ranked.sort(key=lambda item: (-item.score, item.query))

    current_keys = {event.id for event in events}
    previous_keys = {event.get("id") for event in previous_raw}
    new_events = len(current_keys - previous_keys)
    free_events = sum(event.price_kind == "free" for event in events)

    run = DiscoveryRun(
        timestamp=datetime.now(timezone.utc).isoformat(),
        generated_queries=len(queries),
        events_seen=len(events),
        new_events=new_events,
        free_events=free_events,
        ranked_queries=ranked[:300],
    )
    append_jsonl(
        MEMORY_PATH,
        {
            **run.model_dump(),
            "seeds": [
                "https://www.shimokitagrip2020.com/",
                "https://www.shimokita-dash.com/",
            ],
            "events": [event.model_dump() for event in events],
            "graph_stats": {
                "nodes": len(build_graph(events).get("nodes", [])),
                "edges": len(build_graph(events).get("edges", [])),
            },
            "rule": "discover -> score -> expand -> normalize -> dedupe -> verify -> remember -> prioritize",
        },
    )
    return run


if __name__ == "__main__":
    print(run().model_dump_json(indent=2))
