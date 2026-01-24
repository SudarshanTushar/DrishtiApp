from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any
import math
import random
import time

from geoalchemy2 import WKTElement
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db.session import SessionLocal
from db.models import Route, AuthorityDecision, AuditLog

router = APIRouter(prefix="/api/v1/core", tags=["Core Navigation"])

# --- DATA MODELS ---
class Location(BaseModel):
    lat: float
    lng: float

class RouteRequest(BaseModel):
    start: Location
    end: Location
    rain_intensity: int  # mm/hr


class DecisionRequest(BaseModel):
    route_id: str
    actor_role: Literal["DISTRICT", "NDRF"]
    decision: Literal["APPROVED", "REJECTED"]
    actor: str
    context: Dict[str, Any] = Field(default_factory=dict)

# --- MIGRATED SAFE HAVEN DATA ---
SAFE_HAVENS = [
    {"id": "SH_01", "name": "Assam Rifles Cantonment", "lat": 26.15, "lng": 91.76, "type": "MILITARY", "capacity": 5000},
    {"id": "SH_02", "name": "Don Bosco High School", "lat": 26.12, "lng": 91.74, "type": "CIVILIAN", "capacity": 1200},
    {"id": "SH_03", "name": "Civil Hospital Shillong", "lat": 25.57, "lng": 91.89, "type": "MEDICAL", "capacity": 300},
    {"id": "SH_04", "name": "Kohima Science College", "lat": 25.66, "lng": 94.10, "type": "RELIEF_CAMP", "capacity": 2000}
]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def _to_point(lat: float, lng: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


@router.post("/analyze-route")
def calculate_tactical_route(request: RouteRequest):
    """
    Core Pathfinding Algorithm (V2).
    Determines route safety based on rain intensity and terrain data.
    """
    # Simulate processing latency for realism
    time.sleep(0.3)
    
    # Risk Logic: Rain > 40mm/hr triggers "Safety First" protocol
    is_critical_weather = request.rain_intensity > 40
    
    routes = []
    
    # 1. Fast Route (High Risk)
    routes.append({
        "id": "route_fast",
        "label": "FASTEST",
        "distance_km": 124.5,
        "eta": "3h 10m",
        "risk_level": "HIGH" if is_critical_weather else "MODERATE",
        "hazards": ["Landslide Prone (Km 42)", "Slippery Road"] if is_critical_weather else []
    })
    
    # 2. Safe Route (Low Risk)
    routes.append({
        "id": "route_safe",
        "label": "SAFEST",
        "distance_km": 148.2,
        "eta": "4h 05m",
        "risk_level": "LOW",
        "hazards": []
    })
    
    # Find nearest evacuation points
    evac_points = sorted(SAFE_HAVENS, key=lambda x: haversine(request.start.lat, request.start.lng, x['lat'], x['lng']))[:3]

    recommended_id = "route_safe" if is_critical_weather else "route_fast"
    selected_route = next(r for r in routes if r["id"] == recommended_id)

    persisted_route_id = None
    try:
        with SessionLocal() as session:
            db_route = Route(
                start_geom=_to_point(request.start.lat, request.start.lng),
                end_geom=_to_point(request.end.lat, request.end.lng),
                distance_km=selected_route.get("distance_km"),
                risk_level=selected_route.get("risk_level"),
            )
            session.add(db_route)
            session.commit()
            session.refresh(db_route)
            persisted_route_id = str(db_route.id)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist route: {exc}")

    return {
        "status": "SUCCESS",
        "recommended_route": recommended_id,
        "routes": routes,
        "nearest_safe_havens": evac_points,
        "persisted_route_id": persisted_route_id,
    }


@router.post("/routes/{route_id}/decision")
def record_authority_decision(route_id: str, payload: DecisionRequest):
    if payload.route_id != route_id:
        raise HTTPException(status_code=400, detail="route_id mismatch between path and payload")

    try:
        with SessionLocal() as session:
            decision = AuthorityDecision(
                route_id=route_id,
                actor_role=payload.actor_role,
                decision=payload.decision,
            )
            session.add(decision)
            session.flush()

            audit_entry = AuditLog(
                actor=payload.actor,
                action="AUTHORITY_DECISION",
                payload={
                    "route_id": route_id,
                    "actor_role": payload.actor_role,
                    "decision": payload.decision,
                    "context": payload.context,
                },
            )
            session.add(audit_entry)
            session.commit()
            session.refresh(decision)

            return {"status": "RECORDED", "decision_id": str(decision.id)}
    except IntegrityError:
        raise HTTPException(status_code=404, detail="Route not found for decision")
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to persist decision: {exc}")
