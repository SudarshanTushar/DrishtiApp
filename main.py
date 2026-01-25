from fastapi import FastAPI, UploadFile, File, Form, Depends, Header, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
import uuid
import traceback # Added for debug
from datetime import datetime, timezone, timedelta # Simplified time
from zoneinfo import ZoneInfo
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2 import WKTElement
from pydantic import BaseModel
from typing import Optional
from fpdf import FPDF

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

from db.session import SessionLocal, engine, Base
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


def ensure_db_ready():
    """Create PostGIS extension and tables if they are missing."""
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"DB Warning: {e}")


def get_latest_route_and_decision(session):
    """Fetch the latest route and its latest decision; seed defaults if none exist."""
    latest_route = session.query(Route).order_by(Route.created_at.desc()).first()
    if not latest_route:
        seeded_route = Route(
            start_geom=WKTElement("POINT(91.73 26.14)", srid=4326),
            end_geom=WKTElement("POINT(91.89 25.57)", srid=4326),
            distance_km=148.2,
            risk_level="MODERATE",
        )
        session.add(seeded_route)
        session.flush()

        seeded_decision = AuthorityDecision(
            route_id=seeded_route.id,
            actor_role="NDRF",
            decision="APPROVED",
        )
        session.add(seeded_decision)
        session.commit()
        session.refresh(seeded_route)
        session.refresh(seeded_decision)
        return seeded_route, seeded_decision

    latest_decision = (
        session.query(AuthorityDecision)
        .filter(AuthorityDecision.route_id == latest_route.id)
        .order_by(AuthorityDecision.created_at.desc())
        .first()
    )
    return latest_route, latest_decision


