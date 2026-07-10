"""Turn raw signals into the three lenses (curation spec sections 3-4).

Works today on free signals (editorial buzz, new-business flags, scarcity).
Rating-based rules activate automatically once ratings data is added.
"""
import math
from datetime import date, datetime
from .config import (RATING_FLOOR, CONFIDENCE_REVIEWS, CHAIN_MAX_SITES,
                     UPCOMING_EJECT_RATING, UPCOMING_EJECT_MIN_REVIEWS,
                     VELOCITY_WINDOW_DAYS, EDITORIAL_HALF_LIFE_DAYS,
                     UPCOMING_GRADUATE_DAYS)
from .db import connect

def bayes_rating(rating, count, city_mean=4.2):
    """Confidence-weighted rating (spec 3.1)."""
    if rating is None or not count:
        return None
    return (rating * count + city_mean * CONFIDENCE_REVIEWS) / (count + CONFIDENCE_REVIEWS)

def editorial_buzz(con, venue_id) -> float:
    """Sum of mentions with ~8-week half-life decay (spec 4.3)."""
    rows = con.execute(
        "SELECT published FROM editorial_mentions WHERE venue_id=?", (venue_id,)).fetchall()
    score = 0.0
    for r in rows:
        age = 0
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(r["published"][:len("2026-01-01T00:00:00+0000")], fmt)
                age = (date.today() - dt.date()).days
                break
            except ValueError:
                continue
        score += 0.5 ** (max(age, 0) / EDITORIAL_HALF_LIFE_DAYS)
    return score

def review_velocity(con, venue_id) -> float:
    """Change in review count across the velocity window vs baseline (spec 4.1)."""
    rows = con.execute("""SELECT snap_date, review_count FROM snapshots
        WHERE venue_id=? AND review_count IS NOT NULL
        ORDER BY snap_date DESC LIMIT 8""", (venue_id,)).fetchall()
    if len(rows) < 2:
        return 0.0
    newest, oldest = rows[0], rows[-1]
    days = max((date.fromisoformat(newest["snap_date"])
                - date.fromisoformat(oldest["snap_date"])).days, 1)
    delta = (newest["review_count"] or 0) - (oldest["review_count"] or 0)
    weekly = delta / days * 7
    base = max((oldest["review_count"] or 0) / 52, 0.5)
    return weekly / base

def eligible(v) -> bool:
    """Universe rules: open, independent/small-group (spec 2.4)."""
    return bool(v["is_open"]) and (v["chain_sites"] or 1) <= CHAIN_MAX_SITES

def compute(db_path="london_food.db", top=15):
    con = connect(db_path)
    venues = con.execute("SELECT * FROM venues").fetchall()
    row = con.execute("SELECT MIN(first_seen) m FROM venues").fetchone()
    bootstrap_date = row["m"]
    rated, trending, upcoming = [], [], []
    for v in venues:
        if not eligible(v):
            continue
        br = bayes_rating(v["rating"], v["review_count"])
        buzz = editorial_buzz(con, v["id"])
        vel = review_velocity(con, v["id"])
        if br is not None and br >= RATING_FLOOR:
            rated.append((br, v))
        if (br is None or br >= RATING_FLOOR) and (vel > 0 or buzz > 0) and v["rating"] is not None:
            trending.append((vel * 2 + buzz, v))
        age_days = (date.today() - date.fromisoformat(v["first_seen"])).days
        is_new_biz = con.execute(
            "SELECT 1 FROM new_businesses WHERE matched_venue_id=?", (v["id"],)).fetchone()
        if (age_days <= UPCOMING_GRADUATE_DAYS and v["first_seen"] != bootstrap_date) or is_new_biz:
            rc, rt = v["review_count"] or 0, v["rating"]
            if rt is not None and rc >= UPCOMING_EJECT_MIN_REVIEWS and rt < UPCOMING_EJECT_RATING:
                continue
            upcoming.append((buzz + (rt or 0) / 5 + 1 / (age_days + 7), v))
    out = {}
    for lens, lst in (("highest_rated", rated), ("trending", trending), ("upcoming", upcoming)):
        lst.sort(key=lambda t: t[0], reverse=True)
        out[lens] = [{"score": round(s, 3), "id": v["id"], "name": v["name"], "region": v["region"],
                      "lat": v["lat"], "lon": v["lon"],
                      "category": v["category"], "cuisine": v["cuisine"]} for s, v in lst[:top]]
    return out

if __name__ == "__main__":
    import json
    print(json.dumps(compute(), indent=2))
