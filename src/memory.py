"""Discovery memory and query scoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from .ontology import Event, QueryCandidate


def event_key(event: Event) -> str:
    raw = "|".join(
        str(getattr(event, key, "")).strip()
        for key in ("date", "venue", "title", "start_at")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_memory(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def score_query(
    query: str,
    events: Iterable[Event],
    previous_events: Iterable[Event],
    weights: dict[str, int],
) -> QueryCandidate:
    current = list(events)
    previous_keys = {event_key(event) for event in previous_events}
    new_count = sum(event_key(event) not in previous_keys for event in current)
    free_count = sum(event.price_kind == "free" for event in current)
    under_500 = sum(event.price_kind in {"free", "under_500"} for event in current)
    under_1000 = sum(event.price_kind in {"free", "under_500", "under_1000"} for event in current)

    score = (
        new_count * weights.get("new_event", 10)
        + free_count * weights.get("free_event", 5)
        + under_500 * weights.get("under_500", 4)
        + under_1000 * weights.get("under_1000", 2)
    )
    reasons: list[str] = []
    if new_count:
        reasons.append(f"new_events={new_count}")
    if free_count:
        reasons.append(f"free_events={free_count}")
    if "無料" in query:
        score += weights.get("free_keyword", 3)
        reasons.append("free_keyword")

    return QueryCandidate(query=query, kind="keyword", score=score, reason=reasons)
