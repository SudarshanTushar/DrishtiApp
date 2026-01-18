from fastapi import APIRouter
import random

router = APIRouter(prefix="/command", tags=["Command Center"])

@router.get("/overview")
def get_command_overview():
    """Returns Govt Dashboard Stats"""
    return {
        "active_disasters": 3,
        "total_sos": random.randint(120, 150),
        "deployed_resources": {
            "ambulances": 42, "ndrf_teams": 12, "drones_airborne": 8
        },
        "logistics": {
            "ration_packets": 5000, "medical_kits": 1200
        },
        "red_zones": [
            {"lat": 26.15, "lng": 91.75, "radius": 3000, "type": "CRITICAL"},
            {"lat": 25.57, "lng": 91.89, "radius": 2000, "type": "HIGH_RISK"}
        ]
    }
