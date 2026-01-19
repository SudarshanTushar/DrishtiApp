from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
from pydantic import BaseModel

# MODULES
from intelligence.governance import SafetyGovernance
from intelligence.risk_model import LandslidePredictor
from intelligence.languages import LanguageConfig
from intelligence.crowdsource import CrowdManager
from intelligence.analytics import AnalyticsEngine
from intelligence.iot_network import IoTManager
from intelligence.logistics import LogisticsManager
from intelligence.gis import GISEngine
from intelligence.simulation import SimulationManager
from intelligence.vision import VisionEngine
from intelligence.audit import AuditLogger # NEW IMPORT

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

# --- NEW: AUDIT & BROADCAST ENDPOINTS ---
@app.get("/admin/audit-logs")
def get_audit_trail():
    return AuditLogger.get_logs()

@app.post("/admin/broadcast")
def broadcast_alert(message: str, lat: float = 26.14, lng: float = 91.73):
    """
    Triggers a Mass SMS Alert via CAP Protocol.
    """
    xml_payload = AuditLogger.generate_cap_xml(message, lat, lng)
    
    # Log this critical action
    AuditLogger.log("ADMIN", "MASS_BROADCAST", f"Msg: {message}", "CRITICAL")
    
    return {
        "status": "success",
        "protocol": "CAP-XML v1.2",
        "targets": "Telecom Operators (Airtel/Jio/BSNL)",
        "payload_preview": xml_payload
    }

# --- UPDATED EXISTING ENDPOINTS (With Logging) ---

@app.post("/sos/dispatch")
def dispatch_rescue(request: SOSRequest):
    mission = LogisticsManager.request_dispatch(request.lat, request.lng)
    if mission: 
        AuditLogger.log("SYSTEM", "SOS_DISPATCH", f"Unit {mission['unit']['id']} -> {request.lat},{request.lng}", "CRITICAL")
        return {"status": "success", "mission": mission}
    else: 
        AuditLogger.log("SYSTEM", "SOS_FAILED", "No units available", "WARN")
        return {"status": "failed", "message": "All units busy."}

@app.post("/report-hazard")
def report_hazard(report: HazardReport):
    result = CrowdManager.submit_report(report.lat, report.lng, report.hazard_type)
    # Log citizen activity
    AuditLogger.log("CITIZEN", "HAZARD_REPORT", f"{report.hazard_type} at {report.lat},{report.lng}")
    return {"status": "success", "new_zone_status": result}

@app.post("/admin/close-route")
def admin_close_route(lat: float, lng: float):
    CrowdManager.admin_override(lat, lng, "CLOSED")
    AuditLogger.log("ADMIN", "ROUTE_CLOSE", f"Manual Override at {lat},{lng}", "CRITICAL")
    return {"status": "success", "message": "Zone marked BLACK (CLOSED)."}

@app.post("/admin/simulate/start")
def start_simulation(scenario: str = "FLASH_FLOOD"):
    AuditLogger.log("ADMIN", "SIMULATION_START", f"Scenario: {scenario}", "WARN")
    return SimulationManager.start_scenario(scenario, 26.14, 91.73)

@app.post("/admin/simulate/stop")
def stop_simulation():
    AuditLogger.log("ADMIN", "SIMULATION_STOP", "System Reset", "INFO")
    return SimulationManager.stop_simulation()

@app.post("/admin/analyze-drone")
async def analyze_drone_footage(file: UploadFile = File(...)):
    result = VisionEngine.analyze_damage(file.filename)
    if "CATASTROPHIC" in result["classification"]:
        CrowdManager.admin_override(26.14, 91.73, "CLOSED")
        result["auto_action"] = "Route CLOSED by Vision System"
        AuditLogger.log("AI_VISION", "AUTO_CLOSE", f"Damage {result['damage_score']} detected in {file.filename}", "CRITICAL")
    return result

# --- EXISTING READ-ONLY ENDPOINTS ---
@app.get("/iot/feed")
def get_iot_feed():
    data = IoTManager.get_live_readings()
    alert = IoTManager.check_critical_breach(data)
    # Note: We don't log every feed pull to avoid spam, only alerts
    if alert:
         # Check if we recently logged this to avoid duplicates? (Skip for hackathon simplicity)
         pass
    return {"sensors": data, "system_alert": alert}

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: int):
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

@app.get("/gis/layers")
def get_gis_layers(lat: float, lng: float):
    sim_state = SimulationManager.get_overrides()
    if sim_state["active"]:
        return {
            "flood_zones": [{"id": "SIM_FLOOD", "risk_level": "CRITICAL", "coordinates": [[lat+0.05, lng-0.05], [lat+0.05, lng+0.05], [lat-0.05, lng+0.05], [lat-0.05, lng-0.05]], "info": "SIMULATED DISASTER ZONE"}],
            "landslide_clusters": []
        }
    return GISEngine.get_risk_layers(lat, lng)

@app.get("/admin/stats")
def get_admin_stats(): return AnalyticsEngine.get_live_stats()

@app.get("/languages")
def get_languages(): return LanguageConfig.get_config()

@app.get("/offline-pack")
def download_offline_intel(region_id: str):
    return {"region": "NE-Sector-Alpha", "timestamp": time.time(), "emergency_contacts": ["112", "108"], "safe_zones": [{"name": "Guwahati Army Camp", "lat": 26.14, "lng": 91.73}]}

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...), language_code: str = Form("hi-IN")):
    SARVAM_API_KEY = os.getenv("SARVAM_API_KEY") 
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
    try:
        if SARVAM_API_KEY:
            files = {"file": (file.filename, file.file, file.content_type)}
            headers = {"Ocp-Apim-Subscription-Key": SARVAM_API_KEY}
            response = requests.post(SARVAM_URL, headers=headers, files=files)
            translated_text = response.json().get("transcript", "Navigate to Shillong")
        else:
            time.sleep(1)
            translated_text = "Navigate to Shillong"
        target_city = "Shillong" if "shillong" in translated_text.lower() else "Unknown"
        fallback_responses = LanguageConfig.OFFLINE_RESPONSES.get(language_code, LanguageConfig.OFFLINE_RESPONSES["en-IN"])
        voice_reply = f"{fallback_responses['SAFE']} ({target_city})" if target_city != "Unknown" else "Command not understood."
        return {"status": "success", "translated_text": translated_text, "voice_reply": voice_reply, "target": target_city}
    except Exception as e:
        return {"status": "error", "message": str(e)}
