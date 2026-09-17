"""Semantic discovery layer for aw-style event search.

Turns a natural-language intent into structured search facets, then represents
providers, venues, genres, prices and source evidence as reusable assets.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "semantic-search.json"
ASSETS = ROOT / ".data" / "assets.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_query(text: str) -> dict:
    """Map natural language into search facets without requiring exact keywords."""
    facets = {
        "intent": text,
        "genres": [],
        "price_max": None,
        "time": [],
        "providers": [],
        "venue_hubs": []
    }
    rules = [
        ("講談", "講談"), ("浪曲", "浪曲"), ("落語", "落語"),
        ("寄席", "寄席"), ("お笑い", "お笑い"),
    ]
    for token, genre in rules:
        if token in text:
            facets["genres"].append(genre)
    if any(x in text for x in ("無料", "タダ", "0円")):
        facets["price_max"] = 0
    elif "500" in text or "ワンコイン" in text:
        facets["price_max"] = 500
    elif "1000" in text or "千円" in text:
        facets["price_max"] = 1000
    if "早朝" in text:
        facets["time"].append("早朝")
    if "深夜" in text:
        facets["time"].append("深夜")
    if "TIGET" in text or "チケット" in text:
        facets["providers"].append("provider:tiget")
    if "末廣亭" in text or "末広亭" in text:
        facets["venue_hubs"].append("venue:suehirotei")
    return facets


def search_assets(text: str) -> list[dict]:
    assets = load_json(ASSETS)
    facets = semantic_query(text)
    hits = []
    for asset in assets:
        score = 0
        haystack = json.dumps(asset, ensure_ascii=False)
        for genre in facets["genres"]:
            if genre in haystack:
                score += 3
        if asset["id"] in facets["providers"] or asset["id"] in facets["venue_hubs"]:
            score += 5
        if score:
            hits.append({"score": score, "asset": asset})
    return sorted(hits, key=lambda x: x["score"], reverse=True)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "500円以下の講談・浪曲をTIGETから探す"
    print(json.dumps({"query": query, "facets": semantic_query(query), "assets": search_assets(query)}, ensure_ascii=False, indent=2))
