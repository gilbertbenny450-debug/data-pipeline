"""Pull the London food-venue universe from OpenStreetMap (free, no key needed)."""
import json, urllib.request, urllib.parse
from .config import LONDON_BBOX, OSM_FILTERS
from .db import upsert_venue, refresh_chain_counts, mark_closed, connect

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def build_query() -> str:
    s, w, n, e = LONDON_BBOX
    bbox = f"({s},{w},{n},{e})"
    parts = "".join(f"{f}{bbox};" for f in OSM_FILTERS)
    return f"[out:json][timeout:180];({parts});out center tags;"

def fetch(query: str) -> dict:
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data,
        headers={"User-Agent": "london-food-discovery-pipeline/0.2 (prototype)"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)

def element_to_venue(el: dict):
    tags = el.get("tags", {})
    name = tags.get("name")
    if not name:
        return None
    lat = el.get("lat") or (el.get("center") or {}).get("lat")
    lon = el.get("lon") or (el.get("center") or {}).get("lon")
    if lat is None or lon is None:
        return None
    category = tags.get("amenity") or tags.get("shop") or "unknown"
    housenumber = tags.get("addr:housenumber")
    street = tags.get("addr:street")
    address = " ".join(x for x in (housenumber, street) if x) or None
    return {
        "osm_id": f'{el["type"]}/{el["id"]}',
        "name": name,
        "category": category,
        "cuisine": tags.get("cuisine"),
        "lat": lat, "lon": lon,
        "postcode": tags.get("addr:postcode"),
        "address": address,
        "website": tags.get("website") or tags.get("contact:website"),
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "opening_hours": tags.get("opening_hours"),
    }

def run(db_path="london_food.db", data: dict | None = None):
    """data param lets tests inject a saved Overpass response."""
    con = connect(db_path)
    payload = data if data is not None else fetch(build_query())
    count = 0
    for el in payload.get("elements", []):
        v = element_to_venue(el)
        if v:
            upsert_venue(con, v)
            count += 1
    mark_closed(con)
    refresh_chain_counts(con)
    con.commit()
    print(f"OSM pull: {count} venues upserted")
    return count

if __name__ == "__main__":
    run()
