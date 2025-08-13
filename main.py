from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

last_location: Optional[dict] = None

class Location(BaseModel):
    coor: str       # "lat,lon"
    time: str       # "HH.MM" e.g. "13.51"
    date: str       # "DD-MM-YYYY" e.g. "13-8-2025"

@app.post("/update")
def update_location(location: Location):
    global last_location
    try:
        # Split the "coor" string into lat and lon
        lat_str, lon_str = location.coor.split(",")
        lat = float(lat_str.strip())
        lon = float(lon_str.strip())
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid coor format. Use 'lat,lon'")

    last_location = {
        "lat": lat,
        "lon": lon,
        "time": location.time,
        "date": location.date
    }
    return {"status": "success", "stored": last_location}

@app.get("/location")
def get_location():
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location