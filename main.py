import os
import time
import random
import uuid
import re
import traceback
from datetime import datetime, timezone, timedelta
from typing import Optional, List

# FASTAPI
from fastapi import FastAPI, UploadFile, File, Form, Depends, Header, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# PDF GENERATION
from fpdf import FPDF

# DB & ORM
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2 import WKTElement
from db.session import SessionLocal, engine, Base
from db.models import Route, AuthorityDecision

# --- CONFIGURATION ---
# SET THIS TO FALSE LATER TO USE REAL DATABASE
DEMO_MODE = True 

# MODULES (Mocked if missing to prevent crashes)
try:
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
except ImportError:
    # Dummy mocks for stability
    class ResourceSentinel: get_all = staticmethod(lambda: [])
    class AnalyticsEngine: get_live_stats = staticmethod(lambda: {"active_missions": 3, "sos_count": 12})
    class AuditLogger: 
        log = staticmethod(lambda a,b,c,d: print(f"LOG: {a} {b}"))
        get_logs = staticmethod(lambda: [])
    class SecurityGate: verify_admin = staticmethod(lambda: "MOCK_TOKEN")
    class SimulationManager:
        start_scenario = staticmethod(lambda s,x,y: {})
        stop_simulation = staticmethod(lambda: {})
        get_overrides = staticmethod(lambda: {"active": False})
    class DecisionEngine: create_proposal = staticmethod(lambda d,x,y: {"id":"1", "type":"EVAC", "risk":"HIGH"})
    class CrowdManager: 
        admin_override = staticmethod(lambda x,y,z: None)
        submit_report = staticmethod(lambda x,y,z: "OK")
        evaluate_zone = staticmethod(lambda x,y: {"risk":"LOW"})
    class VisionEngine: analyze_damage = staticmethod(lambda x: {"classification":[], "damage_score":0})
    class IoTManager: 
        get_live_readings = staticmethod(lambda: [])
        check_critical_breach = staticmethod(lambda x: None)
    class LogisticsManager:
        request_dispatch = staticmethod(lambda x,y: {"id":"1"})
        get_mission_status = staticmethod(lambda x: {})
    class LandslidePredictor: predict = staticmethod(lambda x,y,z: {"ai_score": 45, "slope_angle": 20, "soil_type": "Clay"})
    class LanguageConfig: 
        get_config = staticmethod(lambda: {})
        OFFLINE_RESPONSES = {"en-IN": {"SAFE": "Route is Safe"}}

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

# --- 1. ROBUST DB SETUP ---
def ensure_db_ready():
    if DEMO_MODE: return # Skip DB setup in demo mode
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"DB Warning: {e}")

# --- 2. FAIL-SAFE DATA FETCHING ---
def get_latest_route_and_decision(session):
    if DEMO_MODE: return None, None # Force defaults
    try:
        latest_route = session.query(Route).order_by(Route.created_at.desc()).first()
        latest_decision = None
        if latest_route:
            latest_decision = (
                session.query(AuthorityDecision)
                .filter(AuthorityDecision.route_id == latest_route.id)
                .order_by(AuthorityDecision.created_at.desc())
                .first()
            )
        return latest_route, latest_decision
    except Exception:
        return None, None

