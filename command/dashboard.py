from fastapi import APIRouter
import random

# Initialize Command Router
router = APIRouter(prefix="/command", tags=["Command & Control"])

@router.get("/overview")
def get_command_overview():
    """
    Returns real-time situational awareness for the Government Dashboard.
    Aggregates data from Sentinel and Field Units.
    """
    # Mock Data for Hackathon Demo
    return {
        "status": "ACTIVE_EMERGENCY",
        "active_disasters": 3,
        "total_sos": random.randint(120, 150),
        "deployed_resources": {
            "ambulances": 42,
            "ndrf_teams": 12,
            "drones_airborne": 8
        },
        "logistics": {
            "ration_packets": 5000,
            "medical_kits": 1200
        },
        # Simulated Red Zones for the Map
        "red_zones": [
            {"lat": 26.15, "lng": 91.75, "radius": 3000, "type": "LANDSLIDE_HIGH"},
            {"lat": 25.57, "lng": 91.89, "radius": 2000, "type": "FLOOD_RISK"}
        ]
    }
