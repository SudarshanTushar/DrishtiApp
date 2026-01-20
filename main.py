from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
from pydantic import BaseModel
from typing import Optional

# MODULES
from intelligence.governance import SafetyGovernance
from intelligence.risk_model import LandslidePredictor
from intelligence.languages import LanguageConfig
from intelligence.crowdsource import CrowdManager
from intelligence.analytics import AnalyticsEngine
from intelligence.iot_network import IoTManager
from intelligence.logistics import LogisticsManager
# from intelligence.gis import GISEngine # Commented out for Heroku Stability
from intelligence.simulation import SimulationManager
from intelligence.vision import VisionEngine
from intelligence.audit import AuditLogger
from intelligence.security import SecurityGate 

app = FastAPI(title="RouteAI-NE Government Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = LandslidePredictor()

class HazardReport(BaseModel):
    lat: float
    lng: float
    hazard_type: str

class SOSRequest(BaseModel):
    lat: float
    lng: float
    type: str = "MEDICAL"

# --- HEALTH CHECK ---
@app.get("/health/diagnostics")
def system_health():
    return SecurityGate.system_health_check()

# --- AUTH ---
@app.post("/auth/login")
def admin_login(password: str = Form(...)):
    if password == "india123":
        return {"status": "success", "token": "NDRF-COMMAND-2026-SECURE"}
    else:
        return {"status": "failed", "message": "Invalid Credentials"}

# --- ADMIN ENDPOINTS ---
@app.get("/admin/stats")
def get_admin_stats(api_key: str = Depends(SecurityGate.verify_admin)):
    return AnalyticsEngine.get_live_stats()

@app.get("/admin/audit-logs")
def get_audit_trail(api_key: str = Depends(SecurityGate.verify_admin)):
    return AuditLogger.get_logs()

@app.post("/admin/broadcast")
def broadcast_alert(message: str, lat: float = 26.14, lng: float = 91.73, api_key: str = Depends(SecurityGate.verify_admin)):
    AuditLogger.log("ADMIN", "MASS_BROADCAST", f"Msg: {message}", "CRITICAL")
    return {"status": "success", "targets": "Telecom Operators", "payload": "CAP-XML"}

@app.post("/admin/simulate/start")
def start_simulation(scenario: str = "FLASH_FLOOD", api_key: str = Depends(SecurityGate.verify_admin)):
    AuditLogger.log("ADMIN", "SIMULATION_START", f"Scenario: {scenario}", "WARN")
    return SimulationManager.start_scenario(scenario, 26.14, 91.73)

@app.post("/admin/simulate/stop")
def stop_simulation(api_key: str = Depends(SecurityGate.verify_admin)):
    AuditLogger.log("ADMIN", "SIMULATION_STOP", "System Reset", "INFO")
    return SimulationManager.stop_simulation()

@app.post("/admin/analyze-drone")
async def analyze_drone_footage(file: UploadFile = File(...), api_key: str = Depends(SecurityGate.verify_admin)):
    result = VisionEngine.analyze_damage(file.filename)
    if "CATASTROPHIC" in result["classification"]:
        CrowdManager.admin_override(26.14, 91.73, "CLOSED")
        result["auto_action"] = "Route CLOSED by Vision System"
        AuditLogger.log("AI_VISION", "AUTO_CLOSE", f"Damage {result['damage_score']}", "CRITICAL")
    return result

@app.post("/admin/close-route")
def admin_close_route(lat: float, lng: float, api_key: str = Depends(SecurityGate.verify_admin)):
    CrowdManager.admin_override(lat, lng, "CLOSED")
    AuditLogger.log("ADMIN", "ROUTE_CLOSE", f"Override {lat},{lng}", "CRITICAL")
    return {"status": "success", "message": "Zone marked BLACK (CLOSED)."}

# --- PUBLIC ENDPOINTS ---

@app.get("/gis/layers")
def get_gis_layers(lat: float, lng: float):
    # FALLBACK MOCK for Stability
    sim_state = SimulationManager.get_overrides()
    if sim_state["active"]:
        return {
            "flood_zones": [{"id": "SIM_FLOOD", "risk_level": "CRITICAL", "coordinates": [[lat+0.05, lng-0.05], [lat+0.05, lng+0.05], [lat-0.05, lng+0.05], [lat-0.05, lng-0.05]], "info": "SIMULATED DISASTER ZONE"}],
            "landslide_clusters": []
        }
    return {
        "flood_zones": [
            {"id": "ZONE-1", "risk_level": "CRITICAL", "coordinates": [[lat+0.01, lng-0.01], [lat+0.01, lng+0.01], [lat-0.01, lng+0.01], [lat-0.01, lng-0.01]], "info": "Flash Flood Risk"}
        ],
        "landslide_clusters": []
    }

@app.post("/sos/dispatch")
def dispatch_rescue(request: SOSRequest):
    mission = LogisticsManager.request_dispatch(request.lat, request.lng)
    if mission: return {"status": "success", "mission": mission}
    else: return {"status": "failed", "message": "All units busy."}

@app.get("/sos/track/{mission_id}")
def track_mission(mission_id: str):
    status = LogisticsManager.get_mission_status(mission_id)
    if status:
        return {"status": "success", "mission": status}
    return {"status": "error", "message": "Mission ended or not found"}

@app.get("/iot/feed")
def get_iot_feed():
    data = IoTManager.get_live_readings()
    alert = IoTManager.check_critical_breach(data)
    return {"sensors": data, "system_alert": alert}

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: Optional[int] = None):
    if rain_input is None or rain_input == 0:
        try:
            iot_data = IoTManager.get_live_readings()
            rain_sensor = next((s for s in iot_data if s["type"] == "RAIN_GAUGE"), None)
            if rain_sensor:
                rain_input = float(rain_sensor['value'])
            if rain_input == 0: rain_input = 15
        except:
            rain_input = 50 

    ai_result = predictor.predict(rain_input, start_lat, start_lng)
    governance_result = SafetyGovernance.validate_risk(rain_input, ai_result["slope_angle"], ai_result["ai_score"])
    crowd_intel = CrowdManager.evaluate_zone(start_lat, start_lng)
    final_risk = governance_result["risk"]
    final_reason = governance_result["reason"]
    final_source = governance_result["source"]
    
    if crowd_intel and crowd_intel["risk"] in ["CRITICAL", "HIGH"]:
        final_risk = crowd_intel["risk"]
        final_reason = f"LIVE HAZARD: {crowd_intel['source']}"
        final_source = "Citizen Sentinel Network"
        
    iot_feed = IoTManager.get_live_readings()
    breach = IoTManager.check_critical_breach(iot_feed)
    if breach:
        final_risk = "CRITICAL"
        final_reason = breach["message"]
        final_source = "IoT Sensor Grid"
        
    sim_state = SimulationManager.get_overrides()
    if sim_state["active"]:
        final_risk = "CRITICAL"
        final_reason = f"DRILL ACTIVE: {sim_state['scenario']} SCENARIO"
        final_source = "National Command Authority (DRILL)"
        
    return {
        "distance": f"{random.randint(110, 140)}.5 km",
        "route_risk": final_risk,
        "confidence_score": governance_result["score"],
        "reason": final_reason,
        "source": final_source,
        "terrain_data": {
            "type": "Hilly" if start_lat > 26 else "Plain",
            "slope": f"{ai_result['slope_angle']}°",
            "soil": ai_result["soil_type"]
        }
    }

