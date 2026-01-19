# backend/intelligence/analytics.py
import random
import time
from intelligence.crowdsource import CrowdManager

class AnalyticsEngine:
    """
    Generates high-level situational awareness metrics for the Command Center.
    """

    @staticmethod
    def get_live_stats():
        # Simulate active user base distribution
        total_users = random.randint(1200, 1500)
        offline_users = random.randint(300, 450)
        
        # Get real crowd reports
        reports = CrowdManager.active_reports
        
        # Calculate Risk Distribution (Simulated for Demo based on current rain)
        # In prod, this would query the DB for all active route calculations
        safe_routes = random.randint(60, 80)
        critical_routes = random.randint(10, 20)
        moderate_routes = 100 - safe_routes - critical_routes

        return {
            "timestamp": time.time(),
            "system_status": "OPERATIONAL",
            "field_units": {
                "total": total_users,
                "online": total_users - offline_users,
                "offline_survival_mode": offline_users
            },
            "risk_distribution": [
                {"name": "Safe", "value": safe_routes, "color": "#10b981"},
                {"name": "Moderate", "value": moderate_routes, "color": "#f59e0b"},
                {"name": "Critical", "value": critical_routes, "color": "#ef4444"}
            ],
            "recent_hazards": reports[-5:] if reports else [], # Last 5 reports
            "isro_feed_status": "CONNECTED (Latency: 45ms)"
        }
