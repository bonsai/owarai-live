"""Web discovery adapter used by the scheduled OWARAI MUSEN agent."""
from __future__ import annotations

import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"
OUTPUT = DATA / "web-candidates.json"
HEADERS = {"User-Agent": "OWARAI-MUSEN-Discovery/1.0 (+GitHub Actions)"}

# Discovery is intentionally broader than "お笑い". The final promotion rule
# still requires a concrete event and a verified source, while the MUSEN UI
# keeps the price ceiling at 500 yen for the target database.
DISCOVERY_SEEDS = [
    "下北GRIP 無料 お笑い ライブ 2026",
    "下北GRIP DASH 無料 お笑い ライブ 2026",
    "東京 500円 お笑い ライブ 2026",
    "東京 無料 お笑い ライブ 2026",
    "東京 500円 スタンダップコメディ 2026",
    "東京 無料 スタンダップコメディ 2026",
    "東京 500円 寄席 2026",
    "東京 無料 寄席 2026",
    "東京 500円 落語 寄席 2026",
    "東京 500円 講談 寄席 2026",
    "東京 500円 浪曲 寄席 2026",
    "東京 500円 漫才 寄席 2026",
    "TIGET 500円 お笑い 寄席 2026",
    "TIGET 500円 スタンダップコメディ 2026",
]


def search(query: str, limit: int = 8) -> list[dict]:
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    request = Request(url, headers=HEADERS)
    with urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    results: list[dict] = []
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for href, title_html in pattern.findall(body):
        title = re.sub(r"<[^>]+>", "", html.unescape(title_html)).strip()
        parsed = urlparse(href)
        target = unquote(parse_qs(parsed.query).get("uddg", [href])[0])
        if target.startswith("http"):
            results.append({"query": query, "title": title, "url": target})
        if len(results) >= limit:
            break
    return results


def build_queries(events: list[dict], max_queries: int = 32) -> list[str]:
    seeds = list(DISCOVERY_SEEDS)
    performers = sorted({a for e in events for a in e.get("artists", []) if a})
    venues = sorted({e.get("venue") for e in events if e.get("venue")})
    for venue in venues[:8]:
        seeds.extend([f"{venue} 500円 お笑い ライブ 2026", f"{venue} 500円 寄席 2026"])
    for performer in performers[:6]:
        seeds.extend([f"{performer} 500円 ライブ 2026", f"{performer} 無料 ライブ 2026"])
    return list(dict.fromkeys(seeds))[:max_queries]


def run(events: list[dict], max_queries: int = 32) -> list[dict]:
    queries = build_queries(events, max_queries)
    found, seen = [], set()
    for query in queries:
        try:
            results = search(query)
        except Exception as exc:
            found.append({"query": query, "error": str(exc)})
            continue
        for result in results:
            if result["url"] in seen:
                continue
            seen.add(result["url"])
            found.append({**result, "found_at": datetime.now(timezone.utc).isoformat(), "confidence": "要確認"})
        time.sleep(0.5)
    DATA.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "queries": queries,
        "results": found,
        "rule": "discover broadly -> price <= 500 target -> preserve evidence -> verify before Event promotion",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return found


if __name__ == "__main__":
    events_path = DATA / "events.json"
    events = json.loads(events_path.read_text(encoding="utf-8")) if events_path.exists() else []
    results = run(events)
    print(json.dumps({"queries": len(build_queries(events)), "results": len(results)}, ensure_ascii=False))
