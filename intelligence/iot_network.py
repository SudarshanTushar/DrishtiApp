import requests
import random

class IoTManager:
    """
    Manages physical sensors and fetches live weather data.
    """

    @staticmethod
    def get_live_readings():
        # 1. Fetch Real Weather for Guwahati (26.14, 91.73)
        # Using Open-Meteo (No API Key needed)
        real_rain = 0
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=26.14&longitude=91.73&current=rain&hourly=rain"
            res = requests.get(url, timeout=2).json()
            real_rain = res['current']['rain'] # mm
        except:
            real_rain = random.randint(0, 5) # Fallback

        # 2. Simulate Sensor Grid based on Real Rain
        # If it's raining, water levels rise
        base_water_level = 48.0 + (real_rain * 0.5) 
        
        sensors = [
            {
                "id": "SENS-01",
                "type": "RIVER_GAUGE",
                "location": "Brahmaputra Alpha",
                "lat": 26.15,
                "lng": 91.74,
                "value": f"{base_water_level:.1f}",
                "unit": "m",
                "status": "CRITICAL" if base_water_level > 50 else "STABLE"
            },
            {
                "id": "SENS-02",
                "type": "RAIN_GAUGE",
                "location": "Shillong Outpost",
                "lat": 25.57,
                "lng": 91.89,
                "value": f"{real_rain}",
                "unit": "mm",
                "status": "WARNING" if real_rain > 10 else "NORMAL"
            },
            {
                "id": "SENS-03",
                "type": "SEISMIC",
                "location": "Tezpur Fault Line",
                "lat": 26.65,
                "lng": 92.79,
                "value": "2.1",
                "unit": "R",
                "status": "NORMAL"
            }
        ]
        return sensors

    @staticmethod
    def check_critical_breach(sensors):
        for s in sensors:
            if s['status'] == "CRITICAL":
                return {
                    "alert": True,
                    "sensor_id": s['id'],
                    "message": f"CRITICAL BREACH AT {s['location']} ({s['value']}{s['unit']})"
                }
        return None
