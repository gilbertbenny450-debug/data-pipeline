"""Weekly pipeline run: pull venues, take snapshot, gather signals, score, export.
Usage: python run_weekly.py [db_path]
"""
import sys
from pipeline import fetch_osm, editorial, companies_house, score, export_app

def main(db="london_food.db"):
    print("=== London Food Discovery — weekly pipeline run ===")
    fetch_osm.run(db)
    from pipeline.db import connect, take_snapshot
    con = connect(db); take_snapshot(con); con.commit()
    print("Snapshot taken")
    editorial.run(db)
    companies_house.run(db)
    results = score.compute(db)
    import json
    with open("latest_rankings.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Rankings written to latest_rankings.json")
    export_app.run(db)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "london_food.db")
