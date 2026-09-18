"""Discovery search graph.

Historical events remain data, not disposable state. The existing data/events.json
is treated as a seed source. The graph expands from genres, price targets, venues,
and event hubs into search queries, then feeds candidates back for verification.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "search-seeds.json"
EVENTS = ROOT / ".data" / "events.json"


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_seed_events() -> list[dict]:
    if not EVENTS.exists():
        return []
    return json.loads(EVENTS.read_text(encoding="utf-8"))


def build_search_graph() -> dict:
    config = load_config()
    events = load_seed_events()
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def node(node_id: str, kind: str, label: str) -> None:
        nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label})

    # Historical DB -> seed layer. Never mutate/delete the historical DB here.
    node("seed:historical-events", "seed", "data/events.json")
    for event in events:
        event_id = f"event:{event.get('id', '')}"
        if not event.get("id"):
            continue
        node(event_id, "event", event.get("title", ""))
        edges.append({"source": "seed:historical-events", "target": event_id, "type": "seeds"})

    for genre in config.get("genres", []):
        genre_id = f"genre:{genre}"
        node(genre_id, "genre", genre)
        edges.append({"source": "seed:historical-events", "target": genre_id, "type": "expand_by"})

    for price in config.get("price_targets", []):
        price_id = f"price:{price}"
        node(price_id, "price", price)
        edges.append({"source": "seed:historical-events", "target": price_id, "type": "filter_by"})

    for hub in config.get("event_hubs", []):
        hub_id = f"hub:{hub['name']}"
        node(hub_id, hub.get("kind", "event_hub"), hub["name"])
        edges.append({"source": "seed:historical-events", "target": hub_id, "type": "expand_to"})

    query_index = 0
    for template in config.get("query_templates", []):
        for genre in config.get("genres", []):
            query = template.format(genre=genre, venue=genre)
            query_id = f"query:{query_index:04d}"
            node(query_id, "query", query)
            edges.append({"source": f"genre:{genre}", "target": query_id, "type": "search"})
            query_index += 1
        for hub in config.get("event_hubs", []):
            query = template.format(genre="講談・浪曲", venue=hub["name"])
            query_id = f"query:{query_index:04d}"
            node(query_id, "query", query)
            edges.append({"source": f"hub:{hub['name']}", "target": query_id, "type": "search"})
            query_index += 1

    return {"nodes": list(nodes.values()), "edges": edges}


if __name__ == "__main__":
    graph = build_search_graph()
    print(json.dumps(graph, ensure_ascii=False, indent=2))
