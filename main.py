#!/usr/bin/env python3
"""
main.py — FastAPI backend for the Wien Baumkataster map.
Exposes two endpoints:
  GET /api/trees?minlat=&minlon=&maxlat=&maxlon=[&species=][&year_from=][&year_to=]
  GET /api/species
"""

import sqlite3
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = Path("/home/trees/data/trees.db")

app = FastAPI()

# CORS: only allow requests from our own frontend domain
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
    species: str = Query(None),
    year_from: int = Query(None),
    year_to: int = Query(None),
):
    # Clamp bounding box to a reasonable size to prevent abuse
    if (maxlat - minlat) > 0.1 or (maxlon - minlon) > 0.1:
        return {"error": "Bounding box too large"}, 400

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

    if species:
        query += " AND species = :species"
        params["species"] = species

    if year_from is not None:
        query += " AND year_planted >= :year_from"
        params["year_from"] = year_from

    if year_to is not None:
        query += " AND year_planted <= :year_to"
        params["year_to"] = year_to

    query += " LIMIT 2000"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()

    return {
        "count": len(rows),
        "trees": [dict(row) for row in rows],
    }


@app.get("/api/species")
def get_species():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT species FROM trees WHERE species IS NOT NULL ORDER BY species"
        ).fetchall()
    return {"species": [row["species"] for row in rows]}
