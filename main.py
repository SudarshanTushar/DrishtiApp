from fastapi import FastAPI, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

# MODULES
from intelligence.resources import ResourceSentinel
from intelligence.governance import SafetyGovernance, DecisionEngine
from intelligence.risk_model import LandslidePredictor
from intelligence.languages import LanguageConfig
from intelligence.crowdsource import CrowdManager
from intelligence.analytics import AnalyticsEngine
from intelligence.iot_network import IoTManager
from intelligence.logistics import LogisticsManager
from intelligence.simulation import SimulationManager
from intelligence.vision import VisionEngine
from intelligence.audit import AuditLogger
from intelligence.security import SecurityGate

from db.session import SessionLocal
from db.models import Route, AuthorityDecision

app = FastAPI(title="RouteAI-NE Government Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = LandslidePredictor()
PENDING_DECISIONS = []


class HazardReport(BaseModel):
    lat: float
    lng: float
    hazard_type: str


class UserProfile(BaseModel):
    name: str = "Unknown"
    phone: Optional[str] = None
    bloodType: Optional[str] = None
    medicalConditions: Optional[str] = None


class SOSRequest(BaseModel):
    lat: float
    lng: float
    type: str = "MEDICAL"
    user: Optional[UserProfile] = None


# --- AUTH LOGIN ---
@app.post("/auth/login")
def admin_login(password: str = Form(...)):
    valid_passwords = {"admin123", "india123", "ndrf2026", "command"}
    if password in valid_passwords:
        return {"status": "success", "token": "NDRF-COMMAND-2026-SECURE"}
    return {"status": "error", "message": "Invalid Credentials"}, 401

@app.post("/admin/broadcast")
def broadcast_alert(message: str, lat: float = 26.14, lng: float = 91.73, api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    AuditLogger.log("ADMIN", "MASS_BROADCAST", f"Msg: {message}", "CRITICAL")
    return {"status": "success", "targets": "Telecom Operators", "payload": "CAP-XML"}

# --- UPDATED SIMULATION ENDPOINTS (AUTO-INJECT) ---

@app.post("/admin/simulate/start")
def start_simulation(scenario: str = "FLASH_FLOOD", api_key: str = Depends(SecurityGate.verify_admin)):
    """
    TRIGGERS THE DEMO LOOP:
    1. Sets Global Simulation State to ACTIVE.
    2. Injects a CRITICAL PROPOSAL into the Governance Queue.
    """
    # 1. Start the Sim Engine
    scenario_data = SimulationManager.start_scenario(scenario, 26.14, 91.73)
    
    # 2. Log the Drill Start
    AuditLogger.log("ADMIN", "DRILL_INITIATED", f"Scenario: {scenario}", "WARN")
    
    # 3. AUTO-INJECT DECISION (The "Magic" Step)
    # This ensures the dashboard immediately flashes "ACTION REQUIRED"
    proposal = DecisionEngine.create_proposal(scenario_data, 26.14, 91.73)
    
    # Avoid duplicates
    existing = next((p for p in PENDING_DECISIONS if p["reason"] == scenario_data["reason"]), None)
    if not existing:
        PENDING_DECISIONS.insert(0, proposal)
    
    return {"status": "ACTIVE", "injected_proposal": proposal["id"]}

@app.post("/admin/simulate/stop")
def stop_simulation(api_key: str = Depends(SecurityGate.verify_admin)):
    """
    CLEANUP:
    1. Stops Sim Engine.
    2. Clears Pending Decisions (so the dashboard goes green).
    """
    AuditLogger.log("ADMIN", "DRILL_STOPPED", "System Reset to Normal", "INFO")
    
    # Clear the queue so the alert disappears
    PENDING_DECISIONS.clear()
    
    return SimulationManager.stop_simulation()

# --- MISSING COMMAND DASHBOARD ENDPOINTS ---

@app.get("/admin/resources")
def get_admin_resources(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Get all resource markers for CommandDashboard"""
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    resources_data = ResourceSentinel.get_all()
    return {"resources": resources_data}

@app.post("/admin/resources/{resource_id}/verify")
def verify_admin_resource(resource_id: str, api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Verify a resource marker"""
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    success = ResourceSentinel.verify_resource(resource_id)
    if success:
        AuditLogger.log("COMMANDER", "RESOURCE_VERIFIED", f"ID: {resource_id}", "INFO")
        return {"status": "success", "message": "Resource Verified"}
    return {"status": "error", "message": "Resource not found"}

@app.delete("/admin/resources/{resource_id}")
def delete_admin_resource(resource_id: str, api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Delete a resource marker"""
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    success = ResourceSentinel.delete_resource(resource_id)
    if success:
        AuditLogger.log("COMMANDER", "RESOURCE_DELETED", f"ID: {resource_id}", "INFO")
        return {"status": "success", "message": "Resource deleted"}
    return {"status": "error", "message": "Resource not found"}

@app.get("/admin/sos-feed")
def get_sos_feed(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Get live SOS emergency feed for CommandDashboard"""
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    # Generate simulated SOS feed for demo
    sos_items = [
        {"id": f"SOS-{i}", "type": random.choice(["MEDICAL", "TRAPPED", "FIRE", "FLOOD"]), 
         "location": f"Zone-{chr(65+i)}", "urgency": random.choice(["CRITICAL", "HIGH", "MEDIUM"]),
         "time": time.time() - (i * 300)} 
        for i in range(random.randint(3, 8))
    ]
    return {"feed": sos_items}

@app.post("/admin/sitrep/generate")
def generate_sitrep(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Generate a structured SITREP from Postgres (JSON output, Heroku-safe)."""
    from fastapi.responses import JSONResponse

    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key

    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    with SessionLocal() as session:
        latest_route = session.query(Route).order_by(Route.created_at.desc()).first()
        if not latest_route:
            return JSONResponse(status_code=404, content={"status": "empty", "message": "No routes available for SITREP"})

        latest_decision = (
            session.query(AuthorityDecision)
            .filter(AuthorityDecision.route_id == latest_route.id)
            .order_by(AuthorityDecision.created_at.desc())
            .first()
        )

    risk_level = latest_route.risk_level or "UNKNOWN"
    decision_status = latest_decision.decision if latest_decision else "PENDING"

    sitrep = {
        "executive_summary": f"Latest route {latest_route.id} assessed as {risk_level}. Decision status: {decision_status}.",
        "route_status": {
            "route_id": str(latest_route.id),
            "distance_km": latest_route.distance_km,
            "created_at": latest_route.created_at.isoformat() if latest_route.created_at else None,
        },
        "risk_level": risk_level,
        "authority_decision": {
            "decision": decision_status,
            "actor_role": latest_decision.actor_role if latest_decision else None,
            "decided_at": latest_decision.created_at.isoformat() if latest_decision and latest_decision.created_at else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return JSONResponse(content=sitrep)

@app.post("/admin/drone/analyze")
def analyze_drone_admin(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Drone footage analysis for CommandDashboard"""
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    
    result = VisionEngine.analyze_damage("drone_footage_simulated.jpg")
    if "CATASTROPHIC" in result["classification"]:
        CrowdManager.admin_override(26.14, 91.73, "CLOSED")
        result["auto_action"] = "Route CLOSED by Vision System"
        AuditLogger.log("AI_VISION", "AUTO_CLOSE", f"Damage {result['damage_score']}", "CRITICAL")
    return result

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
    # FALLBACK MOCK for Stability (Since we removed geopandas)
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

# --- UPDATED SOS ENDPOINT (With Identity Logging) ---
@app.post("/sos/dispatch")
def dispatch_rescue(request: SOSRequest):
    # 1. Log who needs help (Identity Check)
    victim_name = request.user.name if request.user else "Unknown Citizen"
    print(f"🚨 CRITICAL SOS: {victim_name} needs help at {request.lat}, {request.lng}")
    
    # 2. Call Logistics (Existing Logic)
    mission = LogisticsManager.request_dispatch(request.lat, request.lng)
    
    if mission: 
        return {
            "status": "success", 
            "mission": mission, 
            "message": f"Rescue Team Dispatched for {victim_name}"
        }
    else: 
        # Fallback if LogisticsManager is busy (For Demo mostly)
        mission_id = f"NDRF-{random.randint(1000,9999)}"
        return {
            "status": "success", 
            "mission": {"id": mission_id, "status": "DISPATCHED"},
            "message": "Emergency broadcast sent."
        }

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
    """
    COMPREHENSIVE AI-POWERED ROUTE RISK ANALYSIS
    Integrates: Landslide, Terrain, Weather, Crowd Intel, IoT Sensors, Satellite Data
    """
    
    # === 1. WEATHER & RAINFALL DATA ===
    if rain_input is None or rain_input == 0:
        try:
            iot_data = IoTManager.get_live_readings()
            rain_sensor = next((s for s in iot_data if s["type"] == "RAIN_GAUGE"), None)
            if rain_sensor:
                rain_input = float(rain_sensor['value'])
            if rain_input == 0: 
                rain_input = 15  # Default safe value
        except:
            rain_input = 50  # Conservative default
    
    # === 2. AI LANDSLIDE PREDICTION ===
    ai_result = predictor.predict(rain_input, start_lat, start_lng)
    landslide_score = ai_result["ai_score"]
    
    # === 3. TERRAIN ANALYSIS ===
    slope_angle = ai_result["slope_angle"]
    soil_type = ai_result["soil_type"]
    terrain_type = "Hilly" if start_lat > 26 else "Plain"
    
    # Terrain risk scoring
    terrain_risk_score = 0
    if slope_angle > 35:
        terrain_risk_score = 90
    elif slope_angle > 25:
        terrain_risk_score = 70
    elif slope_angle > 15:
        terrain_risk_score = 50
    else:
        terrain_risk_score = 20
    
    # === 4. GOVERNANCE LAYER VALIDATION ===
    governance_result = SafetyGovernance.validate_risk(rain_input, slope_angle, landslide_score)
    base_risk = governance_result["risk"]
    base_score = governance_result["score"]
    base_reason = governance_result["reason"]
    
    # === 5. CROWD INTELLIGENCE (Real-time Hazards) ===
    crowd_intel = CrowdManager.evaluate_zone(start_lat, start_lng)
    crowd_risk = "SAFE"
    crowd_alerts = []
    
    if crowd_intel and crowd_intel["risk"] in ["CRITICAL", "HIGH"]:
        crowd_risk = crowd_intel["risk"]
        crowd_alerts.append(f"⚠️ LIVE HAZARD: {crowd_intel['source']}")
    
    # === 6. IOT SENSOR NETWORK ===
    iot_feed = IoTManager.get_live_readings()
    breach = IoTManager.check_critical_breach(iot_feed)
    iot_risk = "SAFE"
    iot_alerts = []
    
    if breach:
        iot_risk = "CRITICAL"
        iot_alerts.append(f"🔴 {breach['message']}")
    
    # === 7. SIMULATION/DRILL CHECK ===
    sim_state = SimulationManager.get_overrides()
    drill_active = sim_state["active"]
    
    # === 8. MULTI-FACTOR RISK AGGREGATION ===
    # Derive landslide risk level from score
    landslide_risk_level = "HIGH" if landslide_score > 70 else "MODERATE" if landslide_score > 40 else "LOW"
    
    risk_factors = {
        "landslide": {"score": landslide_score, "level": landslide_risk_level},
        "terrain": {"score": terrain_risk_score, "level": "HIGH" if terrain_risk_score > 70 else "MODERATE" if terrain_risk_score > 40 else "LOW"},
        "weather": {"score": min(rain_input * 2, 100), "level": "HIGH" if rain_input > 50 else "MODERATE" if rain_input > 30 else "LOW"},
        "crowd_intel": {"score": 100 if crowd_risk == "CRITICAL" else 70 if crowd_risk == "HIGH" else 30, "level": crowd_risk},
        "iot_sensors": {"score": 100 if iot_risk == "CRITICAL" else 30, "level": iot_risk}
    }
    
    # Calculate composite risk score (weighted average)
    composite_score = (
        risk_factors["landslide"]["score"] * 0.35 +  # 35% weight
        risk_factors["terrain"]["score"] * 0.25 +     # 25% weight
        risk_factors["weather"]["score"] * 0.20 +     # 20% weight
        risk_factors["crowd_intel"]["score"] * 0.15 + # 15% weight
        risk_factors["iot_sensors"]["score"] * 0.05   # 5% weight
    )
    
    # === 9. FINAL RISK DETERMINATION ===
    final_risk = "SAFE"
    final_reason = base_reason
    final_source = governance_result["source"]
    recommendations = []
    
    # Override logic (priority: Drill > IoT > Crowd > AI)
    if drill_active:
        final_risk = "CRITICAL"
        final_reason = f"🚨 DRILL ACTIVE: {sim_state['scenario']} SCENARIO"
        final_source = "National Command Authority (DRILL)"
        recommendations.append("⚠️ Emergency drill in progress - Follow evacuation protocols")
    
    elif iot_risk == "CRITICAL":
        final_risk = "CRITICAL"
        final_reason = " | ".join(iot_alerts)
        final_source = "IoT Sensor Grid"
        recommendations.append("🔴 Real-time sensor breach detected")
        recommendations.append("📍 Reroute immediately to alternate path")
    
    elif crowd_risk in ["CRITICAL", "HIGH"]:
        final_risk = crowd_risk
        final_reason = " | ".join(crowd_alerts)
        final_source = "Citizen Sentinel Network"
        recommendations.append("👥 Recent civilian hazard reports detected")
        recommendations.append("🛡️ Exercise extreme caution")
    
    elif composite_score >= 75:
        final_risk = "CRITICAL"
        final_reason = f"Multi-factor high-risk assessment: Landslide probability {landslide_score}%, Slope {slope_angle}°, Heavy rainfall {rain_input}mm"
        final_source = "AI Risk Engine + Satellite Data"
        recommendations.append("🚫 Route NOT recommended")
        recommendations.append("📞 Contact local authorities")
    
    elif composite_score >= 60:
        final_risk = "HIGH"
        final_reason = f"Elevated risk factors: {landslide_risk_level} landslide risk, challenging terrain"
        final_source = "Integrated Risk Assessment"
        recommendations.append("⚠️ Proceed with extreme caution")
        recommendations.append("🧭 Monitor weather updates")
    
    elif composite_score >= 40:
        final_risk = "MODERATE"
        final_reason = f"Moderate risk conditions detected: {terrain_type} terrain, {rain_input}mm rainfall"
        final_source = "Terrain & Weather Analysis"
        recommendations.append("ℹ️ Stay alert and informed")
        recommendations.append("📱 Keep emergency contacts ready")
    
    else:
        final_risk = "SAFE"
        final_reason = f"Route cleared: Low risk assessment across all factors"
        final_source = "Comprehensive Safety Validation"
        recommendations.append("✅ Route approved for travel")
        recommendations.append("🗺️ Maintain situational awareness")
    
    # === 10. DISTANCE CALCULATION ===
    import math
    # Haversine formula for distance
    R = 6371  # Earth radius in km
    lat1, lon1 = math.radians(start_lat), math.radians(start_lng)
    lat2, lon2 = math.radians(end_lat), math.radians(end_lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    
    # === 11. RETURN COMPREHENSIVE ANALYSIS ===
    return {
        "distance": f"{distance:.1f} km",
        "route_risk": final_risk,
        "confidence_score": int(composite_score),
        "reason": final_reason,
        "source": final_source,
        "recommendations": recommendations,
        "risk_breakdown": {
            "landslide_risk": risk_factors["landslide"]["score"],
            "terrain_risk": risk_factors["terrain"]["score"],
            "weather_risk": risk_factors["weather"]["score"],
            "crowd_intel": risk_factors["crowd_intel"]["score"],
            "iot_sensors": risk_factors["iot_sensors"]["score"]
        },
        "terrain_data": {
            "type": terrain_type,
            "slope": f"{slope_angle}°",
            "soil": soil_type,
            "elevation": "High" if start_lat > 27 else "Medium" if start_lat > 26 else "Low"
        },
        "weather_data": {
            "rainfall_mm": rain_input,
            "severity": "Heavy" if rain_input > 50 else "Moderate" if rain_input > 30 else "Light"
        },
        "alerts": crowd_alerts + iot_alerts,
        "timestamp": int(time.time())
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

# --- FIXED VOICE ENDPOINT (Uses api-subscription-key) ---
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
            
            # THE FIX: Sarvam uses 'api-subscription-key'
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
        # Return success with error message so app doesn't crash on client side
        return {"status": "success", "translated_text": "Error processing voice.", "voice_reply": "System Error. Manual input required.", "target": "Unknown"}


# --- MESH NETWORK RELAY (HYBRID DEMO) ---
# This allows two phones to "chat" using the server as a bridge
# mimicking how they would chat over a real mesh network.

MESH_BUFFER = []

class MeshMessage(BaseModel):
    sender: str
    text: str
    timestamp: float

@app.post("/mesh/send")
def send_mesh_message(msg: MeshMessage):
    MESH_BUFFER.append(msg.dict())
    # Keep only last 50 messages
    if len(MESH_BUFFER) > 50:
        MESH_BUFFER.pop(0)
    return {"status": "sent"}

@app.get("/mesh/messages")
def get_mesh_messages():
    return MESH_BUFFER
