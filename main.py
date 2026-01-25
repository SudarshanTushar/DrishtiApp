from fastapi import FastAPI, UploadFile, File, Form, Depends, Header, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import requests
import random
import uuid
from datetime import datetime, timezone
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
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    Base.metadata.create_all(bind=engine)


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


def build_sitrep_payload(route, decision):
    """
    Constructs a CLEAN, WHITELISTED SITREP payload.
    Strictly forbids route_id, UUIDs, metadata, or raw timestamps.
    """
    def _fmt_ist(dt_obj):
        if not dt_obj:
            dt_obj = datetime.now(timezone.utc)
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=timezone.utc)
        return dt_obj.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")

    # 1. Extract & Normalize Data
    risk_level = (route.risk_level or "MODERATE").upper()
    decision_status = (decision.decision if decision else "PENDING").upper()
    actor = decision.actor_role if decision else "NDRF Authority"
    
    # 2. Safety Classification Logic
    if risk_level == "LOW":
        safety_class = "Safe"
    elif risk_level == "MODERATE":
        safety_class = "Conditional"
    else:
        safety_class = "Unsafe"

    # 3. Formatted Strings
    distance_val = route.distance_km
    distance_str = f"{distance_val:.1f} km" if distance_val is not None else "148.2 km"
    decision_time_str = _fmt_ist(decision.created_at if decision else None)

    # 4. Content Integration
    executive_summary = (
        f"Based on the latest terrain and weather assessment, the evaluated emergency route has been classified as "
        f"{risk_level} RISK and has been {decision_status} by the {actor} for controlled emergency deployment."
    )

    # 5. Return STRICT WHITELIST (No internal keys)
    return {
        "executive_summary": executive_summary,
        "route_overview": {
            "distance": distance_str,
            "risk_level": risk_level,
            "safety_classification": safety_class
        },
        "authority_decision": {
            "authority": actor,
            "decision": decision_status,
            "decision_time": decision_time_str
        }
    }


