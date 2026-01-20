import time
import uuid

class SafetyGovernance:
    """
    NON-NEGOTIABLE SAFETY RULES (GOVERNMENT MANDATE).
    """
    @staticmethod
    def validate_risk(rain_mm: int, slope_angle: float, ai_prediction_score: int):
        final_risk = "SAFE"
        reason = "Normal Conditions"
        score = ai_prediction_score

        if rain_mm > 100:
            return {"risk": "CRITICAL", "score": 10, "reason": "EXTREME RAINFALL (Protocol 101)", "source": "IMD Realtime"}

        if slope_angle > 45 and rain_mm > 40:
            return {"risk": "HIGH", "score": 30, "reason": "UNSTABLE SLOPE + RAIN (ISRO Threshold)", "source": "ISRO Cartosat DEM"}

        if ai_prediction_score < 40:
            final_risk = "CRITICAL"
            reason = "AI Model Alert (Landslide Probability > 80%)"
        elif ai_prediction_score < 70:
            final_risk = "MODERATE"
            reason = "AI Model Caution"

        return {"risk": final_risk, "score": score, "reason": reason, "source": "RouteAI Fusion Engine"}

class DecisionEngine:
    """
    GOVERNANCE LAYER:
    Converts raw Risk Assessments into Formal Action Proposals.
    """
    @staticmethod
    def create_proposal(risk_data, lat, lng):
        proposal_id = f"CMD-{str(uuid.uuid4())[:8].upper()}"
        
        recommended_action = "MONITOR_ONLY"
        urgency = "LOW"
        
        if risk_data["risk"] == "CRITICAL":
            recommended_action = "MASS_EVACUATION_ALERT"
            urgency = "IMMEDIATE"
        elif risk_data["risk"] == "HIGH":
            recommended_action = "DEPLOY_NDRF_SCOUT"
            urgency = "HIGH"
        elif risk_data["risk"] == "MODERATE":
            recommended_action = "ISSUE_CITIZEN_ADVISORY"
            urgency = "MEDIUM"
            
        return {
            "id": proposal_id,
            "timestamp": time.time(),
            "type": recommended_action,
            "target_zone": {"lat": lat, "lng": lng, "radius": "5km"},
            "reason": risk_data["reason"],
            "ai_confidence": risk_data.get("score", 0),
            "source_intel": risk_data.get("source", "Unknown"),
            "status": "PENDING_APPROVAL",
            "urgency": urgency
        }
