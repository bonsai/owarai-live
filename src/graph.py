"""Lightweight discovery graph built from event relationships."""
from __future__ import annotations

from collections import defaultdict

from .ontology import Event


def build_graph(events: list[Event]) -> dict:
    """Return a JSON-friendly bipartite graph of events, venues and artists."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(node_id: str, kind: str, label: str) -> None:
        nodes.setdefault(node_id, {"id": node_id, "kind": kind, "label": label})

    for event in events:
        event_id = f"event:{event.id}"
        add_node(event_id, "event", event.title)
        venue_id = f"venue:{event.venue}"
        add_node(venue_id, "venue", event.venue)
        edges.append({"source": event_id, "target": venue_id, "type": "held_at"})
        for artist in event.artists:
            artist_id = f"artist:{artist}"
            add_node(artist_id, "artist", artist)
            edges.append({"source": artist_id, "target": event_id, "type": "appears_in"})

    return {"nodes": list(nodes.values()), "edges": edges}


def graph_stats(graph: dict) -> dict:
    counts = defaultdict(int)
    for node in graph.get("nodes", []):
        counts[node.get("kind", "unknown")] += 1
    return {"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", [])), **counts}
