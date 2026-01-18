import random
import time
from datetime import datetime

# --- MOCK GIS DATA (Simulating Polygons from ISRO Bhuvan) ---
# Format: { "id": "zone_1", "type": "LANDSLIDE", "risk": "CRITICAL", "bounds": [lat_min, lat_max, lng_min, lng_max] }
RISK_ZONES = [
    {"id": "LS_01", "name": "Jorabat Landslide Sector", "type": "LANDSLIDE", "severity": "CRITICAL", "bounds": (26.1, 26.2, 91.7, 91.9)},
    {"id": "FL_04", "name": "Barak Valley Flood Plain", "type": "FLOOD", "severity": "HIGH", "bounds": (24.8, 25.0, 92.5, 92.8)},
]

def get_risk_heatmap():
    """
    Returns a GeoJSON-like structure of current active risk zones.
    Used by Frontend to draw Red overlays on the map.
    """
    # In production, this would fetch from a PostGIS database updated by data_pipeline.py
    active_zones = []
    
    # Simulate dynamic weather updates
    weather_factor = random.choice(["CLEAR", "STORM", "CYCLONE"])
    
    for zone in RISK_ZONES:
        # If storm, risk expands
        if weather_factor == "STORM":
            active_zones.append({
                **zone,
                "current_status": "ACTIVE",
                "last_update": datetime.now().strftime("%H:%M:%S"),
                "instruction": "AVOID AREA - DO NOT ENTER"
            })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "weather_context": weather_factor,
        "zones": active_zones
    }

def check_geofence(lat: float, lng: float):
    """
    Checks if a user's coordinate falls inside any known Risk Zone.
    """
    for zone in RISK_ZONES:
        lat_min, lat_max, lng_min, lng_max = zone["bounds"]
        if lat_min <= lat <= lat_max and lng_min <= lng <= lng_max:
            return {
                "in_danger_zone": True,
                "zone_details": zone,
                "alert_level": "RED"
            }
    
    return {"in_danger_zone": False, "alert_level": "GREEN"}
