import os
from fastapi import FastAPI, HTTPException, Query, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (Leaflet CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# API key from environment
API_KEY = os.getenv("api_key")

# Stored data
last_location: Optional[dict] = None
last_connection: Optional[dict] = None

# Models
class Location(BaseModel):
    coor: str
    time: str
    date: str

class Connection(BaseModel):
    time: str
    date: str

# Update endpoints
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
        "time": location.time,
        "date": location.date
    }
    return {"status": "success", "stored": last_location}

@app.post("/update/connection")
def update_connection(connection: Connection):
    global last_connection
    last_connection = {
        "time": connection.time,
        "date": connection.date
    }
    return {"status": "success", "stored": last_connection}

# Get endpoints (protected by API key)
@app.get("/location")
def get_location(api_key: str = Query(..., description="API key for access")):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    if not last_location:
        raise HTTPException(status_code=404, detail="No location stored yet")
    return last_location

@app.get("/connection")
def get_connection(api_key: str = Query(..., description="API key for access")):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    if not last_connection:
        raise HTTPException(status_code=404, detail="No connection stored yet")
    return last_connection

# Root page with login
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return """
    <html>
        <head><title>Login</title></head>
        <body>
            <h2>Enter API Key to access map</h2>
            <form action="/" method="post">
                <input type="text" name="key" placeholder="API Key" />
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
            <h2>Invalid API Key</h2>
            <a href="/">Try again</a>
        </body></html>
        """
    
    # Serve the HTML map page using local Leaflet
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phone Location Viewer</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/leaflet/leaflet.css"/>
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

        <script src="/static/leaflet/leaflet.js"></script>
        <script>
            const API_KEY = "{API_KEY}";
            const LOCATION_URL = `/location?api_key=${{API_KEY}}`;
            const CONNECTION_URL = `/connection?api_key=${{API_KEY}}`;

            const map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            let marker;

            async function fetchLocation() {{
                try {{
                    const locResp = await fetch(LOCATION_URL);
                    const connResp = await fetch(CONNECTION_URL);
                    if (!locResp.ok || !connResp.ok) throw new Error('Failed fetching data');

                    const locData = await locResp.json();
                    const connData = await connResp.json();

                    const lat = parseFloat(locData.lat);
                    const lon = parseFloat(locData.lon);
                    let locTime = locData.time.replace('.', ':');
                    let connTime = connData.time.replace('.', ':');

                    document.getElementById('details').innerText =
                        `Location Timestamp: ${{locTime}} ${{locData.date}}\n` +
                        `Activity Timestamp: ${{connTime}} ${{connData.date}}`;

                    if(marker) map.removeLayer(marker);
                    marker = L.marker([lat, lon]).addTo(map)
                              .bindPopup("Last Known Location")
                              .openPopup();
                    map.setView([lat, lon], 15);

                }} catch (err) {{
                    document.getElementById('details').innerText = "Error fetching location: " + err;
                }}
            }}
        </script>
    </body>
    </html>
    """
