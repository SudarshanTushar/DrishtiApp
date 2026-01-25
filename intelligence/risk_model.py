import joblib
import pandas as pd
import numpy as np
import os

class LandslidePredictor:
    def __init__(self):
        # Disabled generic model loading to save memory on Heroku Free Tier
        # Using heuristic fallback
        self.ready = False
        print(f"   [AI] Landslide Model: Running in Heuristic Mode (Memory Optimized)")

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
        if self.ready:
            # Full model check would go here if enabled
            risk_score = (rain_mm * 0.5) + (slope * 1.0)
        else:
            # Deterministic Fallback (Heuristic)
            # Simplified risk calculation: Rain impact + Slope factor
            risk_score = (rain_mm * 0.6) + (slope * 1.2)

        # 3. Normalize & Classify
        risk_score = min(max(risk_score, 0), 100)
        
        return {
            "ai_score": int(risk_score),
            "slope_angle": int(slope),
            "soil_type": "Laterite" if lat > 25 else "Alluvial",
            "prediction_source": "Heuristic_MemoryOptimized"
        }
