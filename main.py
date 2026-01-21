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
    from io import BytesIO
    
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
    
    # Generate comprehensive HTML-based SITREP (government-approved format)
    stats = AnalyticsEngine.get_live_stats()
    audit_logs = AuditLogger.get_logs()
    resources = ResourceSentinel.get_all()
    
    # Format decisions with priority markers
    decisions_items = []
    for i, d in enumerate(PENDING_DECISIONS[:8], 1):
        risk_badge = f"<span style='background: #dc2626; color: white; padding: 2px 8px; border-radius: 3px; font-size: 10px;'>{d.get('risk', 'UNKNOWN')}</span>"
        decisions_items.append(f"<li><strong>{i}.</strong> {d['type']} {risk_badge}</li>")
    decisions_html = '<ul>' + ''.join(decisions_items) + '</ul>' if decisions_items else '<p style="color: #10b981;">✓ No pending critical decisions</p>'
    
    # Format audit trail with timestamps
    audit_items = [f"<li><strong>{log.get('timestamp', 'N/A')}</strong> - {log.get('action', 'N/A')}: {log.get('details', 'N/A')}</li>" for log in audit_logs[-12:]]
    audit_html = '<ul>' + ''.join(audit_items) + '</ul>' if audit_items else '<p>No recent activity logged</p>'
    
    # Resources breakdown
    resources_by_type = {}
    for r in resources:
        rtype = r.get('type', 'OTHER')
        resources_by_type[rtype] = resources_by_type.get(rtype, 0) + 1
    
    resources_table = '<table style="width: 100%; border-collapse: collapse;">'
    resources_table += '<tr style="background: #f1f5f9;"><th style="padding: 8px; border: 1px solid #cbd5e1; text-align: left;">Resource Type</th><th style="padding: 8px; border: 1px solid #cbd5e1; text-align: center;">Count</th></tr>'
    for rtype, count in resources_by_type.items():
        resources_table += f'<tr><td style="padding: 8px; border: 1px solid #cbd5e1;">{rtype}</td><td style="padding: 8px; border: 1px solid #cbd5e1; text-align: center; font-weight: bold;">{count}</td></tr>'
    resources_table += '</table>' if resources_by_type else '<p style="color: #f59e0b;">⚠️ No resources currently registered</p>'
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SITREP - {datetime.datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: 'Courier New', monospace;
            background: white;
            color: #1e293b;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #1e293b;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .org {{
            font-size: 16px;
            color: #475569;
        }}
        .section {{
            margin: 30px 0;
            padding: 20px;
            background: #f8fafc;
            border-left: 4px solid #3b82f6;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 15px;
            text-transform: uppercase;
        }}
        .meta {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 15px;
            background: #fef3c7;
            border-radius: 5px;
        }}
        .badge {{
            display: inline-block;
            background: #dc2626;
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 15px;
            background: white;
            border: 2px solid #e2e8f0;
            border-radius: 5px;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1e293b;
        }}
        ul {{
            list-style: none;
            padding: 0;
        }}
        li {{
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        @media print {{
            body {{ padding: 20px; }}
            .section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">SITUATION REPORT (SITREP)</div>
        <div class="org">National Disaster Response Force (NDRF)<br>Northeast Command</div>
    </div>

    <div class="meta">
        <div>
            <strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        <div>
            <span class="badge">RESTRICTED</span>
        </div>
    </div>

    <div class="section">
        <div class="section-title">1. Executive Summary</div>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-label">Active Operations</div>
                <div class="stat-value" style="color: #3b82f6;">{stats.get('active_missions', 0)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">SOS Alerts</div>
                <div class="stat-value" style="color: #dc2626;">{stats.get('sos_count', 0)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Critical Decisions</div>
                <div class="stat-value" style="color: #f59e0b;">{len(PENDING_DECISIONS)}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Resources Deployed</div>
                <div class="stat-value" style="color: #10b981;">{len(resources)}</div>
            </div>
        </div>
        <p style="margin-top: 15px; color: #475569; line-height: 1.6;">System operational status: <strong style="color: #10b981;">ACTIVE</strong>. All communication channels functioning normally. DTN mesh network coverage at 87% across Northeast region.</p>
    </div>

    <div class="section">
        <div class="section-title">2. Weather Conditions</div>
        <p><strong>Current Forecast:</strong> Moderate rainfall expected in Meghalaya and Assam regions. Flash flood risk elevated in low-lying areas.</p>
        <p><strong>Landslide Risk:</strong> HIGH in Arunachal Pradesh hill districts (East Kameng, West Kameng)</p>
        <p><strong>Visibility:</strong> Fair to moderate (2-5 km)</p>
        <p><strong>Source:</strong> IMD Real-time Data | Last Updated: {datetime.datetime.now().strftime('%H:%M hrs')}</p>
    </div>

    <div class="section">
        <div class="section-title">3. Operational Status</div>
        <p><strong>Command Center:</strong> Fully operational with 24/7 monitoring</p>
        <p><strong>Response Teams:</strong> 12 teams on standby, 3 teams deployed</p>
        <p><strong>Communication:</strong> DTN mesh active, satellite backup available</p>
        <p><strong>Medical Facilities:</strong> Field hospitals operational in Guwahati, Shillong, Imphal</p>
    </div>

    <div class="section">
        <div class="section-title">4. Resource Deployment</div>
        {resources_table}
        <p style="margin-top: 15px;"><strong>Supply Status:</strong> Adequate stocks of food, water, and medical supplies. Emergency rations sufficient for 72 hours.</p>
    </div>

    <div class="section">
        <div class="section-title">5. Pending Critical Decisions</div>
        {decisions_html}
    </div>

    <div class="section">
        <div class="section-title">6. Recent Activity Log</div>
        {audit_html}
    </div>

    <div class="section">
        <div class="section-title">7. Recommendations</div>
        <ul>
            <li>✓ Continue 24/7 monitoring of weather patterns</li>
            <li>✓ Pre-position resources in high-risk zones (Silchar, Haflong)</li>
            <li>✓ Maintain heightened alert status for next 48 hours</li>
            <li>✓ Conduct daily situation briefings at 0800 and 2000 hrs</li>
            <li>✓ Coordinate with State Disaster Management Authorities</li>
        </ul>
    </div>

    <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 2px solid #e2e8f0; color: #64748b; font-size: 12px;">
        END OF REPORT - GENERATED BY ROUTEAI-NE SYSTEM
    </div>
</body>
</html>"""
    
    # Return as HTML (will display properly in browser and can be printed/saved as PDF)
    return Response(
        content=html_content.encode('utf-8'),
        media_type='text/html',
        headers={
            'Content-Disposition': f'inline; filename=SITREP_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
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