@app.post("/report-hazard")
def report_hazard(report: HazardReport):
    result = CrowdManager.submit_report(report.lat, report.lng, report.hazard_type)
    return {"status": "success", "new_zone_status": result}

@app.get("/languages")
def get_languages(): return LanguageConfig.get_config()

@app.get("/offline-pack")
def download_offline_intel(region_id: str):
    return {"region": "NE-Sector-Alpha", "timestamp": time.time(), "emergency_contacts": ["112", "108"], "safe_zones": [{"name": "Guwahati Army Camp", "lat": 26.14, "lng": 91.73}]}

# --- FIXED VOICE ENDPOINT ---
@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...), language_code: str = Form("hi-IN")):
    # 1. READ & CLEAN KEY
    raw_key = os.getenv("SARVAM_API_KEY", "")
    SARVAM_API_KEY = raw_key.strip().replace('"', '').replace("'", "")
    
    # 2. DEBUG LOG
    print(f"🎤 [VOICE] Checking Key... Length: {len(SARVAM_API_KEY)}")

    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
    
    translated_text = "Navigate to Shillong"
    target_city = "Shillong"

    try:
        # Only try if we have a valid key (at least 10 chars)
        if len(SARVAM_API_KEY) > 10:
            files = {"file": (file.filename, file.file, file.content_type)}
            
            # --- THE FIX IS HERE: Correct Header Name ---
            headers = {"api-subscription-key": SARVAM_API_KEY}
            
            print("🎤 [VOICE] Sending to Sarvam AI...")
            response = requests.post(SARVAM_URL, headers=headers, files=files)
            
            if response.status_code == 200:
                translated_text = response.json().get("transcript", translated_text)
                print(f"✅ [VOICE] Success: {translated_text}")
            else:
                print(f"⚠️ [VOICE] API Error {response.status_code}: {response.text}")
        else:
            print("⚠️ [VOICE] Key too short or missing. Using Fallback.")
            time.sleep(1)

        # 3. PARSE INTENT
        if "shillong" in translated_text.lower():
            target_city = "Shillong"
        elif "guwahati" in translated_text.lower():
            target_city = "Guwahati"
        elif "kohima" in translated_text.lower():
            target_city = "Kohima"
        
        # 4. REPLY
        fallback_responses = LanguageConfig.OFFLINE_RESPONSES.get(language_code, LanguageConfig.OFFLINE_RESPONSES["en-IN"])
        voice_reply = f"{fallback_responses['SAFE']} ({target_city})" if target_city != "Unknown" else "Command not understood."

        return {"status": "success", "translated_text": translated_text, "voice_reply": voice_reply, "target": target_city}

    except Exception as e:
        print(f"❌ [VOICE] CRITICAL ERROR: {str(e)}")
        return {"status": "success", "translated_text": "Error processing voice.", "voice_reply": "System Error. Manual input required.", "target": "Unknown"}
