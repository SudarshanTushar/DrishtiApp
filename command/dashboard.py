from fastapi import APIRouter
import random

router = APIRouter(prefix="/api/v1/command", tags=["Command Dashboard"])

@router.get("/overview")
def get_strategic_overview():
    """
    Aggregates data for the District Magistrate / Commander.
    """
    return {
        "defcon_level": 3,
        "active_incidents": 3,
        "sos_beacons_active": random.randint(12, 40),
        "resources": {
            "ambulances_deployed": 42,
            "ndrf_teams_active": 12,
            "air_assets": 8
        },
        "logistics": {
            "food_packets": 5000,
            "medical_kits": 1200
        }
    }
