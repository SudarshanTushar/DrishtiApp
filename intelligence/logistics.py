# backend/intelligence/logistics.py
import math
import time
import random

class LogisticsManager:
    """
    Manages the 'Blue Force' (Rescue Assets).
    Calculates nearest responders and Green Corridor routes.
    """
    
    # Simulated Fleet Registry
    # In prod, this tracks real-time GPS of ambulances/NDRF trucks
    FLEET = [
        {"id": "NDRF_ALPHA", "type": "HEAVY_RESCUE", "lat": 26.10, "lng": 91.70, "status": "AVAILABLE"},
        {"id": "AMB_108_01", "type": "AMBULANCE", "lat": 25.60, "lng": 94.00, "status": "AVAILABLE"},
        {"id": "AMB_108_02", "type": "AMBULANCE", "lat": 26.15, "lng": 91.78, "status": "BUSY"},
        {"id": "DRONE_SQUAD", "type": "AERIAL_RECON", "lat": 25.58, "lng": 91.89, "status": "AVAILABLE"}
    ]

    active_missions = {}

    @staticmethod
    def calculate_distance(lat1, lng1, lat2, lng2):
        # Haversine approximation for speed
        return math.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2)

    @staticmethod
    def request_dispatch(victim_lat, victim_lng, urgency="HIGH"):
        """
        Finds the nearest available unit and assigns it.
        """
        best_unit = None
        min_dist = float('inf')

        for unit in LogisticsManager.FLEET:
            if unit["status"] != "AVAILABLE":
                continue
            
            dist = LogisticsManager.calculate_distance(victim_lat, victim_lng, unit["lat"], unit["lng"])
            if dist < min_dist:
                min_dist = dist
                best_unit = unit

        if best_unit:
            # Create Mission
            mission_id = f"MSN_{int(time.time())}"
            # Update Unit Status
            best_unit["status"] = "DISPATCHED"
            
            mission_details = {
                "mission_id": mission_id,
                "unit": best_unit,
                "eta_minutes": random.randint(5, 15), # Simulated ETA
                "status": "EN_ROUTE"
            }
            LogisticsManager.active_missions[mission_id] = mission_details
            return mission_details
        
        return None # No units available

    @staticmethod
    def get_mission_status(mission_id):
        return LogisticsManager.active_missions.get(mission_id)
