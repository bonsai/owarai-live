"""Canonical event ontology for OWARAI MUSEN."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

PriceKind = Literal["free", "under_500", "under_1000", "paid", "unknown"]
Confidence = Literal["確認済み", "要確認"]


class Event(BaseModel):
    """Normalized comedy event record."""

    model_config = ConfigDict(extra="allow")

    id: str
    date: str
    start_at: str = ""
    title: str
    venue: str
    area: str = ""
    artists: list[str] = Field(default_factory=list)
    price: str = "料金要確認"
    source_type: str = ""
    confidence: Confidence = "要確認"
    note: str = ""
    source_url: str = ""

    @property
    def price_kind(self) -> PriceKind:
        price = self.price.replace(",", "")
        if "無料" in price or "0円" in price:
            return "free"
        if "500円" in price and "1,500" not in price:
            return "under_500"
        if "1,000円" in price:
            return "under_1000"
        if "要確認" in price:
            return "unknown"
        return "paid"


class QueryCandidate(BaseModel):
    kind: Literal["performer", "venue", "source", "keyword"]
    query: str
    score: float = 0
    reason: list[str] = Field(default_factory=list)


class DiscoveryRun(BaseModel):
    timestamp: str
    generated_queries: int
    events_seen: int
    new_events: int
    free_events: int
    ranked_queries: list[QueryCandidate] = Field(default_factory=list)
