# backend/intelligence/simulation.py

class SimulationManager:
    """
    The 'God Mode' for the system. 
    Allows admins to trigger fake disasters for drills/demos.
    """
    
    # Global State
    state = {
        "active": False,
        "scenario": None, # 'FLASH_FLOOD', 'LANDSLIDE_CLUSTER'
        "target_lat": 26.14,
        "target_lng": 91.73
    }

    @staticmethod
    def start_scenario(scenario_type, lat, lng):
        SimulationManager.state = {
            "active": True,
            "scenario": scenario_type,
            "target_lat": lat,
            "target_lng": lng
        }
        return {"status": "ACTIVE", "mode": scenario_type}

    @staticmethod
    def stop_simulation():
        SimulationManager.state["active"] = False
        SimulationManager.state["scenario"] = None
        return {"status": "STOPPED"}

    @staticmethod
    def get_overrides():
        return SimulationManager.state