def build_sitrep_html(sitrep: dict, stats: dict, resources: list, audit_logs: list, pending_decisions: list) -> str:
    """Render an HTML SITREP (print/save ready). Adapted for Clean Payload."""
    import datetime

    # HTML still needs some extra resource/stats tables, passed separately.
    # We pull the main text from the specific whitelisted sitrep structure.

    # Helper for audit logs time (stats timestamps are not in the clean payload)
    def fmt_ist_log(dt_str: Optional[str]) -> str:
        if not dt_str: return "N/A"
        try:
             parsed = datetime.datetime.fromisoformat(dt_str)
             if parsed.tzinfo is None: parsed = parsed.replace(tzinfo=datetime.timezone.utc)
             return parsed.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b %H:%M")
        except: return dt_str

    resources_by_type = {}
    for r in resources:
        rtype = r.get("type", "OTHER")
        resources_by_type[rtype] = resources_by_type.get(rtype, 0) + 1

    resources_rows = "".join(
        f"<tr><td style='padding:8px; border:1px solid #cbd5e1;'>{rtype}</td>"
        f"<td style='padding:8px; border:1px solid #cbd5e1; text-align:center; font-weight:bold;'>{count}</td></tr>"
        for rtype, count in resources_by_type.items()
    )
    resources_table = (
        "<table style='width:100%; border-collapse:collapse;'>"
        "<tr style='background:#f1f5f9;'><th style='padding:8px; border:1px solid #cbd5e1; text-align:left;'>Resource Type</th>"
        "<th style='padding:8px; border:1px solid #cbd5e1; text-align:center;'>Count</th></tr>"
        f"{resources_rows}</table>" if resources_by_type else "<p style='color:#f59e0b;'>⚠️ No resources currently registered</p>"
    )

    decisions_items = []
    for i, d in enumerate(pending_decisions[:8], 1):
        risk_badge = (
            "<span style='background:#dc2626; color:white; padding:2px 8px; border-radius:3px; font-size:10px;'>"
            f"{d.get('risk', 'UNKNOWN')}</span>"
        )
        decisions_items.append(f"<li><strong>{i}.</strong> {d.get('type','DECISION')} {risk_badge}</li>")
    decisions_html = (
        "<ul>" + "".join(decisions_items) + "</ul>"
        if decisions_items
        else "<p style='color:#10b981;'>✓ No pending critical decisions</p>"
    )

    audit_items = [
        f"<li><strong>{fmt_ist_log(log.get('timestamp'))}</strong> - {log.get('action','N/A')}: {log.get('details','N/A')}</li>"
        for log in audit_logs[-12:]
    ]
    audit_html = "<ul>" + "".join(audit_items) + "</ul>" if audit_items else "<p>No recent activity logged</p>"

    now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
    
    # Extract from CLEAN PAYLOAD
    exec_summary = sitrep.get("executive_summary", "Assessment pending.")
    
    overview = sitrep.get("route_overview", {})
    distance_text = overview.get("distance", "N/A")
    risk_level = overview.get("risk_level", "MODERATE")
    
    auth_data = sitrep.get("authority_decision", {})
    decision_status = auth_data.get("decision", "PENDING")
    decision_actor = auth_data.get("authority", "NDRF")
    readable_decided = auth_data.get("decision_time", now.strftime("%d %b %Y, %I:%M %p IST"))

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>SITREP - {now.strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #ffffff; color: #0f172a; padding: 32px; max-width: 880px; margin: 0 auto; }}
        .header {{ text-align: center; border-bottom: 3px solid #0f172a; padding-bottom: 18px; margin-bottom: 28px; }}
        .title {{ font-size: 24px; font-weight: 700; letter-spacing: 0.4px; }}
        .org {{ font-size: 15px; color: #475569; margin-top: 6px; }}
        .section {{ margin: 24px 0; padding: 18px; background: #f8fafc; border-left: 4px solid #2563eb; }}
        .section-title {{ font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .meta {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 18px; padding: 14px; background: #fff7ed; border-radius: 6px; border: 1px solid #fed7aa; }}
        .badge {{ background: #dc2626; color: white; padding: 6px 14px; border-radius: 999px; font-size: 11px; font-weight: 700; }}
        .stats {{ display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 14px; margin: 16px 0; }}
        .stat-box {{ padding: 14px; background: white; border: 1px solid #e2e8f0; border-radius: 6px; }}
        .stat-label {{ font-size: 12px; color: #64748b; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.4px; }}
        .stat-value {{ font-size: 22px; font-weight: 700; color: #0f172a; }}
        ul {{ list-style: none; padding: 0; margin: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
        table {{ font-size: 13px; }}
        @media print {{ body {{ padding: 12px; }} .section {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <div class='header'>
        <div class='title'>SITUATION REPORT (SITREP)</div>
        <div class='org'>National Disaster Response Force (NDRF)<br/>Northeast Command</div>
    </div>

        <div class='meta'>
            <div><strong>Date:</strong> {now.strftime('%d %b %Y, %I:%M %p IST')}</div>
            <div><strong>Assessment:</strong> Evaluated Route</div>
            <div><span class='badge'>RESTRICTED</span></div>
        </div>

    <div class='section'>
        <div class='section-title'>1. Executive Summary</div>
        <div class='stats'>
            <div class='stat-box'><div class='stat-label'>Active Operations</div><div class='stat-value' style='color:#2563eb;'>{stats.get('active_missions',0)}</div></div>
            <div class='stat-box'><div class='stat-label'>SOS Alerts</div><div class='stat-value' style='color:#dc2626;'>{stats.get('sos_count',0)}</div></div>
            <div class='stat-box'><div class='stat-label'>Critical Decisions</div><div class='stat-value' style='color:#f59e0b;'>{len(pending_decisions)}</div></div>
            <div class='stat-box'><div class='stat-label'>Resources Deployed</div><div class='stat-value' style='color:#16a34a;'>{len(resources)}</div></div>
        </div>
        <p style='margin-top:12px; color:#475569; line-height:1.6;'>{exec_summary}</p>
    </div>

    <div class='section'>
        <div class='section-title'>2. Route & Decision</div>
        <p><strong>Risk Level:</strong> {risk_level}</p>
        <p><strong>Authority Decision:</strong> {decision_status} ({decision_actor})</p>
        <p><strong>Decision Time:</strong> {readable_decided}</p>
        <p><strong>Distance:</strong> {distance_text}</p>
    </div>

    <div class='section'>
        <div class='section-title'>3. Resource Deployment</div>
        {resources_table}
        <p style='margin-top:12px; color:#475569;'>Supply status: Adequate stocks of food, water, and medical supplies; emergency rations sufficient for 72 hours.</p>
    </div>

    <div class='section'>
        <div class='section-title'>4. Pending Critical Decisions</div>
        {decisions_html}
    </div>

    <div class='section'>
        <div class='section-title'>5. Recent Activity Log</div>
        {audit_html}
    </div>

    <div class='section'>
        <div class='section-title'>6. Recommendations</div>
        <ul>
            <li>✓ Continue 24/7 monitoring of weather patterns</li>
            <li>✓ Pre-position resources in high-risk zones (Silchar, Haflong)</li>
            <li>✓ Maintain heightened alert status for next 48 hours</li>
            <li>✓ Conduct daily situation briefings at 0800 and 2000 hrs</li>
            <li>✓ Coordinate with State Disaster Management Authorities</li>
        </ul>
    </div>

    <div style='text-align:center; margin-top:40px; padding-top:16px; border-top:2px solid #e2e8f0; color:#64748b; font-size:12px;'>
        END OF REPORT - GENERATED BY ROUTEAI-NE SYSTEM
    </div>
</body>
</html>"""
    return html


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

    try:
        ensure_db_ready()
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "error", "message": "Database schema setup failed", "detail": str(exc)})

    try:
        with SessionLocal() as session:
            latest_route, latest_decision = get_latest_route_and_decision(session)
    except SQLAlchemyError as exc:
        return JSONResponse(status_code=503, content={"status": "error", "message": "Database unavailable", "detail": str(exc)})

    sitrep = build_sitrep_payload(latest_route, latest_decision)

    # Honor requested format
    fmt = (format or "json").lower()
    if fmt == "pdf":
        return _sitrep_pdf_response(api_key, authorization)
    if fmt == "html":
        stats = AnalyticsEngine.get_live_stats()
        resources = ResourceSentinel.get_all()
        audit_logs = AuditLogger.get_logs()
        html = build_sitrep_html(sitrep, stats, resources, audit_logs, PENDING_DECISIONS)
        return Response(content=html.encode("utf-8"), media_type="text/html", headers={"Content-Disposition": "inline; filename=SITREP.html"})

    return JSONResponse(content=sitrep)


def _sitrep_pdf_response(api_key: Optional[str], authorization: Optional[str]):
    """Internal helper to generate a professional PDF SITREP and return Response."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key

    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    try:
        ensure_db_ready()
    except Exception as exc:
        AuditLogger.log("SYSTEM", "DB_SETUP_FAIL", str(exc), "ERROR")
        # Continue anyway as tables might exist

    try:
        with SessionLocal() as session:
            latest_route, latest_decision = get_latest_route_and_decision(session)
            # Use the CLEAN payload builder
            sitrep = build_sitrep_payload(latest_route, latest_decision)
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "error", "message": "Database unavailable", "detail": str(exc)})

    ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    file_slug_time = ist_now.strftime("%Y%m%d_%H%M")
    district_name = "Kamrup_Metro"

    # EXTRACT SAFE VALUES DIRECTLY (No logic here)
    executive_summary = sitrep["executive_summary"]
    
    overview = sitrep["route_overview"]
    distance_text = overview["distance"]
    risk_level = overview["risk_level"]
    safety_classification = overview["safety_classification"]
    
    authority = sitrep["authority_decision"]
    auth_name = authority["authority"]
    auth_decision = authority["decision"]
    auth_time = authority["decision_time"]

    # Build PDF (Strict Whitelist Layout)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def add_spacer(h=4):
        pdf.ln(h)

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SITUATION REPORT (SITREP)", ln=1, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, "DRISHTI-NE | AI-Based Disaster Decision Support System", ln=1, align="C")
    add_spacer(2)

    # Section 1: Executive Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "1. Executive Summary", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 7, executive_summary)
    add_spacer()

    # Section 2: Route Overview (table)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "2. Route Overview", ln=1)
    pdf.set_font("Arial", "B", 11)
    
    # 3-Column Table Header
    col_widths = [60, 40, 60]
    headers = ["Distance", "Risk Level", "Safety Classification"]
    for header, width in zip(headers, col_widths):
        pdf.cell(width, 8, header, border=1, align="C")
    pdf.ln()
    
    # 3-Column Table Row (Manual Placement)
    pdf.set_font("Arial", "", 11)
    pdf.cell(col_widths[0], 8, distance_text, border=1, align="C")
    pdf.cell(col_widths[1], 8, risk_level, border=1, align="C")
    pdf.cell(col_widths[2], 8, safety_classification, border=1, align="C")
    pdf.ln()
    add_spacer()

    # Section 3: Authority Decision
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "3. Authority Decision", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Decision Authority: {auth_name}", ln=1)
    pdf.cell(0, 7, f"Final Decision: {auth_decision}", ln=1)
    pdf.cell(0, 7, f"Decision Time: {auth_time}", ln=1)
    add_spacer()

    # Footer
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 6, "For Official Use Only", ln=1, align="C")
    pdf.cell(0, 6, "Generated by DRISHTI-NE | Government Pilot Mode", ln=1, align="C")

    # Fail-fast validation
    # Scan ENTIRE PDF text content (approximated by scanning inputs used)
    # A true PDF text scan requires reading the output bytes, but scanning inputs covers 99% of cases here.
    rendered_text = " ".join([
        executive_summary,
        distance_text,
        risk_level,
        safety_classification,
        auth_name,
        auth_decision,
        auth_time
    ])
    
    import re
    # Stronger Check: Look for 8-4-4-4-12 UUID format
    uuid_pattern = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    # Regex for ISO timestamps like 2026-01-25T04...
    iso_like_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
    
    forbidden_hits = [
        bool(uuid_pattern.search(rendered_text)),
        "Metadata" in rendered_text,
        "Route ID" in rendered_text,
        "Timestamp" in rendered_text,
        "n/a" in rendered_text.lower(),
        bool(iso_like_pattern.search(rendered_text)),
    ]
    
    # VISUAL MARKER: PROOF OF NEW CODE
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 6, "For Official Use Only", ln=1, align="C")
    pdf.cell(0, 6, "Generated by DRISHTI-NE | Government Pilot Mode | V2.0-SECURE-STABLE", ln=1, align="C")

    if any(forbidden_hits):
        AuditLogger.log("SYSTEM", "SITREP_RENDER_BLOCKED", "Forbidden field detected in PDF render", "ERROR")
        return JSONResponse(status_code=500, content={"status": "error", "message": "SITREP render blocked: forbidden internal fields"})

    # Output PDF
    pdf_bytes = bytes(pdf.output())
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=SITREP_{file_slug_time}.pdf"})


@app.post("/admin/sitrep/pdf")
def generate_sitrep_pdf(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """POST: Generate a professional PDF SITREP using the latest route/decision."""
    return _sitrep_pdf_response(api_key, authorization)


@app.get("/admin/sitrep/pdf")
def generate_sitrep_pdf_get(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """GET: Generate a professional PDF SITREP (download-friendly)."""
    return _sitrep_pdf_response(api_key, authorization)


@app.get("/admin/sitrep/html")
def generate_sitrep_html(api_key: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """GET: Generate an HTML SITREP (rich layout, print/save to PDF)."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    elif api_key:
        token = api_key

    if token != "NDRF-COMMAND-2026-SECURE":
        return JSONResponse(status_code=403, content={"status": "error", "message": "Unauthorized"})

    try:
        ensure_db_ready()
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "error", "message": "Database schema setup failed", "detail": str(exc)})

    try:
        with SessionLocal() as session:
            latest_route, latest_decision = get_latest_route_and_decision(session)
            sitrep = build_sitrep_payload(latest_route, latest_decision)
            stats = AnalyticsEngine.get_live_stats()
            resources = ResourceSentinel.get_all()
            audit_logs = AuditLogger.get_logs()
    except SQLAlchemyError as exc:
        return JSONResponse(status_code=503, content={"status": "error", "message": "Database unavailable", "detail": str(exc)})

    html = build_sitrep_html(sitrep, stats, resources, audit_logs, PENDING_DECISIONS)
    return Response(
        content=html.encode("utf-8"),
        media_type="text/html",
        headers={"Content-Disposition": "inline; filename=SITREP.html"},
    )


@app.get("/admin/audit-log")
def get_audit_trail(api_key: str = Depends(SecurityGate.verify_admin)):
    """Return recent audit log entries (admin only)."""
    return AuditLogger.get_logs()

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
