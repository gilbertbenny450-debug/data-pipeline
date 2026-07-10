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

# Shop types that must never enter the universe even if co-tagged
EXCLUDED_SHOP_TYPES = {"supermarket", "convenience", "kiosk", "greengrocer",
                       "butcher", "alcohol", "newsagent", "variety_store"}

# Known chains — excluded outright (curation spec 2.4).
# PREFIX entries match "name" or "name ..."; EXACT entries match the whole name only
# (protects independents like "Paul Rothe & Son" from blocking on "Paul").
CHAIN_PREFIX = [
    "greggs", "pret a manger", "costa", "starbucks", "caffe nero", "cafe nero",
    "mcdonald", "kfc", "burger king", "subway", "domino", "pizza hut",
    "pizza express", "pizzaexpress", "nando", "wagamama", "five guys", "itsu",
    "wasabi", "tortilla", "chipotle", "gail", "blank street", "ole steen",
    "joe the juice", "black sheep coffee", "waitrose", "little waitrose",
    "tesco", "sainsbury", "aldi", "lidl", "asda", "morrisons", "marks spencer",
    "ms simply food", "co op", "coop food", "whsmith", "crosstown", "creams",
    "kaspa", "tim horton", "taco bell", "papa john", "kokoro", "german doner",
    "bubbleology", "chaiiwala", "benugo", "patisserie valerie", "krispy kreme",
    "dunkin", "shake shack", "franco manca", "zizzi", "ask italian", "prezzo",
    "bella italia", "frankie benny", "slim chickens", "popeyes", "wingstop",
    "tgi friday", "harvester", "toby carvery", "wetherspoon", "greene king",
]
CHAIN_EXACT = ["paul", "eat", "leon", "grind", "pod", "pure", "coco di mama"]

# Curation spec thresholds (section 6)
RATING_FLOOR = 4.0
CONFIDENCE_REVIEWS = 25
CHAIN_MAX_SITES = 5
UPCOMING_EJECT_RATING = 3.8
UPCOMING_EJECT_MIN_REVIEWS = 10
UPCOMING_GRADUATE_DAYS = 90
UPCOMING_GRADUATE_REVIEWS = 50
VELOCITY_WINDOW_DAYS = 28
EDITORIAL_HALF_LIFE_DAYS = 56

# Region assignment: compass regions around central London
CENTRAL_LAT, CENTRAL_LON = 51.5117, -0.1275
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
