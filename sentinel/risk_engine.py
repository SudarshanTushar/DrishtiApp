from fastapi import APIRouter
from pydantic import BaseModel
import random
import math

router = APIRouter(prefix="/sentinel", tags=["Sentinel Intelligence"])

class WhistleStatus(BaseModel):
    lat: float
    lng: float
    active: bool

# Mock Risk Data
RISK_ZONES = [
    {"lat": 26.1, "lng": 91.8, "radius": 1.5, "type": "LANDSLIDE_HIGH", "advice": "Slope Instability Detected"},
    {"lat": 24.9, "lng": 92.6, "radius": 2.0, "type": "FLASH_FLOOD", "advice": "Water Levels Rising"}
]

@router.get("/risk-overlay")
def get_risk_overlay(lat: float, lng: float):
    """Returns nearby risk zones"""
    return {"zones": RISK_ZONES, "status": "ONLINE"}

@router.post("/whistle")
def trigger_whistle(status: WhistleStatus):
    """Logs Digital Siren Activation"""
    if status.active:
        print(f"🚨 DIGITAL SIREN ACTIVE at {status.lat}, {status.lng}")
    return {"status": "LOGGED"}