# --- 3. HELPER: TEXT SANITIZER ---
def clean_text(text):
    """Ensure text is safe for Latin-1 encoding."""
    if not isinstance(text, str): return str(text)
    replacements = {"\u2013": "-", "\u2014": "--", "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "₹": "Rs. "}
    for char, replacement in replacements.items(): text = text.replace(char, replacement)
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- 4. THE "GOVERNMENT FORM" PDF ENGINE ---
def generate_professional_pdf(route, decision):
    """
    Generates the Clean 'Government Boxed' Layout.
    GUARANTEES NO 'n/a' VALUES by forcing defaults.
    """
    print(">>> RENDERING PDF (GOVERNMENT LAYOUT)...") # Debug Log

    # === A. DATA SANITIZATION ===
    # Use DB data if available, otherwise FORCE Clean Pilot Data
    route_id = str(route.id) if (route and route.id) else "ROUTE-ALPHA-01"
    if len(route_id) > 10 and "-" in route_id: route_id = f"R-{route_id.split('-')[0].upper()}"
    
    distance = f"{route.distance_km:.1f} km" if (route and route.distance_km) else "148.2 km"
    risk = (route.risk_level if (route and route.risk_level) else "MODERATE").upper()
    
    auth_role = (decision.actor_role if (decision and decision.actor_role) else "NDRF COMMANDER").upper()
    status = (decision.decision if (decision and decision.decision) else "APPROVED").upper()
    
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist_offset)
    dtg = now.strftime("%d%H%MZ %b %y").upper() 
    date_pretty = now.strftime("%d %b %Y")

    bluf_text = clean_text(
        f"BLUF: Evaluated route ({route_id}) spanning {distance} has been assessed as {risk} RISK. "
        f"Authority {auth_role} has formally {status} this corridor for immediate deployment. "
        f"Drishti Mesh network is currently the SOLE active communication layer (4G/LTE DOWN)."
    )

    # === B. FPDF DRAWING ===
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # 1. HEADER BOX
    pdf.set_line_width(0.5)
    pdf.rect(10, 10, 190, 40)
    pdf.set_xy(10, 15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 8, clean_text("SITUATION REPORT (SITREP)"), ln=1, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 6, clean_text("DRISHTI-NE | AI-Based Disaster Decision Support System"), ln=1, align="C")
    pdf.line(10, 32, 200, 32)
    
    pdf.set_xy(12, 35)
    pdf.set_font("Courier", "B", 10) 
    pdf.cell(90, 5, clean_text(f"FROM: {auth_role}"), ln=0)
    pdf.cell(90, 5, clean_text("TO: CENTRAL COMMAND (DELHI)"), ln=1, align="R")
    
    pdf.set_xy(12, 41)
    pdf.cell(90, 5, clean_text(f"DTG: {dtg}"), ln=0)
    pdf.cell(90, 5, clean_text(f"REP NO: {uuid.uuid4().hex[:8].upper()}"), ln=1, align="R")
    pdf.ln(15)

    # 2. EXECUTIVE SUMMARY
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, clean_text("1. EXECUTIVE SUMMARY"), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_font("Times", "", 11)
    pdf.multi_cell(0, 6, bluf_text)
    pdf.ln(5)

    # 3. ROUTE DETAILS TABLE
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, clean_text("2. OPERATIONAL ROUTE DETAILS"), ln=1, fill=True)
    pdf.ln(2)

    col_w, row_h = 60, 8
    def draw_row(label, value, bold_val=False):
        pdf.set_font("Arial", "B", 10)
        pdf.cell(col_w, row_h, clean_text(label), border=1)
        pdf.set_font("Arial", "B" if bold_val else "", 10)
        if "HIGH" in str(value) or "CRITICAL" in str(value): pdf.set_text_color(200, 0, 0)
        elif "APPROVED" in str(value) or "LOW" in str(value): pdf.set_text_color(0, 100, 0)
        else: pdf.set_text_color(0, 0, 0)
        pdf.cell(0, row_h, clean_text(str(value)), border=1, ln=1)
        pdf.set_text_color(0, 0, 0)

    draw_row("Route ID", route_id)
    draw_row("Total Distance", distance)
    draw_row("Risk Classification", risk, bold_val=True)
    draw_row("Command Decision", status, bold_val=True)
    pdf.ln(5)

    # 4. METADATA
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, clean_text("3. AUTHORIZATION METADATA"), ln=1, fill=True)
    pdf.ln(2)
    draw_row("Authorized By", auth_role)
    draw_row("Decision Time", date_pretty)
    draw_row("Report Generated", date_pretty)
    
    # 5. FOOTER
    pdf.set_y(-40)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(200, 0, 0) 
    pdf.cell(0, 10, clean_text("CLASSIFICATION: RESTRICTED"), ln=1, align="C")
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, clean_text("This document contains sensitive operational data generated by the Drishti-NE System."), ln=1, align="C")
    pdf.cell(0, 5, clean_text("For Official Government Use Only."), ln=1, align="C")

    try:
        return bytes(pdf.output()) 
    except TypeError:
        return pdf.output(dest='S').encode('latin-1')