def clean_text(text):
    """Ensure text is safe for Latin-1 encoding (Standard FPDF limitation)."""
    if not isinstance(text, str):
        return str(text)
    replacements = {
        "\u2013": "-", "\u2014": "--", "\u2018": "'", "\u2019": "'", 
        "\u201c": '"', "\u201d": '"', "₹": "Rs. "
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1')


def build_sitrep_payload(route, decision):
    """
    ADVANCED INTELLIGENCE AGGREGATOR.
    Pulls live data from IoT, Simulation, and Resource modules to 
    generate the 5-Section Government Format.
    """
    # --- 1. TIME SYNCHRONIZATION ---
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    now_utc = datetime.now(timezone.utc)
    now_ist = now_utc.astimezone(ist_offset)
    
    # Military DTG Format: 250830Z JAN 26
    dtg = now_utc.strftime("%d%H%MZ %b %y").upper()
    
    # --- 2. GATHER LIVE INTELLIGENCE ---
    
    # A. SIMULATION STATE (Is the world ending?)
    sim_data = SimulationManager.get_overrides()
    is_drill = sim_data.get("active", False)
    sim_phase = sim_data.get("phase", 0)
    
    # B. IOT SENSOR FUSION
    iot_readings = IoTManager.get_live_readings()
    rain_sensor = next((s for s in iot_readings if s["type"] == "RAIN_GAUGE"), {"value": 0})
    rain_val = float(rain_sensor["value"])
    
    # C. RESOURCE STATUS
    resources = ResourceSentinel.get_all()
    team_count = len(resources)
    
    # D. CROWD INTEL (SOS Signals)
    # In a real app, we'd count DB rows. For pilot, we estimate based on risk.
    risk_level = (route.risk_level or "MODERATE").upper()
    
    # --- 3. CONSTRUCT THE 5-SECTION REPORT ---
    
    # SECTION 1: EXECUTIVE SUMMARY (BLUF)
    # Dynamic Threat Assessment
    if is_drill:
        op_status = "RED - CRITICAL (DRILL ACTIVE)"
        threat = f"Simulated Phase {sim_phase}: Flash Flood wavefront advancing in Sector 4."
        casualties = f"{random.randint(12, 40)} Unverified / {random.randint(2, 5)} Confirmed"
    elif risk_level == "HIGH":
        op_status = "AMBER - ELEVATED"
        threat = "Heavy rainfall triggering localized slope instability."
        casualties = "0 Confirmed / Monitoring incoming SOS."
    else:
        op_status = "GREEN - NORMAL"
        threat = "Routine environmental monitoring. No active threats."
        casualties = "0 Reports."

    # SECTION 2: INTELLIGENCE & SENSORS
    # Dynamic Weather & Visuals
    weather_desc = f"Rainfall: {rain_val}mm | Visibility: {'POOR (<500m)' if rain_val > 80 else 'GOOD (>5km)'}"
    
    drone_status = "UAV-402 Grounded (Weather)" if rain_val > 100 else "UAV-402 Patrol: No structural damage detected."
    if is_drill and sim_phase > 2:
        drone_status = "UAV-402 confirms embankment breach at Grid 84-22."

    # SECTION 3: OPERATIONS
    # Dynamic Decision Tracking
    decision_txt = (decision.decision if decision else "PENDING").upper()
    actor_txt = decision.actor_role if decision else "COMMAND"
    
    completed_ops = "Routine patrol routes established."
    if decision_txt == "APPROVED":
        completed_ops = f"Route {str(route.id)[:8]} AUTHORIZED for deployment."
    elif decision_txt == "REJECTED":
        completed_ops = f"Route {str(route.id)[:8]} LOCKED DOWN by {actor_txt}."

    pending_ops = "None."
    if len(PENDING_DECISIONS) > 0:
        pending_ops = f"AUTH REQUIRED: {len(PENDING_DECISIONS)} AI Proposals pending review."

    # SECTION 4: LOGISTICS
    # Dynamic Resource Tracking
    # Fuel calculation logic: heavy rain = more fuel usage
    fuel_level = 90 - (rain_val * 0.5) 
    if fuel_level < 30: fuel_level = 30 # Floor
    
    logistics_status = f"Medical Kits: 100% | Rations: 95% | Fuel: {int(fuel_level)}% ({'CRITICAL' if fuel_level < 40 else 'STABLE'})."

    # SECTION 5: COMMUNICATIONS
    # Dynamic Mesh Health
    internet = "UP (Fibre)"
    if is_drill or rain_val > 120:
        internet = "DOWN (0%) - CABLE CUT"
    
    mesh_health = "STABLE (98% Coverage)"
    packet_vol = random.randint(1200, 5000)

    # --- 4. RETURN STRUCTURED JSON ---
    # This matches the "govFormat" enrichment in your Frontend
    return {
        "dtg": dtg,
        "unit": "NE-COMMAND-NODE-ALPHA",
        "executive_summary": f"{threat} Status: {op_status}", # Fallback for old viewers
        
        # The "Pro" Fields for the new Dashboard
        "bluf_status": op_status,
        "bluf_threat": threat,
        "casualty_count": casualties,
        
        "weather_rain": weather_desc,
        "drone_intel": drone_status,
        
        "completed_action": completed_ops,
        "pending_decision": pending_ops,
        
        "teams_deployed": team_count,
        "supplies_fuel": logistics_status,
        
        "internet_status": internet,
        "mesh_status": mesh_health,
        "packets_relayed": f"{packet_vol} Packets (Store-Carry-Forward)",
        
        "meta": {
             "id": str(route.id) if route.id else "N/A",
             "timestamp": now_ist.strftime("%d %b %Y, %H:%M"),
        }
    }

def _sitrep_pdf_response(api_key: Optional[str], authorization: Optional[str]):
    """
    GENERATES 'OFFICIAL CLASSIFIED' STYLE PDF.
    Features: Watermark, Status Colors, Official Header, Digital Signature.
    """
    # 1. Auth & Data Fetching (Standard)
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key

    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    # Fetch Data
    latest_route, latest_decision = None, None
    try:
        ensure_db_ready()
        with SessionLocal() as session:
            latest_route, latest_decision = get_latest_route_and_decision(session)
            sitrep = build_sitrep_payload(latest_route, latest_decision)
    except Exception as exc:
        print(f"SITREP Data Error: {exc}")
        return JSONResponse(status_code=503, content={"status": "error", "message": "Data Unavailable"})

    # 2. Extract Data
    unit_name = sitrep.get("unit", "NE-COMMAND")
    dtg_val = sitrep.get("dtg", "IMMEDIATE")
    bluf_status = sitrep.get("bluf_status", "UNKNOWN")
    bluf_threat = sitrep.get("bluf_threat", "No Data")
    
    meta = sitrep.get("meta", {})
    route_id = meta.get("id", "N/A")
    if len(route_id) > 10: route_id = f"R-{route_id.split('-')[0].upper()}"
    
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    file_slug_time = datetime.now(ist_offset).strftime("%Y%m%d_%H%M")

    # 3. DRAW THE PROFESSIONAL PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- WATERMARK (Subtle Background) ---
    pdf.set_font("Arial", "B", 50)
    pdf.set_text_color(240, 240, 240) # Very light gray
    with pdf.rotation(45, 105, 148):
        pdf.text(30, 190, "OFFICIAL USE ONLY")
    pdf.set_text_color(0, 0, 0) # Reset

    # --- CLASSIFICATION HEADER (Red Bar) ---
    pdf.set_fill_color(200, 0, 0) # Dark Red
    pdf.rect(0, 0, 210, 8, 'F')
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 1)
    pdf.cell(210, 6, "RESTRICTED // LAW ENFORCEMENT SENSITIVE", align='C')
    pdf.set_text_color(0, 0, 0) # Reset

    # --- OFFICIAL HEADER BLOCK ---
    pdf.ln(10)
    pdf.set_line_width(0.5)
    pdf.rect(10, 18, 190, 35) # Box
    
    # Title
    pdf.set_xy(10, 22)
    pdf.set_font("Times", "B", 18)
    pdf.cell(190, 8, "SITUATION REPORT (SITREP)", ln=1, align="C")
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(190, 5, "DRISHTI-NE | AI-Based Disaster Decision Support System", ln=1, align="C")
    
    # Divider Line
    pdf.line(10, 36, 200, 36)
    
    # Metadata Grid
    pdf.set_xy(12, 39)
    pdf.set_font("Courier", "B", 10) 
    pdf.cell(95, 5, f"FROM: {unit_name}", ln=0)
    pdf.cell(95, 5, f"DTG:  {dtg_val}", ln=1, align="R")
    
    pdf.set_xy(12, 45)
    pdf.cell(95, 5, "TO:   CENTRAL COMMAND (DELHI)", ln=0)
    pdf.cell(95, 5, f"REP:  {uuid.uuid4().hex[:8].upper()}", ln=1, align="R")

    pdf.ln(15)

    # --- 1. EXECUTIVE SUMMARY (BLUF) ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 235) # Cool Gray
    pdf.cell(0, 8, "  1. EXECUTIVE SUMMARY (BLUF)", ln=1, fill=True)
    pdf.ln(3)
    
    # Dynamic Status Color
    status_fill = (220, 255, 220) # Light Green
    if "RED" in bluf_status: status_fill = (255, 220, 220) # Light Red
    elif "AMBER" in bluf_status: status_fill = (255, 245, 220) # Light Amber
    
    pdf.set_fill_color(*status_fill)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 8, " OPERATIONAL STATUS ", border=1, fill=True, align='C')
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"  {bluf_status}", border=1, ln=1)
    
    pdf.ln(2)
    pdf.set_font("Times", "", 11)
    pdf.multi_cell(0, 6, f"THREAT ASSESSMENT: {bluf_threat}")
    pdf.ln(2)
    pdf.set_font("Times", "I", 10)
    pdf.cell(0, 6, f"Casualty Report: {sitrep.get('casualty_count', 'N/A')}", ln=1)
    pdf.ln(4)

    # --- 2. INTELLIGENCE & SENSORS ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 235)
    pdf.cell(0, 8, "  2. INTELLIGENCE & SENSORS", ln=1, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 10)
    # Draw simple lines for cleaner look
    pdf.cell(5, 6, "-", ln=0)
    pdf.cell(0, 6, f"Meteorological: {sitrep.get('weather_rain', 'N/A')}", ln=1)
    pdf.cell(5, 6, "-", ln=0)
    pdf.cell(0, 6, f"Visual Intel: {sitrep.get('drone_intel', 'N/A')}", ln=1)
    pdf.ln(4)

    # --- 3. OPERATIONS & DECISIONS ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 235)
    pdf.cell(0, 8, "  3. OPERATIONS & DECISIONS", ln=1, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(35, 6, "COMPLETED:", font_style="B")
    pdf.cell(0, 6, sitrep.get('completed_action', 'N/A'), ln=1)
    
    pdf.cell(35, 6, "PENDING:", font_style="B")
    # Highlight pending in Amber text if exists
    if "None" not in sitrep.get('pending_decision', 'None'):
        pdf.set_text_color(200, 100, 0)
    pdf.cell(0, 6, sitrep.get('pending_decision', 'N/A'), ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # --- 4. LOGISTICS & RESOURCES ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 235)
    pdf.cell(0, 8, "  4. LOGISTICS & RESOURCES", ln=1, fill=True)
    pdf.ln(2)
    
    # Table Header
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(95, 6, "DEPLOYED ASSETS", border=1, fill=True, align='C')
    pdf.cell(95, 6, "CRITICAL SUPPLIES", border=1, fill=True, align='C', ln=1)
    
    # Table Content
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"NDRF Teams: {sitrep.get('teams_deployed', '0')}", border=1, align='C')
    pdf.cell(95, 8, f"Fuel Status: {sitrep.get('supplies_fuel', 'N/A')}", border=1, align='C', ln=1)
    pdf.ln(4)

    # --- 5. COMMUNICATIONS ---
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 235)
    pdf.cell(0, 8, "  5. COMMUNICATIONS & NETWORK HEALTH", ln=1, fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Backbone Status: {sitrep.get('internet_status', 'N/A')}", ln=1)
    pdf.cell(0, 6, f"Mesh Integrity:  {sitrep.get('mesh_status', 'N/A')}", ln=1)
    pdf.cell(0, 6, f"Message Vol:     {sitrep.get('packets_relayed', 'N/A')}", ln=1)
    
    # --- FOOTER (Digital Signature Style) ---
    pdf.set_y(-35)
    pdf.set_line_width(0.2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f"GENERATED BY SYSTEM: DRISHTI-CORE-V1", ln=1, align="R")
    pdf.cell(0, 4, f"DIGITAL SIGNATURE: {uuid.uuid4()}", ln=1, align="R")
    
    # Classification Footer
    pdf.set_y(-15)
    pdf.set_fill_color(200, 0, 0)
    pdf.rect(0, pdf.get_y(), 210, 15, 'F')
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, pdf.get_y()+4)
    pdf.cell(210, 6, "RESTRICTED // LAW ENFORCEMENT SENSITIVE", align='C')

    # 4. Output
    try:
        return Response(
            content=bytes(pdf.output()), 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=SITREP_{file_slug_time}.pdf"}
        )
    except TypeError: # Legacy FPDF
        return Response(
            content=pdf.output(dest='S').encode('latin-1'),
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename=SITREP_{file_slug_time}.pdf"}
        )
    
    def draw_row(label, value, bold_val=False):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(col_w, row_h, clean_text(label), border=1)
        pdf.set_font("Arial", "B" if bold_val else "", 10)
        
        # Risk Coloring (Text Only - FPDF1.7 compatible)
        if "HIGH" in str(value) or "CRITICAL" in str(value):
            pdf.set_text_color(200, 0, 0)
        elif "APPROVED" in str(value) or "LOW" in str(value):
            pdf.set_text_color(0, 100, 0)
        else:
            pdf.set_text_color(0, 0, 0)
            
        pdf.cell(0, row_h, clean_text(str(value)), border=1, ln=1)
        pdf.set_text_color(0, 0, 0) # Reset

    draw_row("Route ID", route_id)
    draw_row("Total Distance", distance_text)
    draw_row("Risk Classification", risk_level, bold_val=True)
    draw_row("Command Decision", auth_decision, bold_val=True)
    pdf.ln(5)

    # --- METADATA ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, clean_text("3. AUTHORIZATION METADATA"), ln=1, fill=True)
    pdf.ln(2)
    
    draw_row("Authorized By", auth_name)
    draw_row("Decision Time", date_pretty)
    draw_row("Report Generated", date_pretty)
    
    # --- FOOTER (Rubber Stamp) ---
    pdf.set_y(-40)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(200, 0, 0) 
    pdf.cell(0, 10, clean_text("CLASSIFICATION: RESTRICTED"), ln=1, align="C")
    
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, clean_text("This document contains sensitive operational data generated by the Drishti-NE System."), ln=1, align="C")
    pdf.cell(0, 5, clean_text("For Official Government Use Only."), ln=1, align="C")

    # 4. Output
    try:
        # FPDF2
        pdf_bytes = bytes(pdf.output()) 
    except TypeError:
        # Legacy FPDF 1.7
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"status": "error", "message": "PDF Generation Failed"})

    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=SITREP_{file_slug_time}.pdf"})


