"""SQLite storage: venues, weekly snapshots, editorial mentions, new-business flags."""
import sqlite3, math, re
from .config import CENTRAL_LAT, CENTRAL_LON, CENTRAL_RADIUS_KM

SCHEMA = """
CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY,
  osm_id TEXT UNIQUE,
  name TEXT NOT NULL,
  norm_name TEXT,
  category TEXT,
  cuisine TEXT,
  lat REAL, lon REAL,
  region TEXT,
  postcode TEXT,
  address TEXT,
  website TEXT,
  phone TEXT,
  opening_hours TEXT,
  first_seen TEXT DEFAULT (date('now')),
  last_seen TEXT,
  chain_sites INTEGER DEFAULT 1,
  rating REAL,
  review_count INTEGER,
  is_open INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS snapshots (
  venue_id INTEGER,
  snap_date TEXT,
  review_count INTEGER,
  rating REAL,
  PRIMARY KEY (venue_id, snap_date)
);
CREATE TABLE IF NOT EXISTS editorial_mentions (
  id INTEGER PRIMARY KEY,
  venue_id INTEGER,
  source TEXT,
  title TEXT,
  url TEXT,
  published TEXT,
  UNIQUE (venue_id, url)
);
CREATE TABLE IF NOT EXISTS new_businesses (
  company_number TEXT PRIMARY KEY,
  name TEXT,
  sic TEXT,
  incorporated TEXT,
  postcode TEXT,
  matched_venue_id INTEGER
);
CREATE INDEX IF NOT EXISTS idx_norm ON venues(norm_name);
"""

# Columns added after the first release — applied to older databases automatically
MIGRATIONS = ["address TEXT", "website TEXT", "phone TEXT", "opening_hours TEXT"]

def connect(path="london_food.db"):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    for col in MIGRATIONS:
        try:
            con.execute(f"ALTER TABLE venues ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass  # column already exists
    return con

STOPWORDS = {"the","ltd","limited","london","restaurant","cafe","café","bar","kitchen"}

def normalize_name(name: str) -> str:
    s = re.sub(r"[^a-z0-9 ]", "", name.lower())
    words = [w for w in s.split() if w not in STOPWORDS]
    return " ".join(words) or s.strip()

def assign_region(lat: float, lon: float) -> str:
    """Compass region relative to central London; Central inside radius."""
    dlat = (lat - CENTRAL_LAT) * 111.0
    dlon = (lon - CENTRAL_LON) * 111.0 * math.cos(math.radians(CENTRAL_LAT))
    if math.hypot(dlat, dlon) <= CENTRAL_RADIUS_KM:
        return "Central"
    ang = math.degrees(math.atan2(dlon, dlat)) % 360  # 0=N, 90=E
    for lo, hi, r in [(337.5,360,"North"),(0,22.5,"North"),(22.5,67.5,"North East"),
                      (67.5,112.5,"South East"),(112.5,157.5,"South East"),
                      (157.5,202.5,"South"),(202.5,247.5,"South West"),
                      (247.5,292.5,"West"),(292.5,337.5,"North West")]:
        if lo <= ang < hi:
            return r
    return "Central"

def upsert_venue(con, v: dict):
    v = dict(v)
    v["norm_name"] = normalize_name(v["name"])
    v["region"] = assign_region(v["lat"], v["lon"])
    for k in ("address","website","phone","opening_hours","postcode","cuisine"):
        v.setdefault(k, None)
    con.execute("""
      INSERT INTO venues (osm_id,name,norm_name,category,cuisine,lat,lon,region,postcode,
                          address,website,phone,opening_hours,last_seen)
      VALUES (:osm_id,:name,:norm_name,:category,:cuisine,:lat,:lon,:region,:postcode,
              :address,:website,:phone,:opening_hours,date('now'))
      ON CONFLICT(osm_id) DO UPDATE SET
        name=excluded.name, norm_name=excluded.norm_name, category=excluded.category,
        cuisine=excluded.cuisine, lat=excluded.lat, lon=excluded.lon,
        region=excluded.region, postcode=excluded.postcode,
        address=excluded.address, website=excluded.website, phone=excluded.phone,
        opening_hours=excluded.opening_hours,
        last_seen=date('now'), is_open=1
    """, v)

def refresh_chain_counts(con):
    """Count sites sharing a normalized brand name (curation spec 2.4)."""
    con.execute("""
      UPDATE venues SET chain_sites =
        (SELECT COUNT(*) FROM venues v2 WHERE v2.norm_name = venues.norm_name AND v2.is_open=1)
      WHERE norm_name != ''
    """)

def mark_closed(con, days_unseen=21):
    con.execute("""
      UPDATE venues SET is_open=0
      WHERE last_seen < date('now', ?)
    """, (f"-{days_unseen} days",))

def take_snapshot(con):
    con.execute("""
      INSERT OR REPLACE INTO snapshots (venue_id, snap_date, review_count, rating)
      SELECT id, date('now'), review_count, rating FROM venues WHERE is_open=1
    """)
