import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# --- 1. MOCK DATA GENERATOR (Training Phase) ---
# In production, replace this with 'landslide_data.csv'
def generate_training_data(n_samples=5000):
    np.random.seed(42)
    data = {
        'slope': np.random.uniform(0, 90, n_samples),          # Degrees
        'rainfall_24h': np.random.uniform(0, 400, n_samples),  # mm
        'soil_moisture': np.random.uniform(0, 100, n_samples), # %
        'rock_type_hard': np.random.randint(0, 2, n_samples),  # 0=Soft, 1=Hard
        'vegetation_index': np.random.uniform(0, 1, n_samples) # NDVI
    }
    df = pd.DataFrame(data)
    
    # --- PHYSICAL LAW SIMULATION (Ground Truth) ---
    # Risk increases with Slope and Rain. Hard rock reduces risk.
    df['risk_score'] = (
        (df['slope'] / 90) * 0.4 + 
        (df['rainfall_24h'] / 400) * 0.4 + 
        (df['soil_moisture'] / 100) * 0.1 - 
        (df['rock_type_hard'] * 0.2) - 
        (df['vegetation_index'] * 0.1)
    )
    # Add noise
    df['risk_score'] += np.random.normal(0, 0.05, n_samples)
    df['risk_score'] = df['risk_score'].clip(0, 1) # Ensure 0-1 range
    
    return df

# --- 2. TRAINING ENGINE ---
def train_landslide_model():
    print("🌋 Training Landslide Risk Model (RandomForest)...")
    df = generate_training_data()
    
    X = df[['slope', 'rainfall_24h', 'soil_moisture', 'rock_type_hard', 'vegetation_index']]
    y = df['risk_score']
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X, y)
    
    # Explainability Check
    importances = dict(zip(X.columns, model.feature_importances_))
    print(f"   ✅ Feature Impact: {importances}")
    
    # Save Model
    joblib.dump(model, 'landslide_rf.pkl')
    print("   💾 Model saved to 'landslide_rf.pkl'")

if __name__ == "__main__":
    train_landslide_model()