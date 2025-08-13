from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI()

last_location: Optional[dict] = None

class Location(BaseModel):
    lat: float
    lon: float
    timestamp: Optional[str] = None

@app.post("/update")
def update_location(location: Location):
    global last_location
    last_location = {
        "lat": location.lat,
        "lon": location.lon,
        "timestamp": location.timestamp or datetime.utcnow().isoformat()
    }
    return {"status": "success", "stored": last_location}

@app.get("/location")
def get_location():
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location