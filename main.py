#!/usr/bin/env python3
"""
main.py — FastAPI backend for the Wien Baumkataster map.
"""

import sqlite3
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = Path("/home/trees/data/trees.db")

# Group mapping: substring (lowercase) -> group label
SPECIES_GROUPS = {
    "ahorn":    "Ahorn",
    "linde":    "Linde",
    "eiche":    "Eiche",
    "platan":   "Platane",
    "kastanie": "Kastanie",
    "kirsche":  "Kirsche",
    "esche":    "Esche",
    "birke":    "Birke",
    "pappel":   "Pappel",
    "pflaume":  "Pflaume",
}

def get_group(species: str) -> str | None:
    if not species:
        return None
    s = species.lower()
    for key, label in SPECIES_GROUPS.items():
        if key in s:
            return label
    return None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trees.maxheinze.eu"],
    allow_methods=["GET"],
    allow_headers=[],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/trees")
def get_trees(
    minlat: float = Query(...),
    minlon: float = Query(...),
    maxlat: float = Query(...),
    maxlon: float = Query(...),
    group: str = Query(None),
    year_from: int = Query(None),
    year_to: int = Query(None),
):
    if (maxlat - minlat) > 0.09 or (maxlon - minlon) > 0.13:
        return {"error": "zoom"}

    query = """
        SELECT baum_id, lat, lon, species, year_planted,
               district, street, height_class, crown_diameter, trunk_circumference
        FROM trees
        WHERE lat BETWEEN :minlat AND :maxlat
          AND lon BETWEEN :minlon AND :maxlon
    """
    params = {
        "minlat": minlat, "maxlat": maxlat,
        "minlon": minlon, "maxlon": maxlon,
    }

    if group:
        # Map group label back to substring for SQL LIKE
        key = next((k for k, v in SPECIES_GROUPS.items() if v == group), None)
        if key:
            query += " AND LOWER(species) LIKE :species_pattern"
            params["species_pattern"] = f"%{key}%"

    if year_from is not None:
        query += " AND year_planted >= :year_from"
        params["year_from"] = year_from

    if year_to is not None:
        query += " AND year_planted <= :year_to"
        params["year_to"] = year_to

    query += " LIMIT 2000"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    trees = []
    for row in rows:
        d = dict(row)
        d["group"] = get_group(d.get("species"))
        trees.append(d)

    return {"count": len(trees), "trees": trees}


@app.get("/api/groups")
def get_groups():
    return {"groups": list(SPECIES_GROUPS.values())}
