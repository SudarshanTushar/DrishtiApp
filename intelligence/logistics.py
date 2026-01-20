import time
import math

class LogisticsManager:
    # Simulating a database of active missions
    active_missions = {}

    @staticmethod
    def request_dispatch(user_lat, user_lng):
        mission_id = f"MSN-{int(time.time())}"
        
        # 1. Spawn Unit slightly away from user (approx 2-3km)
        # 0.02 deg ~ 2.2km
        start_lat = user_lat + 0.02
        start_lng = user_lng + 0.02

        mission = {
            "mission_id": mission_id,
            "status": "DISPATCHED",
            "start_time": time.time(),
            "user_loc": (user_lat, user_lng),
            "unit": {
                "id": "UNIT-ALPHA",
                "type": "DRONE_AMBULANCE",
                "lat": start_lat,
                "lng": start_lng,
                "speed": 0.0005 # Lat/Lng movement per tick
            }
        }
        
        LogisticsManager.active_missions[mission_id] = mission
        return mission

    @staticmethod
    def get_mission_status(mission_id):
        mission = LogisticsManager.active_missions.get(mission_id)
        if not mission:
            return None

        # 2. CALCULATE MOVEMENT (Linear Interpolation)
        # Move unit closer to user
        unit_lat, unit_lng = mission['unit']['lat'], mission['unit']['lng']
        target_lat, target_lng = mission['user_loc']

        # Vector towards target
        d_lat = target_lat - unit_lat
        d_lng = target_lng - unit_lng
        distance = math.sqrt(d_lat**2 + d_lng**2)

        # Stop if close enough
        if distance < 0.0005:
            mission['status'] = "ARRIVED"
            mission['eta_minutes'] = 0
        else:
            # Move by speed factor
            speed = mission['unit']['speed']
            move_lat = (d_lat / distance) * speed
            move_lng = (d_lng / distance) * speed
            
            mission['unit']['lat'] += move_lat
            mission['unit']['lng'] += move_lng
            
            # Estimate ETA (Simple distance / speed)
            mission['eta_minutes'] = int(distance * 100) # Rough scaler

        return mission
