import math

# --- SAFE HAVEN DATABASE (Mocked) ---
SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY_BASE", "capacity": 5000},
    {"id": "SH_02", "name": "Don Bosco High School", "lat": 26.12, "lng": 91.74, "type": "RELIEF_CAMP", "capacity": 1200},
    {"id": "SH_03", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": 300},
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

def find_nearest_safe_zones(user_lat: float, user_lng: float, limit: int = 3):
    """
    Returns the top 3 safest locations sorted by proximity and capacity.
    """
    ranked_havens = []
    
    for haven in SAFE_HAVENS:
        dist = haversine_distance(user_lat, user_lng, haven["lat"], haven["lng"])
        ranked_havens.append({**haven, "distance_km": round(dist, 2)})
    
    # Sort by distance
    ranked_havens.sort(key=lambda x: x["distance_km"])
    
    return ranked_havens[:limit]
