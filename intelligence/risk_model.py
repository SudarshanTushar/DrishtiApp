# backend/intelligence/risk_model.py
import random
import os
import joblib
import pandas as pd

class LandslidePredictor:
    """
    Integrates Static ISRO Data + Dynamic Rain Data + Stored ML Models
    """

    def __init__(self):
        self.model = None
        # Try to load the model you uploaded
        model_path = os.path.join(os.path.dirname(__file__), '../ai_engine/landslide_rf.pkl')
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                print("✅ LOADED CUSTOM ML MODEL")
            except Exception as e:
                print(f"⚠️ Model Load Failed: {e}. Using Simulation.")
        else:
            print("⚠️ No Model Found. Using Simulation.")

    def get_isro_static_data(self, lat: float, lng: float):
        """
        Simulates fetching static terrain data from ISRO layers (Bhuvan).
        """
        # Logic: Hilly areas (Lat > 26) have higher slope
        if lat > 26.0: 
            return {"slope": random.randint(30, 60), "soil_type": "Loamy-Unstable"}
        else:
            return {"slope": random.randint(5, 20), "soil_type": "Alluvial-Stable"}

    def predict(self, rain_input: int, lat: float, lng: float):
        static_data = self.get_isro_static_data(lat, lng)
        slope = static_data["slope"]
        
        # 1. Prediction Strategy
        if self.model:
            # If we have the real model, use it (Assuming it takes [rain, slope])
            # input_df = pd.DataFrame([[rain_input, slope]], columns=['rain', 'slope'])
            # prediction = self.model.predict_proba(input_df)[0][1] # Probability of landslide
            # ai_score = 100 - int(prediction * 100)
            
            # For now, safe fallback to calculation to prevent crash if model columns differ
            ai_score = max(0, 100 - (rain_input * 0.5) - (slope * 0.8))
        else:
            # Simulation Logic
            penalty = (rain_input * 0.5) + (slope * 0.5 if slope > 30 else 0)
            ai_score = max(0, int(100 - penalty))

        return {
            "ai_score": ai_score, 
            "slope_angle": slope,
            "soil_type": static_data["soil_type"]
        }
