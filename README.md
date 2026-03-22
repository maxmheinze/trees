# Bäume in Wien

A mobile-optimized web app displaying Vienna's public tree cadastre (Baumkataster) on an interactive map.

## Features
- 230,000+ trees from the Wien Open Data WFS
- Filter by tree group (Ahorn, Linde, Eiche, etc.) and planting year
- Color-coded markers by species group
- Click any tree for details (species, height, crown, trunk circumference)
- Live geolocation with accuracy circle
- Light mode, Inter font, mobile-first layout

## Stack
- **Frontend:** MapLibre GL JS, CARTO Positron basemap, vanilla JS/HTML/CSS
- **Backend:** FastAPI + SQLite, served via uvicorn behind nginx
- **Data:** [Baumkataster Wien](https://www.data.gv.at/datasets/c91a4635-8b7d-43fe-9b27-d95dec8392a7) (CC BY 3.0 AT)
