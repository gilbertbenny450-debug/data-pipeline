"""Export a compact app_data.json that the prototype app loads directly."""
import json, random
from .db import connect
from .config import CHAIN_MAX_SITES
from . import score

MAX_VENUES = 1200

def run(db_path="london_food.db", out="app_data.json"):
    con = connect(db_path)
    rows = con.execute("""
        SELECT id, name, region, category, cuisine, lat, lon
        FROM venues
        WHERE is_open=1 AND chain_sites<=? AND name IS NOT NULL
    """, (CHAIN_MAX_SITES,)).fetchall()
    venues = [dict(r) for r in rows]
    tagged = [v for v in venues if v["cuisine"]]
    untagged = [v for v in venues if not v["cuisine"]]
    random.Random(42).shuffle(tagged)
    random.Random(43).shuffle(untagged)
    sample = (tagged + untagged)[:MAX_VENUES]
    lenses = score.compute(db_path)
    with open(out, "w") as f:
        json.dump({"venues": sample, "lenses": lenses}, f)
    print(f"App export: {len(sample)} venues + lenses -> {out}")

if __name__ == "__main__":
    run()
