import os
from fastapi import FastAPI, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key from environment
API_KEY = os.getenv("api_key")

# Stored data
last_location: Optional[dict] = None

# Models
class Location(BaseModel):
    coor: str
    acc:  float
    time: str
    date: str

# Update location endpoint
@app.post("/update/location")
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
        "acc": location.acc,
        "time": location.time,
        "date": location.date
    }
    return {"status": "success", "stored": last_location}

# Get location endpoint (protected by API key)
@app.get("/location")
def get_location(api_key: str = Query(..., description="API key for access")):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location

# Root page with login
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <html>
        <head><title>Login</title></head>
        <body>
            <h2>Enter Password to access map</h2>
            <form action="/" method="post">
                <input type="text" name="key" placeholder="Password" />
                <button type="submit">Submit</button>
            </form>
        </body>
    </html>
    """

@app.post("/", response_class=HTMLResponse)
async def login_submit(key: str = Form(...)):
    if key != API_KEY:
        return """
        <html><body>
            <h2>Incorrect Password</h2>
            <a href="/">Try again</a>
        </body></html>
        """
    
    # Serve the HTML map page using Leaflet CDN
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phone Location Viewer</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
            #info {{ padding: 10px; text-align: center; background: #f0f0f0; }}
            #map {{ height: 80vh; width: 100%; }}
            button {{ padding: 10px 15px; margin-top: 5px; cursor: pointer; }}
            #details {{ margin-top: 5px; white-space: pre-line; }}
        </style>
    </head>
    <body>
        <div id="info">
            <button onclick="fetchLocation()">Get Last Location</button>
            <div id="details">Press the button to fetch the location.</div>
        </div>
        <div id="map"></div>

        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            const API_KEY = "{API_KEY}";
            const LOCATION_URL = `/location?api_key=${{API_KEY}}`;

            const map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            let marker;
            let circle;

            async function fetchLocation() {{
                try {{
                    const locResp = await fetch(LOCATION_URL);
                    if (!locResp.ok) throw new Error('Failed fetching location');

                    const locData = await locResp.json();

                    const lat = parseFloat(locData.lat);
                    const lon = parseFloat(locData.lon);
                    const acc = parseFloat(locData.acc);
                    let locTime = locData.time.replace('.', ':');

                    document.getElementById('details').innerText =
                        `Location Timestamp: ${{locTime}} ${{locData.date}}\\nAccuracy: ±${{acc}} m`;

                    // Remove previous marker and circle
                    if(marker) map.removeLayer(marker);
                    if(circle) map.removeLayer(circle);

                    // Add marker
                    marker = L.marker([lat, lon]).addTo(map)
                              .bindPopup(`Last Known Location<br>Accuracy: ±${{acc}} m`)
                              .openPopup();

                    // Add circle representing accuracy
                    circle = L.circle([lat, lon], {{ radius: acc, color: 'blue', fillColor: '#add8e6', fillOpacity: 0.3 }}).addTo(map);

                    map.setView([lat, lon], 15);

                }} catch (err) {{
                    document.getElementById('details').innerText = "Error fetching location: " + err;
                }}
            }}
        </script>
    </body>
    </html>
    """
