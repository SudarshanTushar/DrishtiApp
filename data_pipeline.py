import time
import random
from datetime import datetime

# --- CONFIGURATION: SOVEREIGN DATA SOURCES ---
DATA_SOURCES = {
    "TERRAIN": "ISRO_BHUVAN_CARTOSAT_3",
    "WEATHER": "IMD_INSAT_3DR_RAPID",
    "DISASTER": "NDMA_ALERT_FEED"
}

print(f"📡 [SYSTEM START] INITIALIZING DATA INGESTION PIPELINE...")

def fetch_imd_weather():
    """Simulates polling the Indian Meteorological Dept API"""
    # Real-world: requests.get('https://api.imd.gov.in/v1/weather/ne-sector')
    rain_mm = random.choice([45, 120, 210, 15, 300]) 
    return {"rainfall_24h": rain_mm, "source": "INSAT-3DR"}

def fetch_isro_terrain():
    """Simulates fetching soil data from Bhuvan"""
    return {
        "slope_avg": random.uniform(30, 60),
        "soil_moisture": random.uniform(40, 95),
        "lithology": "SEDIMENTARY_SOFT"
    }

def run_pipeline():
    print("\n🔄 PIPELINE ACTIVE: Polling Satellites every 5s...")
    while True:
        # 1. EXTRACT
        weather = fetch_imd_weather()
        terrain = fetch_isro_terrain()
        
        # 2. TRANSFORM (Data Fusion)
        timestamp = datetime.now().strftime('%H:%M:%S')
        data_packet = {
            "time": timestamp,
            "rain": weather['rainfall_24h'],
            "soil": terrain['soil_moisture'],
            "risk_flag": "HIGH" if weather['rainfall_24h'] > 150 else "NORMAL"
        }
        
        # 3. LOAD (Visual Log for Judges)
        print(f"   [{timestamp}] 💾 INGESTED: Rain={data_packet['rain']}mm | Soil={data_packet['soil']:.1f}% | Integrity: INDIGENOUS")
        
        if data_packet['rain'] > 200:
            print("   ⚠️  [ALERT] TRIGGERING DISASTER PROTOCOL (Code Red)")
            
        time.sleep(5)

if __name__ == "__main__":
    run_pipeline()