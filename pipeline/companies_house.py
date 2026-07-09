"""Detect brand-new food businesses via Companies House (free API key required).

Get a free key at https://developer.company-information.service.gov.uk
then set env var CH_API_KEY. Skipped gracefully if the key is absent.
"""
import base64, json, os, urllib.request
from datetime import date, timedelta
from .config import CH_API_BASE, CH_SIC_CODES
from .db import connect

def run(db_path="london_food.db", days_back=30, injected: list | None = None):
    con = connect(db_path)
    key = os.environ.get("CH_API_KEY")
    if injected is None and not key:
        print("Companies House: no CH_API_KEY set — skipping (get a free key to enable)")
        return 0
    if injected is not None:
        companies = injected
    else:
        since = (date.today() - timedelta(days=days_back)).isoformat()
        url = (f"{CH_API_BASE}/advanced-search/companies?"
               f"sic_codes={','.join(CH_SIC_CODES)}"
               f"&incorporated_from={since}&location=London&size=500")
        req = urllib.request.Request(url, headers={
            "Authorization": "Basic " + base64.b64encode(f"{key}:".encode()).decode()})
        with urllib.request.urlopen(req, timeout=60) as r:
            companies = json.load(r).get("items", [])
    n = 0
    for c in companies:
        addr = c.get("registered_office_address") or {}
        con.execute("""INSERT OR IGNORE INTO new_businesses
            (company_number, name, sic, incorporated, postcode)
            VALUES (?,?,?,?,?)""",
            (c.get("company_number"), c.get("company_name"),
             ",".join(c.get("sic_codes") or []),
             c.get("date_of_creation"), addr.get("postal_code")))
        n += 1
    con.commit()
    print(f"Companies House: {n} new food businesses recorded")
    return n

if __name__ == "__main__":
    run()