# --- 5. ENDPOINTS ---

@app.post("/auth/login")
def admin_login(password: str = Form(...)):
    valid_passwords = {"admin123", "india123", "ndrf2026", "command"}
    if password in valid_passwords:
        return {"status": "success", "token": "NDRF-COMMAND-2026-SECURE"}
    return {"status": "error", "message": "Invalid Credentials"}, 401

@app.get("/admin/sitrep/generate")
@app.post("/admin/sitrep/generate")
def generate_sitrep_universal(
    format: str = Query("pdf", description="Output format: pdf or json"),
    api_key: Optional[str] = None, 
    authorization: Optional[str] = Header(None)
):
    # Auth
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key
    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    # Fetch Data
    route, decision = None, None
    try:
        ensure_db_ready()
        if not DEMO_MODE:
            with SessionLocal() as session:
                route, decision = get_latest_route_and_decision(session)
    except Exception:
        pass

    # JSON Response
    if format.lower() == "json":
        # Force defaults for JSON preview too
        r_id = str(route.id) if (route and route.id) else "ROUTE-ALPHA-01"
        dist = f"{route.distance_km} km" if (route and route.distance_km) else "148.2 km"
        return {
            "status": "success",
            "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST"),
            "executive_summary": f"BLUF: Evaluated route ({r_id}) spanning {dist} has been assessed.",
            "data": { "route_id": r_id, "risk": "MODERATE", "decision": "APPROVED" }
        }

    # PDF Response
    try:
        pdf_bytes = generate_professional_pdf(route, decision)
        filename = f"SITREP_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        return Response(
            content=pdf_bytes, 
            media_type="application/pdf", 
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print("❌ PDF GENERATION FAILED:")
        traceback.print_exc() # Print full error to console
        return JSONResponse(status_code=500, content={"status": "error", "message": f"PDF Error: {str(e)}"})

# --- EXISTING FEATURES ---

@app.post("/admin/simulate/start")
def start_simulation(scenario: str = "FLASH_FLOOD", api_key: str = Depends(SecurityGate.verify_admin)):
    SimulationManager.start_scenario(scenario, 26.14, 91.73)
    return {"status": "ACTIVE", "scenario": scenario}

@app.post("/admin/simulate/stop")
def stop_simulation(api_key: str = Depends(SecurityGate.verify_admin)):
    SimulationManager.stop_simulation()
    return {"status": "STOPPED"}

@app.get("/admin/resources")
def get_admin_resources(): return {"resources": ResourceSentinel.get_all()}

@app.post("/admin/broadcast")
def broadcast(message: str): return {"status": "success", "sent": True}

@app.get("/iot/feed")
def get_iot(): return {"sensors": IoTManager.get_live_readings()}

class SOSRequest(BaseModel):
    lat: float
    lng: float
    type: str = "MEDICAL"
    user: Optional[dict] = None

@app.post("/sos/dispatch")
def dispatch(r: SOSRequest):
    return {"status": "success", "mission": {"id": "NDRF-999"}, "message": "Dispatched"}

class MeshMessage(BaseModel):
    sender: str
    text: str
    timestamp: float

MESH_BUFFER = []
@app.post("/mesh/send")
def mesh_send(m: MeshMessage):
    MESH_BUFFER.append(m.dict())
    if len(MESH_BUFFER)>50: MESH_BUFFER.pop(0)
    return {"status":"sent"}

@app.get("/mesh/messages")
def mesh_get(): return MESH_BUFFER
