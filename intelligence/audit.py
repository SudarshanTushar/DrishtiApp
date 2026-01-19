# backend/intelligence/audit.py
import time
from datetime import datetime

class AuditLogger:
    """
    'The Black Box'. 
    Records critical events for post-disaster forensic analysis.
    """
    
    # In-memory storage for hackathon (Use PostgreSQL/Blockchain in prod)
    LOGS = []

    @staticmethod
    def log(actor, action, details, severity="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "id": f"LOG_{int(time.time()*1000)}",
            "time": timestamp,
            "actor": actor,       # e.g., "SYSTEM", "ADMIN", "USER_101"
            "action": action,     # e.g., "ROUTE_CLOSE", "SOS_DISPATCH"
            "details": details,
            "severity": severity  # INFO, WARN, CRITICAL
        }
        # Prepend to keep newest first
        AuditLogger.LOGS.insert(0, entry)
        # Keep only last 100 logs
        if len(AuditLogger.LOGS) > 100:
            AuditLogger.LOGS.pop()
        
        return entry

    @staticmethod
    def get_logs():
        return AuditLogger.LOGS

    @staticmethod
    def generate_cap_xml(alert_msg, lat, lng):
        """
        Generates NDMA-compliant Common Alerting Protocol (XML)
        for Mass SMS/Cell Broadcast.
        """
        # Simulated XML generation
        return f"""
        <alert>
            <identifier>NDMA-CAP-{int(time.time())}</identifier>
            <sender>ROUTEAI-NE-GOV</sender>
            <sent>{datetime.now().isoformat()}</sent>
            <status>Actual</status>
            <msgType>Alert</msgType>
            <scope>Public</scope>
            <info>
                <category>Geo</category>
                <event>Landslide/Flood</event>
                <urgency>Immediate</urgency>
                <severity>Extreme</severity>
                <certainty>Observed</certainty>
                <headline>{alert_msg}</headline>
                <area>
                    <areaDesc>Lat: {lat}, Lng: {lng}</areaDesc>
                    <circle>{lat},{lng} 5.0</circle>
                </area>
            </info>
        </alert>
        """
