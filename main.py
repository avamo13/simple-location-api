import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_location: Optional[dict] = None

class Location(BaseModel):
    coor: str
    time: str
    date: str

@app.post("/update")
def update_location(location: Location):
    global last_location
    try:
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
def get_location(api_key: str = Query(..., description="API key for access")):
    if api_key != os.getenv("api_key"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location