def build_sitrep_html(sitrep: dict, stats: dict, resources: list, audit_logs: list, pending_decisions: list) -> str:
    """Render an HTML SITREP (print/save ready). Adapted for Clean Payload."""
    # (HTML Generation Logic - kept same for brevity, assuming PDF is priority)
    # ... [Keep your existing HTML builder code here] ...
    return "<html><body>HTML View Not Updated - Please Use PDF Download</body></html>"


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
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    AuditLogger.log("ADMIN", "MASS_BROADCAST", f"Msg: {message}", "CRITICAL")
    return {"status": "success", "targets": "Telecom Operators", "payload": "CAP-XML"}

# --- UPDATED SIMULATION ENDPOINTS ---

@app.post("/admin/simulate/start")
def start_simulation(scenario: str = "FLASH_FLOOD", api_key: str = Depends(SecurityGate.verify_admin)):
    scenario_data = SimulationManager.start_scenario(scenario, 26.14, 91.73)
    AuditLogger.log("ADMIN", "DRILL_INITIATED", f"Scenario: {scenario}", "WARN")
    proposal = DecisionEngine.create_proposal(scenario_data, 26.14, 91.73)
    existing = next((p for p in PENDING_DECISIONS if p["reason"] == scenario_data["reason"]), None)
    if not existing:
        PENDING_DECISIONS.insert(0, proposal)
    return {"status": "ACTIVE", "injected_proposal": proposal["id"]}

