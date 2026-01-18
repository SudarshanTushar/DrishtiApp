import math
import random
import time

# --- MOCK DATA (Ideally this comes from a database) ---
SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY_BASE", "capacity": 5000},
    {"id": "SH_02", "name": "Don Bosco High School", "lat": 26.12, "lng": 91.74, "type": "RELIEF_CAMP", "capacity": 1200},
    {"id": "SH_03", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": 300},
    {"id": "SH_04", "name": "Kohima Science College", "lat": 25.66, "lng": 94.10, "type": "RELIEF_CAMP", "capacity": 2000},
    {"id": "SH_05", "name": "Dimapur Airport Shelter", "lat": 25.88, "lng": 93.77, "type": "LOGISTICS", "capacity": 5000}
]

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates distance in KM between two coordinates."""
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_routes(start_lat, start_lng, end_lat, end_lng, rain_input):
    """
    Simulates finding a Fast vs. Safe route based on rain intensity.
    """
    # Simulate processing delay
    time.sleep(0.5)

    route_fast = {
        "id": "fast",
        "label": "USUAL ROUTE",
        "distance": "124.5 km",
        "time": "3h 10m",
        "risk": "HIGH",
        "hazard": "Landslide at Mile 40",
        "color": "#ef4444"
    }
    route_safe = {
        "id": "safe",
        "label": "SECURE ROUTE",
        "distance": "148.2 km",
        "time": "4h 05m",
        "risk": "LOW",
        "hazard": "None",
        "color": "#10b981"
    }

    # Logic: If rain > 40mm, recommend Safe Route
    recommended_id = route_safe["id"] if rain_input > 40 else route_fast["id"]

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended_id,
        "confidence_score": random.randint(88, 99),
        "live_alerts": [{"type": "Heavy Rain", "loc": "En route", "severity": "Medium"}]
    }

def find_nearest_safe_zones(lat, lng, limit=3):
    """Finds top N safe havens sorted by proximity."""
    ranked = []
    for haven in SAFE_HAVENS:
        dist = haversine_distance(lat, lng, haven["lat"], haven["lng"])
        ranked.append({**haven, "distance_km": round(dist, 2)})
    
    ranked.sort(key=lambda x: x["distance_km"])
    return ranked[:limit]
