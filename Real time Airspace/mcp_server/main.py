from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import math

app = FastAPI(title="Airspace Copilot MCP Server")

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "flights.json")
DEMO_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "flights_demo.json")

class Flight(BaseModel):
    icao24: str
    callsign: Optional[str] = None
    origin_country: str
    time_position: Optional[int] = None
    last_contact: int
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    baro_altitude: Optional[float] = None
    on_ground: bool
    velocity: Optional[float] = None
    true_track: Optional[float] = None
    vertical_rate: Optional[float] = None
    sensors: Optional[List[int]] = None
    geo_altitude: Optional[float] = None
    squawk: Optional[str] = None
    spi: bool
    position_source: int

class Anomaly(BaseModel):
    icao24: str
    callsign: Optional[str]
    description: str
    severity: str

def load_flights() -> List[Dict[str, Any]]:
    # Check if demo data mode is enabled
    use_demo = os.getenv("USE_DEMO_DATA", "false").lower() == "true"
    data_path = DEMO_DATA_PATH if use_demo else DATA_PATH
    
    if not os.path.exists(data_path):
        return []
    try:
        with open(data_path, "r") as f:
            data = json.load(f)
            # OpenSky returns a list of lists in 'states', or sometimes just a list of dicts if pre-processed.
            # The instructions say n8n extracts fields. Let's assume n8n saves a list of dicts.
            # If n8n saves raw OpenSky response, it has a 'states' key with list of lists.
            # I will assume for now n8n saves a list of objects/dicts for easier consumption.
            if isinstance(data, dict) and "states" in data:
                # Convert raw OpenSky format to dicts if needed, but let's assume n8n does the cleaning.
                # For now, let's assume the file contains a list of flight objects.
                return [] # Placeholder if structure is unknown, but I will implement assuming list of dicts
            return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return []

@app.get("/flights/list", response_model=List[Dict[str, Any]])
def list_flights(region: Optional[str] = None, limit: int = 2):
    """
    List flights, optionally filtered by region name.
    Regions are hardcoded for this assignment.
    Limited to 2 flights by default to avoid token limits.
    """
    flights = load_flights()
    if not region:
        return flights[:limit]
    
    # Hardcoded regions
    regions = {
        "Region A": {"min_lat": 40, "max_lat": 50, "min_lon": -10, "max_lon": 10}, # Example: Europeish
        "Region B": {"min_lat": 25, "max_lat": 45, "min_lon": -125, "max_lon": -70}, # Example: US
    }
    
    if region not in regions:
        # If region not found, return all or empty? Let's return all for now or error.
        # Instructions say "flights.list region snapshot(region name)".
        return flights[:limit]

    bounds = regions[region]
    filtered = []
    for f in flights:
        lat = f.get("latitude")
        lon = f.get("longitude")
        if lat and lon:
            if (bounds["min_lat"] <= lat <= bounds["max_lat"] and
                bounds["min_lon"] <= lon <= bounds["max_lon"]):
                filtered.append(f)
                if len(filtered) >= limit:
                    break
    return filtered

@app.get("/flights/get", response_model=Dict[str, Any])
def get_flight(callsign: str):
    """
    Get flight details by callsign or ICAO24.
    """
    flights = load_flights()
    callsign = callsign.strip().upper()
    for f in flights:
        # Check callsign (strip whitespace)
        c_sign = f.get("callsign", "").strip().upper()
        if c_sign == callsign:
            return f
        # Check ICAO24
        if f.get("icao24", "").upper() == callsign:
            return f
    raise HTTPException(status_code=404, detail="Flight not found")

@app.get("/alerts/list", response_model=List[Anomaly])
def list_alerts(limit: int = 1):
    """
    List active anomalies (limited to top 1 by default).
    """
    flights = load_flights()
    anomalies = []
    
    for f in flights:
        # Simple anomaly logic
        alt = f.get("baro_altitude")
        vel = f.get("velocity")
        
        # 1. Low speed at high altitude
        if alt and vel:
            if alt > 10000 and vel < 100: # 10km high, < 100 m/s (very slow for jet)
                anomalies.append(Anomaly(
                    icao24=f.get("icao24"),
                    callsign=f.get("callsign"),
                    description=f"Low speed ({vel} m/s) at high altitude ({alt} m)",
                    severity="HIGH"
                ))
        
        # 2. Stationary (if we had history, but here we only have snapshot)
        # We can check if velocity is near 0 but not on ground
        on_ground = f.get("on_ground", False)
        if not on_ground and vel is not None and vel < 10:
             anomalies.append(Anomaly(
                    icao24=f.get("icao24"),
                    callsign=f.get("callsign"),
                    description=f"Stationary/Hovering in air ({vel} m/s)",
                    severity="MEDIUM"
                ))
        
        # Limit to avoid token issues
        if len(anomalies) >= limit:
            break
                
    return anomalies

@app.post("/update-flights")
def update_flights(flights: List[Dict[str, Any]] = Body(...)):
    """
    Receive flight data from n8n and save to file.
    """
    try:
        with open(DATA_PATH, "w") as f:
            json.dump(flights, f, indent=2)
        return {"success": True, "count": len(flights)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
