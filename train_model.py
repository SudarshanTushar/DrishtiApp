import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import joblib

# --- CONFIGURATION ---
DATA_SIZE = 5000
print("🚀 Initializing Multi-Model Training Protocol...")

# ==========================================
# 1. TRAIN LANDSLIDE MODEL (The Mountain Brain)
# ==========================================
print("⛰️  Training Landslide Detection Model...")

# Logic: High Slope (>40) + Rain + Soil Moisture = Danger
lats = np.random.uniform(26.0, 29.5, DATA_SIZE) # Hills of Arunachal/Nagaland
slope = np.random.uniform(0, 80, DATA_SIZE)     # Steep slopes
rain = np.random.uniform(0, 400, DATA_SIZE)     # Heavy rain
soil = np.random.uniform(20, 100, DATA_SIZE)    # Saturation

landslide_risk = []
for i in range(DATA_SIZE):
    # Physics: Landslides need Slope AND Rain
    score = (slope[i] * 0.7) + (rain[i] * 0.3) + (soil[i] * 0.1)
    if score > 80: landslide_risk.append("CRITICAL")
    elif score > 50: landslide_risk.append("CAUTION")
    else: landslide_risk.append("SAFE")

df_landslide = pd.DataFrame({'slope': slope, 'rain': rain, 'soil': soil, 'risk': landslide_risk})

rf_model = RandomForestClassifier(n_estimators=100)
rf_model.fit(df_landslide[['slope', 'rain', 'soil']], df_landslide['risk'])
joblib.dump(rf_model, 'model_landslide.pkl')


# ==========================================
# 2. TRAIN FLOOD MODEL (The Valley Brain)
# ==========================================
print("🌊 Training Flood Prediction Model...")

# Logic: Low Elevation (<50m) + Rain + River Proximity = Danger
elevation = np.random.uniform(10, 2000, DATA_SIZE) # 10m (Assam plains) to 2000m
river_dist = np.random.uniform(0, 5000, DATA_SIZE) # Distance to river (meters)

flood_risk = []
for i in range(DATA_SIZE):
    # Physics: Floods happen at Low Elevation near Rivers
    # Low elevation contributes to risk (inverse relationship)
    elevation_factor = (2000 - elevation[i]) / 20 
    river_factor = (5000 - river_dist[i]) / 50
    
    score = (elevation_factor * 0.5) + (river_factor * 0.3) + (rain[i] * 0.2)
    
    if score > 120: flood_risk.append("CRITICAL")
    elif score > 80: flood_risk.append("CAUTION")
    else: flood_risk.append("SAFE")

df_flood = pd.DataFrame({'elevation': elevation, 'river_dist': river_dist, 'rain': rain, 'risk': flood_risk})

gb_model = GradientBoostingClassifier(n_estimators=100)
gb_model.fit(df_flood[['elevation', 'river_dist', 'rain']], df_flood['risk'])
joblib.dump(gb_model, 'model_flood.pkl')

print("✅ SYSTEMS ARMED: 'model_landslide.pkl' and 'model_flood.pkl' created.")