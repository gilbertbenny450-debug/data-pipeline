"""Monitor food-press RSS feeds; match articles to venues = buzz signal (spec 4.3)."""
import re, urllib.request, xml.etree.ElementTree as ET
from .config import EDITORIAL_FEEDS
from .db import connect, normalize_name

def fetch_feed(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "london-food-discovery/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        root = ET.fromstring(r.read())
    items = []
    for item in root.iter("item"):  # RSS 2.0
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
            "summary": re.sub(r"<[^>]+>", " ", item.findtext("description") or ""),
        })
    ns = "{http://www.w3.org/2005/Atom}"
    for entry in root.iter(f"{ns}entry"):  # Atom
        link = entry.find(f"{ns}link")
        items.append({
            "title": (entry.findtext(f"{ns}title") or "").strip(),
            "link": link.get("href") if link is not None else "",
            "published": (entry.findtext(f"{ns}published") or "").strip(),
            "summary": re.sub(r"<[^>]+>", " ", entry.findtext(f"{ns}summary") or ""),
        })
    return items

def match_articles(con, source: str, items: list[dict]) -> int:
    """Match venue names in headlines/summaries. Only names with 2+ words
    (or 8+ chars) to avoid false hits on generic single words."""
    venues = con.execute(
        "SELECT id, norm_name FROM venues WHERE is_open=1 AND length(norm_name) >= 5"
    ).fetchall()
    hits = 0
    for it in items:
        text = normalize_name(f'{it["title"]} {it["summary"]}')
        for v in venues:
            nn = v["norm_name"]
            if (" " in nn or len(nn) >= 8) and nn in text:
                con.execute("""INSERT OR IGNORE INTO editorial_mentions
                    (venue_id, source, title, url, published)
                    VALUES (?,?,?,?,?)""",
                    (v["id"], source, it["title"], it["link"], it["published"]))
                hits += con.total_changes > 0
    return hits

def run(db_path="london_food.db", feeds=None, injected: dict | None = None):
    con = connect(db_path)
    total = 0
    for source, url in (feeds or EDITORIAL_FEEDS):
        try:
            items = injected[source] if injected else fetch_feed(url)
            total += match_articles(con, source, items)
        except Exception as e:
            print(f"  feed failed ({source}): {e}")
    con.commit()
    print(f"Editorial: {total} venue mentions recorded")
    return total

if __name__ == "__main__":
    run()
