# backend/intelligence/simulation.py

class SimulationManager:
    """
    The 'God Mode' for the system. 
    Injects synthetic disaster data to test the Governance & Response layers.
    """
    
    # Global State
    state = {
        "active": False,
        "scenario": None, 
        "target_lat": 26.14,
        "target_lng": 91.73,
        "details": {}
    }

    # PRE-DEFINED SCENARIOS (The "Script" for your Demo)
    SCENARIOS = {
        "FLASH_FLOOD": {
            "type": "FLASH_FLOOD",
            "risk": "CRITICAL",
            "reason": "Glacial Lake Outburst (GLOF) Detected at Teesta V Dam.",
            "source": "Hydro-Sensor Network (Sector 4)",
            "score": 99,
            "impact_radius": "8km"
        },
        "LANDSLIDE": {
            "type": "LANDSLIDE",
            "risk": "HIGH",
            "reason": "Seismic Soil Liquefaction & Slope Instability > 45°.",
            "source": "ISRO Cartosat-3 DEM + Geophone Array",
            "score": 88,
            "impact_radius": "3km"
        }
    }

    @staticmethod
    def start_scenario(scenario_key, lat, lng):
        """
        Activates the system. Returns the scenario details to be injected.
        """
        scenario = SimulationManager.SCENARIOS.get(scenario_key, SimulationManager.SCENARIOS["FLASH_FLOOD"])
        
        SimulationManager.state = {
            "active": True,
            "scenario": scenario_key,
            "target_lat": lat,
            "target_lng": lng,
            "details": scenario
        }
        return scenario

    @staticmethod
    def stop_simulation():
        """
        Resets the system to 'Peace Time'.
        """
        SimulationManager.state = {
            "active": False,
            "scenario": None,
            "target_lat": 26.14,
            "target_lng": 91.73,
            "details": {}
        }
        return {"status": "STOPPED"}

    @staticmethod
    def get_overrides():
        return SimulationManager.state
