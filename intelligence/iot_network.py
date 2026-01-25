import requests
import random
from .simulation import SimulationManager

class IoTManager:
    # Guwahati Coordinates (Center of Ops)
    LAT = 26.14
    LNG = 91.73
    
    @staticmethod
    def get_live_readings():
        """
        Fetches REAL weather data from OpenMeteo API.
        If Simulation is ACTIVE, it overrides with 'Disaster Data'.
        """
        # 1. CHECK FOR SIMULATION OVERRIDE (The "Drill" Logic)
        sim_state = SimulationManager.get_overrides()
        if sim_state["active"]:
            # Return FAKE disaster data
            return [
                {"id": "S-01", "type": "RAIN_GAUGE", "value": sim_state["simulated_sensors"]["rain_gauge"], "unit": "mm"},
                {"id": "S-02", "type": "RIVER_LEVEL", "value": sim_state["simulated_sensors"]["water_level"], "unit": "cm"},
                {"id": "S-03", "type": "SOIL_MOISTURE", "value": 98, "unit": "%"}
            ]

        # 2. FETCH REAL DATA (The "Live" Logic)
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={IoTManager.LAT}&longitude={IoTManager.LNG}&current=rain,wind_speed_10m"
            response = requests.get(url, timeout=2)
            data = response.json()
            
            real_rain = data.get("current", {}).get("rain", 0.0)
            real_wind = data.get("current", {}).get("wind_speed_10m", 5.0)
            
            return [
                {"id": "S-01", "type": "RAIN_GAUGE", "value": real_rain, "unit": "mm"},
                {"id": "S-02", "type": "RIVER_LEVEL", "value": 45, "unit": "cm"}, # Nominal
                {"id": "S-03", "type": "WIND_SENSOR", "value": real_wind, "unit": "km/h"}
            ]
        except Exception as e:
            print(f" [IoT] Sensor Error: {e}")
            return [{"id": "S-ERR", "type": "STATUS", "value": "OFFLINE", "unit": ""}]

    @staticmethod
    def check_critical_breach(readings):
        """Returns True if any sensor exceeds safety thresholds."""
        for sensor in readings:
            if sensor["type"] == "RAIN_GAUGE" and float(sensor["value"]) > 80:
                return "FLOOD_RISK"
            if sensor["type"] == "RIVER_LEVEL" and float(sensor["value"]) > 150:
                return "EMBANKMENT_BREACH"
        return None
