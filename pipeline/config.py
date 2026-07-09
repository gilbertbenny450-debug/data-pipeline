"""Central config — every threshold from the curation spec lives here, tunable."""

# Greater London bounding box (south, west, north, east)
LONDON_BBOX = (51.28, -0.51, 51.70, 0.33)

# OSM tags that define the venue universe (curation spec section 2.2)
OSM_FILTERS = [
    'node["amenity"~"^(restaurant|cafe|fast_food|ice_cream)$"]',
    'way["amenity"~"^(restaurant|cafe|fast_food|ice_cream)$"]',
    'node["shop"~"^(bakery|confectionery|pastry|deli)$"]',
    'way["shop"~"^(bakery|confectionery|pastry|deli)$"]',
    'node["amenity"="bar"]["food"="yes"]',
    'node["amenity"="marketplace"]',
    'way["amenity"="marketplace"]',
]

# Curation spec thresholds (section 6)
RATING_FLOOR = 4.0            # Highest Rated & Trending
CONFIDENCE_REVIEWS = 25       # Bayesian confidence threshold
CHAIN_MAX_SITES = 5           # max London sites to count as "lesser known"
UPCOMING_EJECT_RATING = 3.8   # ejected from Upcoming below this...
UPCOMING_EJECT_MIN_REVIEWS = 10  # ...once it has this many reviews
UPCOMING_GRADUATE_DAYS = 90
UPCOMING_GRADUATE_REVIEWS = 50
VELOCITY_WINDOW_DAYS = 28
EDITORIAL_HALF_LIFE_DAYS = 56  # ~8 weeks

# Region assignment: compass regions around central London
CENTRAL_LAT, CENTRAL_LON = 51.5117, -0.1275   # ~Covent Garden
CENTRAL_RADIUS_KM = 3.2

REGIONS = ["Central", "North", "North East", "South East",
           "South", "South West", "West", "North West"]

# Editorial RSS feeds to monitor (buzz signals, spec 4.3)
EDITORIAL_FEEDS = [
    ("Eater London", "https://london.eater.com/rss/index.xml"),
    ("Time Out London Food", "https://www.timeout.com/london/food-drink/rss.xml"),
    ("Secret London", "https://secretldn.com/food-drink/feed/"),
    ("Hot Dinners", "https://www.hot-dinners.com/?format=feed&type=rss"),
]

# Companies House: SIC codes for food businesses (spec 4.4)
CH_SIC_CODES = ["56101", "56102", "56103", "56302", "10710", "47240"]
CH_API_BASE = "https://api.company-information.service.gov.uk"
