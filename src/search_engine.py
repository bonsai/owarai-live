"""Search-engine abstraction.

The first prototype is intentionally provider-neutral: it creates high-value
queries and leaves HTTP/search credentials outside the core ontology.
"""
from __future__ import annotations

from .ontology import QueryCandidate

PATTERNS = [
    ("performer", "{value} お笑い ライブ 2026"),
    ("performer", "{value} 無料 お笑い ライブ 2026"),
    ("performer", "{value} 出演 ライブ 2026"),
    ("venue", "{value} お笑い ライブ 2026"),
    ("venue", "{value} 無料 お笑い ライブ 2026"),
    ("venue", "{value} TIGET お笑い"),
]


def build_queries(performers: list[str], venues: list[str]) -> list[QueryCandidate]:
    candidates: list[QueryCandidate] = []
    for kind, template in PATTERNS:
        values = performers if kind == "performer" else venues
        for value in values:
            candidates.append(
                QueryCandidate(
                    kind=kind,
                    query=template.format(value=value),
                )
            )
    return candidates


def dedupe_queries(candidates: list[QueryCandidate]) -> list[QueryCandidate]:
    seen: set[str] = set()
    result: list[QueryCandidate] = []
    for candidate in candidates:
        if candidate.query in seen:
            continue
        seen.add(candidate.query)
        result.append(candidate)
    return result
