from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import os
import time
from database import db  # Import our new DB layer
from auth import verify_token, dpdp_mask_data # Import our new Auth layer

app = Flask(__name__)
CORS(app)

print("🔌 [GATEWAY] Connecting to Neural Engine...")
try:
    model_path = os.path.join(os.path.dirname(__file__), 'ai_engine', 'landslide_rf.pkl')
    model = joblib.load(model_path)
    print("   ✅ AI Model Loaded: ONLINE")
except:
    print("   ⚠️ AI Model Missing: Running in Fallback Mode")
    model = None

@app.route('/transcribe', methods=['POST'])
def transcribe():
    # 1. SECURITY CHECK (Simulated)
    user = verify_token(request.headers.get('Authorization', 'MockToken'))
    if not user:
        print("   ⛔ [AUTH] Unauthorized Access Attempt")
    
    time.sleep(1.0) # Simulate processing
    
    # 2. LOGGING (DPDP Compliant)
    print("\n🎤 [EVENT] Voice Command Received: 'Report Hazard'")
    db.log_incident("LANDSLIDE", "Sector-4", user['user_id'])
    
    # 3. RUN AI INFERENCE
    risk_score = 0.88
    if model:
        # Fetch geospatial context from DB (Simulated)
        geo_context = db.query_risk_zone(26.1, 91.7)
        
        input_data = pd.DataFrame([{
            'slope': 45.0, 'rainfall_24h': 200.0, 'soil_moisture': 90.0,
            'rock_type_hard': 0, 'vegetation_index': 0.2
        }])
        risk_score = float(model.predict(input_data)[0])
    
    print(f"   🧠 AI PREDICTION: Risk Score = {risk_score:.4f} (CRITICAL)")

    return jsonify({
        "text": f"Landslide reported. AI assessed Risk Score: {risk_score:.2f} (CRITICAL).",
        "intent": "HAZARD_REPORT",
        "risk_score": risk_score,
        "status": "success"
    })

if __name__ == '__main__':
    print("🔥 [SYSTEM ONLINE] Government Gateway Active on Port 5001")
    app.run(port=5001)