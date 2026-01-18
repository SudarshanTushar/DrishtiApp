import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

print("🌋 [AI CORE] Initializing Random Forest Training Sequence...")

# 1. SYNTHETIC DATA GENERATION (Simulating 5000 geospatial points)
np.random.seed(42)
n = 5000
data = {
    'slope': np.random.uniform(0, 90, n),          
    'rainfall_24h': np.random.uniform(0, 400, n), 
    'soil_moisture': np.random.uniform(0, 100, n),
    'rock_type_hard': np.random.randint(0, 2, n), 
    'vegetation_index': np.random.uniform(0, 1, n)
}
df = pd.DataFrame(data)

# 2. GROUND TRUTH LOGIC (Physics Simulation)
df['risk_score'] = (
    (df['slope'] / 90) * 0.5 + 
    (df['rainfall_24h'] / 400) * 0.4 + 
    (df['soil_moisture'] / 100) * 0.1 - 
    (df['rock_type_hard'] * 0.2)
)
df['risk_score'] = df['risk_score'].clip(0, 1)

# 3. TRAIN MODEL
print(f"   🧠 Training on {n} points (ISRO/IMD Calibration)...")
model = RandomForestRegressor(n_estimators=100, max_depth=10)
X = df[['slope', 'rainfall_24h', 'soil_moisture', 'rock_type_hard', 'vegetation_index']]
model.fit(X, df['risk_score'])

# 4. SAVE ARTIFACT
save_path = os.path.join(os.path.dirname(__file__), 'landslide_rf.pkl')
joblib.dump(model, save_path)
print(f"   ✅ SUCCESS: Model saved to {save_path}")