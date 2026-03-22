#!/usr/bin/env python3
"""
ingest.py — Downloads the Wien Baumkataster from the WFS and imports it into SQLite.
Run once manually, then weekly via cron.
"""

import httpx
import sqlite_utils
import json
import sys
from pathlib import Path

DB_PATH = Path("/home/trees/data/trees.db")
WFS_URL = (
    "https://data.wien.gv.at/daten/geo"
    "?service=WFS"
    "&request=GetFeature"
    "&version=1.1.0"
    "&typeName=ogdwien:BAUMKATOGD"
    "&srsName=EPSG:4326"
    "&outputFormat=json"
)

def fetch_trees():
    print("Fetching Baumkataster from Wien WFS (this may take a while)...")
    with httpx.Client(timeout=300) as client:
        response = client.get(WFS_URL)
        response.raise_for_status()
    data = response.json()
    features = data.get("features", [])
    print(f"Fetched {len(features)} trees.")
    return features

def parse_trees(features):
    trees = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None])
        trees.append({
            "baum_id":            props.get("BAUM_ID"),
            "lat":                coords[1],
            "lon":                coords[0],
            "species":            props.get("GATTUNG_ART"),
            "year_planted":       props.get("PFLANZJAHR"),
            "district":           props.get("BEZIRK"),
            "street":             props.get("OBJEKT_STRASSE"),
            "trunk_circumference":props.get("STAMMUMFANG"),
            "height_class":       props.get("BAUMHOEHE_TXT"),
            "crown_diameter":     props.get("KRONENDURCHMESSER_TXT"),
        })
    return trees

def import_to_db(trees):
    print(f"Importing into {DB_PATH}...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove old DB if it exists so we do a clean re-import
    if DB_PATH.exists():
        DB_PATH.unlink()

    db = sqlite_utils.Database(DB_PATH)
    db["trees"].insert_all(trees, pk="baum_id")

    # Indexes for the queries we'll be running
    print("Creating indexes...")
    db["trees"].create_index(["lat", "lon"])
    db["trees"].create_index(["species"])
    db["trees"].create_index(["year_planted"])

    print(f"Done. {db['trees'].count} trees in database.")

if __name__ == "__main__":
    try:
        features = fetch_trees()
        trees = parse_trees(features)
        import_to_db(trees)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
