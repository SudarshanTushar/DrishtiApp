import math
import random
import time

# Mock Safe Haven Database
SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Base", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": "HIGH"},
    {"id": "SH_02", "name": "Don Bosco School", "lat": 26.12, "lng": 91.74, "type": "CIVILIAN", "capacity": "MEDIUM"},
    {"id": "SH_03", "name": "Civil Hospital", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": "LOW"}
]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_routes(start_lat, start_lng, end_lat, end_lng, rain_input):
    """Simulates Routing Logic"""
    time.sleep(0.5) # Simulating compute time
    
    route_fast = {
        "id": "fast", "label": "USUAL ROUTE", "distance": "124.5 km",
        "time": "3h 10m", "risk": "HIGH", "hazard": "Landslide at Mile 40", "color": "#ef4444"
    }
    route_safe = {
        "id": "safe", "label": "SECURE ROUTE", "distance": "148.2 km",
        "time": "4h 05m", "risk": "LOW", "hazard": "None", "color": "#10b981"
    }

    recommended = route_safe if rain_input > 40 else route_fast

    return {
        "routes": [route_fast, route_safe],
        "recommended_id": recommended["id"],
        "confidence_score": random.randint(88, 99)
    }

def find_nearest_safe_zones(lat, lng):
    """Finds top 3 safe zones"""
    ranked = []
    for haven in SAFE_HAVENS:
        dist = haversine_distance(lat, lng, haven["lat"], haven["lng"])
        ranked.append({**haven, "distance_km": round(dist, 2)})
    ranked.sort(key=lambda x: x["distance_km"])
    return ranked[:3]
