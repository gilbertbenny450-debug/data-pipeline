"""End-to-end test with injected sample data (no network needed)."""
import json, os
from pipeline import fetch_osm, editorial, companies_house, score
from pipeline.db import connect

DB = "test.db"
if os.path.exists(DB): os.remove(DB)

# --- 1. fake Overpass response: 8 venues incl. a 6-site chain ---
mk = lambda i, name, lat, lon, cat="restaurant", cui=None: {
    "type": "node", "id": i, "lat": lat, "lon": lon,
    "tags": {"name": name, "amenity": cat, **({"cuisine": cui} if cui else {})}}
elements = [
    mk(1, "Koyo Matcha Room", 51.5135, -0.135, "cafe", "japanese"),
    mk(2, "Mama Adjoa's", 51.474, -0.069, "restaurant", "west_african"),
    mk(3, "Ocak 44", 51.546, -0.075, "restaurant", "turkish"),
    mk(4, "Yardie Yard", 51.462, -0.115, "restaurant", "caribbean"),
    mk(5, "Golden Hour Bakes", 51.516, -0.205, "bakery"),
    mk(6, "Duds Diner", 51.53, -0.10, "restaurant"),
] + [mk(100+i, "MegaChain Coffee", 51.50+i*0.01, -0.12, "cafe") for i in range(6)]
fetch_osm.run(DB, data={"elements": elements})

con = connect(DB)
# --- 2. simulate history: first_seen ages + two snapshots for velocity ---
con.execute("UPDATE venues SET first_seen=date('now','-200 days') WHERE name NOT IN ('Golden Hour Bakes','Koyo Matcha Room')")
con.execute("UPDATE venues SET first_seen=date('now','-20 days') WHERE name IN ('Golden Hour Bakes','Koyo Matcha Room')")
# ratings (as if Places were enabled) — Duds Diner is a bad new opening
ratings = {"Koyo Matcha Room": (4.7, 40), "Mama Adjoa's": (4.8, 176), "Ocak 44": (4.6, 453),
           "Yardie Yard": (4.7, 284), "Duds Diner": (3.2, 25), "MegaChain Coffee": (4.5, 900)}
for n, (r, c) in ratings.items():
    con.execute("UPDATE venues SET rating=?, review_count=? WHERE name=?", (r, c, n))
# snapshots: 28 days ago vs today (Yardie Yard spiking, Ocak steady)
old = {"Yardie Yard": 220, "Ocak 44": 445, "Mama Adjoa's": 170}
for n, c in old.items():
    con.execute("""INSERT INTO snapshots SELECT id, date('now','-28 days'), ?, rating
                   FROM venues WHERE name=?""", (c, n))
con.execute("INSERT INTO snapshots SELECT id, date('now'), review_count, rating FROM venues")
con.commit()

# --- 3. editorial mentions (injected feed) ---
feed = {"Eater London": [
    {"title": "Golden Hour Bakes is the opening of the summer", "link": "https://x/1", "published": "2026-07-01", "summary": ""},
    {"title": "Where to eat now: Yardie Yard in Brixton", "link": "https://x/2", "published": "2026-06-20", "summary": ""},
]}
editorial.run(DB, feeds=[("Eater London", "injected")], injected=feed)

# --- 4. Companies House (injected) ---
companies_house.run(DB, injected=[{"company_number": "12345678", "company_name": "GOLDEN HOUR BAKES LTD",
    "sic_codes": ["56102"], "date_of_creation": "2026-06-15",
    "registered_office_address": {"postal_code": "W11 2ES"}}])

# --- 5. score ---
out = score.compute(DB)
print(json.dumps(out, indent=2))

# --- assertions ---
names = lambda lens: [v["name"] for v in out[lens]]
assert "MegaChain Coffee" not in names("highest_rated"), "chain policy failed"
assert "Duds Diner" not in names("upcoming"), "ejection rule failed"
assert "Golden Hour Bakes" in names("upcoming"), "new-opening detection failed"
assert names("trending")[0] == "Yardie Yard", "velocity ranking failed"
assert "Mama Adjoa's" not in names("upcoming"), "bootstrap guard failed"
regions = {v["name"]: v["region"] for lens in out.values() for v in lens}
print("regions:", regions)
print("ALL TESTS PASSED")
