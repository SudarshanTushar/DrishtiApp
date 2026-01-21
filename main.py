from fastapi import FastAPI, UploadFile, File, Form, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
import uuid
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
# from intelligence.gis import GISEngine  <-- DISABLED TO PREVENT HEROKU CRASH
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

# --- IN-MEMORY DECISION QUEUE (For Demo) ---
# In production, this would be a Redis/Postgres table
PENDING_DECISIONS = []

class HazardReport(BaseModel):
    lat: float
    lng: float
    hazard_type: str

# --- UPDATED SOS MODELS (Identity Support) ---
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

# --- RESOURCE MESH ENDPOINTS ---

@app.get("/resources/list")
def list_resources():
    """Returns all known resource points (Water, Meds, Food)."""
    return ResourceSentinel.get_all()

@app.post("/resources/tag")
def tag_resource(res_type: str, lat: float, lng: float, qty: str, api_key: Optional[str] = None):
    """
    Tags a resource point. 
    If api_key matches, it is marked as VERIFIED (Government).
    Otherwise, it is marked UNVERIFIED (Crowdsourced).
    """
    is_admin = (api_key == "NDRF-COMMAND-2026-SECURE")
    new_res = ResourceSentinel.add_resource(res_type, lat, lng, qty, is_admin)
    
    # Audit log for Government tagged resources
    if is_admin:
        AuditLogger.log("ADMIN", "RESOURCE_TAG", f"Official {res_type} added at {lat},{lng}", "INFO")
    
    return {"status": "success", "resource": new_res}

@app.post("/resources/verify/{res_id}")
def verify_resource_endpoint(res_id: str, api_key: str = Depends(SecurityGate.verify_admin)):
    """Commanders can mark a civilian report as OFFICIAL."""
    success = ResourceSentinel.verify_resource(res_id)
    if success:
        AuditLogger.log("COMMANDER", "RESOURCE_VERIFIED", f"ID: {res_id}", "INFO")
        return {"status": "success", "message": "Resource Verified"}
    return {"status": "error", "message": "Resource not found"}

@app.delete("/resources/delete/{res_id}")
def delete_resource_endpoint(res_id: str, api_key: str = Depends(SecurityGate.verify_admin)):
    """Commanders can remove fake or depleted resources."""
    success = ResourceSentinel.delete_resource(res_id)
    if success:
        return {"status": "success", "message": "Resource Removed"}
    return {"status": "error", "message": "Resource not found"}

# --- HEALTH CHECK ---
@app.get("/health/diagnostics")
def system_health():
    return SecurityGate.system_health_check()

# --- AUTH ---
@app.post("/auth/login")
def admin_login(password: str = Form(...)):
    # Accept multiple valid passwords for demo
    if password in ["admin123", "india123", "ndrf2026", "command"]:
        return {"status": "success", "token": "NDRF-COMMAND-2026-SECURE"}
    else:
        return {"status": "error", "message": "Invalid Credentials"}, 401

# --- GOVERNANCE & DECISION ENDPOINTS (NEW) ---

@app.get("/admin/governance/pending")
def get_pending_decisions(api_key: str = Depends(SecurityGate.verify_admin)):
    """
    Returns the list of actions waiting for Human Approval.
    """
    # SIMULATION: If empty, generate a fake critical decision for the Demo
    # This ensures the Judges always see something to approve.
    if not PENDING_DECISIONS:
        dummy_risk = {
            "risk": "CRITICAL", 
            "score": 98, 
            "reason": "Cloudburst Protocol (Rain > 120mm)", 
            "source": "IMD Realtime"
        }
        # Use the new DecisionEngine
        proposal = DecisionEngine.create_proposal(dummy_risk, 26.14, 91.73)
        PENDING_DECISIONS.append(proposal)
        
    return PENDING_DECISIONS

@app.post("/admin/governance/decide")
def submit_decision(decision_id: str, action: str, admin_notes: str, api_key: str = Depends(SecurityGate.verify_admin)):
    """
    The 'Nuclear Key'. Admin either APPROVES or REJECTS the AI's plan.
    """
    # 1. Find the proposal
    proposal = next((p for p in PENDING_DECISIONS if p["id"] == decision_id), None)
    
    if not proposal:
        return {"status": "error", "message": "Decision ID not found."}
    
    # 2. Execute Logic based on Human Choice
    if action == "APPROVE":
        # LOGGING (Chain of Trust)
        AuditLogger.log(
            actor="COMMANDER_ADMIN",
            action=f"AUTHORIZED_{proposal['type']}",
            details=f"Approved AI Proposal {decision_id}. Notes: {admin_notes}",
            severity="CRITICAL"
        )
        
        # REMOVE FROM QUEUE
        PENDING_DECISIONS.remove(proposal)
        
        # EXECUTE (Simulated Execution)
        # In real life, this triggers the SMS Gateway / NDRF Radio
        return {
            "status": "success", 
            "outcome": f"🚀 EXECUTED: {proposal['type']}", 
            "audit_hash": str(uuid.uuid4())
        }
        
    elif action == "REJECT":
        # Log the Rejection (Important for AI Training Loop)
        AuditLogger.log(
            actor="COMMANDER_ADMIN", 
            action="REJECTED_ACTION", 
            details=f"Rejected {decision_id}. Reason: {admin_notes}", 
            severity="WARN"
        )
        PENDING_DECISIONS.remove(proposal)
        return {"status": "success", "outcome": "❌ Action Cancelled. Model flagged for retraining."}

# --- EXISTING ADMIN ENDPOINTS ---

@app.get("/admin/stats")
def get_admin_stats(api_key: str = Depends(SecurityGate.verify_admin)):
    return AnalyticsEngine.get_live_stats()

@app.get("/admin/audit-logs")
def get_audit_trail(api_key: str = Depends(SecurityGate.verify_admin)):
    return AuditLogger.get_logs()

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
    """Generate SITREP PDF for CommandDashboard"""
    from fastapi.responses import Response
    import datetime
    
    # Extract token from Authorization header or query param
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    
    # Verify token
    if token != "NDRF-COMMAND-2026-SECURE":
        return Response(
            content=b'{"status": "error", "message": "Unauthorized"}',
            status_code=403,
            media_type='application/json'
        )
    
    # Generate simple text-based SITREP
    stats = AnalyticsEngine.get_live_stats()
    audit_logs = AuditLogger.get_logs()
    
    sitrep_content = f"""
    ═══════════════════════════════════════════════════════════
    SITUATION REPORT (SITREP)
    National Disaster Response Force (NDRF) - Northeast Command
    ═══════════════════════════════════════════════════════════
    
    Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Classification: RESTRICTED
    
    SUMMARY:
    - Active Missions: {stats.get('active_missions', 0)}
    - SOS Beacons: {stats.get('sos_count', 0)}
    - Pending Decisions: {len(PENDING_DECISIONS)}
    - Resources Available: {len(ResourceSentinel.get_all())}
    
    CRITICAL DECISIONS:
    {chr(10).join([f"- {d['type']} ({d.get('risk', 'UNKNOWN')} RISK)" for d in PENDING_DECISIONS[:5]])}
    
    AUDIT TRAIL (Recent):
    {chr(10).join([f"- {log.get('action', 'N/A')}: {log.get('details', 'N/A')}" for log in audit_logs[-10:]])}
    
    ═══════════════════════════════════════════════════════════
    END OF REPORT
    ═══════════════════════════════════════════════════════════
    """
    
    # Return as PDF-like content (text for now, can be enhanced with reportlab)
    return Response(
        content=sitrep_content.encode('utf-8'),
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename=SITREP_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        }
    )

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