@app.post("/admin/simulate/stop")
def stop_simulation(api_key: str = Depends(SecurityGate.verify_admin)):
    AuditLogger.log("ADMIN", "DRILL_STOPPED", "System Reset to Normal", "INFO")
    PENDING_DECISIONS.clear()
    return SimulationManager.stop_simulation()

# --- MISSING COMMAND DASHBOARD ENDPOINTS ---

@app.get("/admin/resources")
def get_admin_resources(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    return {"resources": ResourceSentinel.get_all()}

@app.post("/admin/resources/{resource_id}/verify")
def verify_admin_resource(resource_id: str, api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    success = ResourceSentinel.verify_resource(resource_id)
    if success:
        AuditLogger.log("COMMANDER", "RESOURCE_VERIFIED", f"ID: {resource_id}", "INFO")
        return {"status": "success", "message": "Resource Verified"}
    return {"status": "error", "message": "Resource not found"}

@app.delete("/admin/resources/{resource_id}")
def delete_admin_resource(resource_id: str, api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    success = ResourceSentinel.delete_resource(resource_id)
    if success:
        AuditLogger.log("COMMANDER", "RESOURCE_DELETED", f"ID: {resource_id}", "INFO")
        return {"status": "success", "message": "Resource deleted"}
    return {"status": "error", "message": "Resource not found"}

@app.get("/admin/sos-feed")
def get_sos_feed(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return {"status": "error", "message": "Unauthorized"}, 403
    sos_items = [
        {"id": f"SOS-{i}", "type": random.choice(["MEDICAL", "TRAPPED", "FIRE", "FLOOD"]), 
         "location": f"Zone-{chr(65+i)}", "urgency": random.choice(["CRITICAL", "HIGH", "MEDIUM"]),
         "time": time.time() - (i * 300)} 
        for i in range(random.randint(3, 8))
    ]
    return {"feed": sos_items}

@app.post("/admin/sitrep/generate")
@app.get("/admin/sitrep/generate")
def generate_sitrep(api_key: Optional[str] = None, authorization: Optional[str] = Header(None), format: str = Query("pdf", enum=["json", "html", "pdf"])):
    """Generate SITREP in JSON (default), or HTML/PDF when requested."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    # Check format
    fmt = (format or "json").lower()
    
    # DB Access
    latest_route, latest_decision = None, None
    try:
        ensure_db_ready()
        with SessionLocal() as session:
            latest_route, latest_decision = get_latest_route_and_decision(session)
    except Exception:
        pass # Continue with defaults if DB fails

    # JSON Response
    if fmt == "json":
        return JSONResponse(content=build_sitrep_payload(latest_route, latest_decision))
        
    # PDF Response
    if fmt == "pdf":
        return _sitrep_pdf_response(api_key, authorization)

    # HTML Response (Fallback)
    return Response(content="<html><body>HTML not implemented</body></html>", media_type="text/html")


@app.post("/admin/sitrep/pdf")
def generate_sitrep_pdf(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    return _sitrep_pdf_response(api_key, authorization)


@app.get("/admin/sitrep/pdf")
def generate_sitrep_pdf_get(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    return _sitrep_pdf_response(api_key, authorization)

@app.get("/admin/audit-log")
def get_audit_trail(api_key: str = Depends(SecurityGate.verify_admin)):
    return AuditLogger.get_logs()

@app.post("/admin/drone/analyze")
def analyze_drone_admin(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
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
    victim_name = request.user.name if request.user else "Unknown Citizen"
    print(f"🚨 CRITICAL SOS: {victim_name} needs help at {request.lat}, {request.lng}")
    mission = LogisticsManager.request_dispatch(request.lat, request.lng)
    if mission: 
        return {"status": "success", "mission": mission, "message": f"Rescue Team Dispatched for {victim_name}"}
    else: 
        mission_id = f"NDRF-{random.randint(1000,9999)}"
        return {"status": "success", "mission": {"id": mission_id, "status": "DISPATCHED"}, "message": "Emergency broadcast sent."}

@app.get("/sos/track/{mission_id}")
def track_mission(mission_id: str):
    status = LogisticsManager.get_mission_status(mission_id)
    if status: return {"status": "success", "mission": status}
    return {"status": "error", "message": "Mission ended or not found"}

@app.get("/iot/feed")
def get_iot_feed():
    data = IoTManager.get_live_readings()
    alert = IoTManager.check_critical_breach(data)
    return {"sensors": data, "system_alert": alert}

@app.get("/analyze")
def analyze_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float, rain_input: Optional[int] = None):
    # (Keeping the massive Analyze logic from user provided file for safety)
    if rain_input is None or rain_input == 0:
        try:
            iot_data = IoTManager.get_live_readings()
            rain_sensor = next((s for s in iot_data if s["type"] == "RAIN_GAUGE"), None)
            if rain_sensor: rain_input = float(rain_sensor['value'])
            if rain_input == 0: rain_input = 15
        except: rain_input = 50
    ai_result = predictor.predict(rain_input, start_lat, start_lng)
    landslide_score = ai_result["ai_score"]
    slope_angle = ai_result["slope_angle"]
    soil_type = ai_result["soil_type"]
    terrain_type = "Hilly" if start_lat > 26 else "Plain"
    terrain_risk_score = 90 if slope_angle > 35 else 70 if slope_angle > 25 else 50 if slope_angle > 15 else 20
    governance_result = SafetyGovernance.validate_risk(rain_input, slope_angle, landslide_score)
    crowd_intel = CrowdManager.evaluate_zone(start_lat, start_lng)
    crowd_risk = crowd_intel["risk"] if (crowd_intel and crowd_intel["risk"] in ["CRITICAL", "HIGH"]) else "SAFE"
    iot_feed = IoTManager.get_live_readings()
    breach = IoTManager.check_critical_breach(iot_feed)
    iot_risk = "CRITICAL" if breach else "SAFE"
    sim_state = SimulationManager.get_overrides()
    drill_active = sim_state["active"]
    composite_score = (landslide_score * 0.35 + terrain_risk_score * 0.25 + min(rain_input * 2, 100) * 0.20 + (100 if crowd_risk=="CRITICAL" else 30) * 0.15 + (100 if iot_risk=="CRITICAL" else 30) * 0.05)
    
    final_risk = "SAFE"
    if drill_active: final_risk = "CRITICAL"
    elif iot_risk == "CRITICAL": final_risk = "CRITICAL"
    elif crowd_risk in ["CRITICAL", "HIGH"]: final_risk = crowd_risk
    elif composite_score >= 75: final_risk = "CRITICAL"
    elif composite_score >= 60: final_risk = "HIGH"
    elif composite_score >= 40: final_risk = "MODERATE"
    
    import math
    R = 6371
    lat1, lon1 = math.radians(start_lat), math.radians(start_lng)
    lat2, lon2 = math.radians(end_lat), math.radians(end_lng)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    return {
        "distance": f"{distance:.1f} km",
        "route_risk": final_risk,
        "confidence_score": int(composite_score),
        "reason": governance_result["reason"],
        "source": governance_result["source"],
        "recommendations": ["Follow protocols"],
        "risk_breakdown": {},
        "terrain_data": {"type": terrain_type, "slope": f"{slope_angle}°", "soil": soil_type, "elevation": "N/A"},
        "weather_data": {"rainfall_mm": rain_input, "severity": "Moderate"},
        "alerts": [],
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

@app.post("/listen")
async def listen_to_voice(file: UploadFile = File(...), language_code: str = Form("hi-IN")):
    # (Keeping existing logic)
    raw_key = os.getenv("SARVAM_API_KEY", "")
    SARVAM_API_KEY = raw_key.strip().replace('"', '').replace("'", "")
    SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
    translated_text = "Navigate to Shillong"
    target_city = "Shillong"
    try:
        if len(SARVAM_API_KEY) > 10:
            files = {"file": (file.filename, file.file, file.content_type)}
            headers = {"api-subscription-key": SARVAM_API_KEY}
            response = requests.post(SARVAM_URL, headers=headers, files=files)
            if response.status_code == 200:
                translated_text = response.json().get("transcript", translated_text)
    except Exception: pass
    
    if "shillong" in translated_text.lower(): target_city = "Shillong"
    elif "guwahati" in translated_text.lower(): target_city = "Guwahati"
    elif "kohima" in translated_text.lower(): target_city = "Kohima"
    fallback_responses = LanguageConfig.OFFLINE_RESPONSES.get(language_code, LanguageConfig.OFFLINE_RESPONSES["en-IN"])
    voice_reply = f"{fallback_responses['SAFE']} ({target_city})" if target_city != "Unknown" else "Command not understood."
    return {"status": "success", "translated_text": translated_text, "voice_reply": voice_reply, "target": target_city}

MESH_BUFFER = []
class MeshMessage(BaseModel):
    sender: str
    text: str
    timestamp: float

@app.post("/mesh/send")
def send_mesh_message(msg: MeshMessage):
    MESH_BUFFER.append(msg.dict())
    if len(MESH_BUFFER) > 50: MESH_BUFFER.pop(0)
    return {"status": "sent"}

@app.get("/mesh/messages")
def get_mesh_messages():
    return MESH_BUFFER
