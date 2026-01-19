# backend/intelligence/iot_network.py
import time
import random
from intelligence.simulation import SimulationManager # NEW IMPORT

class IoTManager:
    """
    Manages physical sensors. Now supports Simulation Overrides.
    """
    
    SENSORS = {
        "SENS_001": {"type": "RIVER_GAUGE", "lat": 26.18, "lng": 91.75, "location": "Brahmaputra Bank"},
        "SENS_002": {"type": "RAIN_GAUGE", "lat": 25.60, "lng": 91.90, "location": "Shillong Slope A"},
        "SENS_003": {"type": "SOIL_MOISTURE", "lat": 25.80, "lng": 93.00, "location": "NH-06 Pass"}
    }

    @staticmethod
    def get_live_readings():
        telemetry = []
        sim_state = SimulationManager.get_overrides() # Check for Simulation
        
        for sensor_id, meta in IoTManager.SENSORS.items():
            status = "NORMAL"
            value = 0.0
            unit = ""

            # --- SIMULATION OVERRIDE LOGIC ---
            if sim_state["active"] and sim_state["scenario"] == "FLASH_FLOOD":
                # If Flash Flood scenario, SPIKE the river gauges
                if meta["type"] == "RIVER_GAUGE":
                    value = random.uniform(14.5, 16.0) # Critical Levels
                    status = "CRITICAL"
                    unit = "m"
                elif meta["type"] == "RAIN_GAUGE":
                    value = random.uniform(110, 150)
                    status = "CRITICAL"
                    unit = "mm/hr"
                else:
                    value = random.uniform(50, 80)
                    unit = "%"
            # ----------------------------------
            else:
                # Normal Operation (Random Fluctuation)
                if meta["type"] == "RIVER_GAUGE":
                    value = random.uniform(8.0, 12.0)
                    unit = "m"
                    if value > 11.5: status = "WARNING"
                elif meta["type"] == "RAIN_GAUGE":
                    value = random.uniform(0, 40)
                    unit = "mm/hr"
                elif meta["type"] == "SOIL_MOISTURE":
                    value = random.uniform(20, 60)
                    unit = "%"

            telemetry.append({
                "id": sensor_id,
                "type": meta["type"],
                "lat": meta["lat"],
                "lng": meta["lng"],
                "location": meta["location"],
                "value": round(value, 2),
                "unit": unit,
                "status": status,
                "last_update": time.time()
            })

        return telemetry

    @staticmethod
    def check_critical_breach(telemetry_data):
        for reading in telemetry_data:
            if reading["status"] == "CRITICAL":
                return {
                    "alert": True,
                    "message": f"🚨 CRITICAL ALERT: {reading['type']} breach at {reading['location']}. WATER LEVEL: {reading['value']}{reading['unit']}. EVACUATE.",
                    "zone_lat": reading["lat"],
                    "zone_lng": reading["lng"]
                }
        return None
