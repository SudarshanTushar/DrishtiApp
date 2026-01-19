# backend/intelligence/iot_network.py
import time
import random

class IoTManager:
    """
    Manages the network of physical sensors (Rain Gauges, River Sensors).
    """
    
    # Simulated Sensor Registry
    # In prod, this comes from a database of Hardware IDs
    SENSORS = {
        "SENS_001": {"type": "RIVER_GAUGE", "lat": 26.18, "lng": 91.75, "location": "Brahmaputra Bank"},
        "SENS_002": {"type": "RAIN_GAUGE", "lat": 25.60, "lng": 91.90, "location": "Shillong Slope A"},
        "SENS_003": {"type": "SOIL_MOISTURE", "lat": 25.80, "lng": 93.00, "location": "NH-06 Pass"}
    }

    @staticmethod
    def get_live_readings():
        """
        Simulates real-time telemetry from the field.
        """
        telemetry = []
        
        for sensor_id, meta in IoTManager.SENSORS.items():
            status = "NORMAL"
            value = 0.0
            unit = ""

            if meta["type"] == "RIVER_GAUGE":
                # Simulate rising water levels
                value = random.uniform(8.0, 14.0) # Meters
                unit = "m"
                if value > 12.0: status = "CRITICAL"
                elif value > 10.5: status = "WARNING"

            elif meta["type"] == "RAIN_GAUGE":
                value = random.uniform(0, 120) # mm/hr
                unit = "mm/hr"
                if value > 100: status = "CRITICAL"
                elif value > 60: status = "WARNING"

            elif meta["type"] == "SOIL_MOISTURE":
                value = random.uniform(20, 95) # % Saturation
                unit = "%"
                if value > 90: status = "CRITICAL"
            
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
        """
        Checks if any sensor has triggered a Red Alert.
        Returns a broadcast message if true.
        """
        for reading in telemetry_data:
            if reading["status"] == "CRITICAL":
                return {
                    "alert": True,
                    "message": f"CRITICAL BREACH: {reading['type']} at {reading['location']} ({reading['value']}{reading['unit']}). EVACUATE IMMEDIATE.",
                    "zone_lat": reading["lat"],
                    "zone_lng": reading["lng"]
                }
        return None
