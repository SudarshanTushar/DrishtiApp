# backend/intelligence/crowdsource.py
import time

class CrowdManager:
    """
    Manages the 'Human Sensor Network'.
    Aggregates user reports and determines if a route should be flagged.
    """
    
    # In-memory store for demo (Use Redis/Postgres in Prod)
    active_reports = [] 
    
    # TRUST THRESHOLDS
    THRESHOLD_WARNING = 3  # 3 user reports = Mark as Risky
    THRESHOLD_CRITICAL = 5 # 5 reports = Mark as Closed

    @staticmethod
    def submit_report(lat: float, lng: float, hazard_type: str):
        report = {
            "lat": lat,
            "lng": lng,
            "type": hazard_type,
            "timestamp": time.time(),
            "verified": False
        }
        CrowdManager.active_reports.append(report)
        return CrowdManager.evaluate_zone(lat, lng)

    @staticmethod
    def evaluate_zone(lat, lng):
        """
        Checks how many reports exist near this location (Geospatial Clustering).
        Returns the derived risk level.
        """
        # Simple Clustering Logic (approx 1km radius)
        nearby_reports = [
            r for r in CrowdManager.active_reports 
            if abs(r["lat"] - lat) < 0.01 and abs(r["lng"] - lng) < 0.01
        ]
        
        count = len(nearby_reports)
        
        if count >= CrowdManager.THRESHOLD_CRITICAL:
            return {"risk": "CRITICAL", "source": f"Confirmed by {count} Citizens"}
        elif count >= CrowdManager.THRESHOLD_WARNING:
            return {"risk": "HIGH", "source": f"Reported by {count} Citizens"}
        elif count > 0:
            return {"risk": "MODERATE", "source": "Unverified User Report"}
        
        return None # No crowd data

    @staticmethod
    def admin_override(lat: float, lng: float, status: str):
        """
        GOVERNMENT 'KILL SWITCH'.
        Instantly marks a zone, bypassing all voting logic.
        """
        # Fake an overwhelming number of reports to force the logic
        for _ in range(10):
            CrowdManager.active_reports.append({
                "lat": lat, "lng": lng, 
                "type": f"ADMIN_OVERRIDE_{status}", 
                "timestamp": time.time(),
                "verified": True
            })
