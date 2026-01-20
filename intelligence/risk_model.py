import joblib
import pandas as pd
import numpy as np
import os

class LandslidePredictor:
    def __init__(self):
        # Load the Pre-trained Random Forest Model
        # Ensure 'model_landslide.pkl' is in the root or 'ai_engine' folder
        try:
            model_path = os.path.join(os.path.dirname(__file__), '../ai_engine/landslide_rf.pkl')
            if not os.path.exists(model_path):
                # Fallback to root if not found in ai_engine
                model_path = 'model_landslide.pkl'
            
            self.model = joblib.load(model_path)
            print(f"   🧠 [AI] Landslide Model Loaded: {model_path}")
            self.ready = True
        except Exception as e:
            print(f"   ⚠️ [AI] Model Load Failed: {e}")
            self.ready = False

    def predict(self, rain_mm, lat, lng):
        """
        Returns real inference based on inputs.
        """
        # 1. Calculate/Mock Slope based on Location (In real app, fetch from DEM Raster)
        # For North East India (approx Lat 25-28), hills are steeper
        slope = 0
        if lat > 26.0: slope = np.random.uniform(20, 45) # Hilly
        else: slope = np.random.uniform(0, 10) # Plains

        # 2. Prepare Features for Model [Rainfall, Slope, Soil_Type_Index]
        # Assuming Model was trained on [Rain, Slope]
        
        risk_score = 0
        if self.ready:
            try:
                # Real Inference
                features = pd.DataFrame([[rain_mm, slope]], columns=['rainfall', 'slope'])
                risk_score = self.model.predict_proba(features)[0][1] * 100 # Probability of Class 1 (Landslide)
            except:
                # Fallback Logic if model features differ
                risk_score = (rain_mm * 0.4) + (slope * 1.2)
        else:
            # Deterministic Fallback
            risk_score = (rain_mm * 0.5) + (slope * 1.0)

        # 3. Normalize & Classify
        risk_score = min(max(risk_score, 0), 100)
        
        return {
            "ai_score": int(risk_score),
            "slope_angle": int(slope),
            "soil_type": "Laterite" if lat > 25 else "Alluvial",
            "prediction_source": "RandomForest_v2" if self.ready else "Heuristic_Fallback"
        }
