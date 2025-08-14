import os
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

last_location: Optional[dict] = None

class Location(BaseModel):
    coor: str       # "lat,lon"
    time: str       # "HH.MM" e.g. "13.51"
    date: str       # "DD-MM-YYYY" e.g. "13-8-2025"

# Get API key from environment
API_KEY = os.environ.get("api_key")

def verify_api_key(key: str = Query(..., description="API key for access")):
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

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
def get_location(api_key: None = Depends(verify_api_key)):
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location