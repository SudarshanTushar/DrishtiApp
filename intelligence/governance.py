import time
import uuid

class SafetyGovernance:
    """
    NON-NEGOTIABLE SAFETY RULES (GOVERNMENT MANDATE).
    These rules override any AI/ML prediction.
    """
    
    @staticmethod
    def validate_risk(rain_mm: int, slope_angle: float, ai_prediction_score: int):
        final_risk = "SAFE"
        reason = "Normal Conditions"
        score = ai_prediction_score

        # RULE 1: The "Cloudburst" Protocol (IMD Override)
        # If rain > 100mm, it is UNSAFE regardless of what AI says.
        if rain_mm > 100:
            return {
                "risk": "CRITICAL", 
                "score": 10, 
                "reason": "EXTREME RAINFALL (Protocol 101)",
                "source": "IMD Realtime"
            }

        # RULE 2: The "Critical Slope" Protocol (ISRO Data Override)
        # Slopes > 45 deg with Moderate Rain are always dangerous.
        if slope_angle > 45 and rain_mm > 40:
            return {
                "risk": "HIGH", 
                "score": 30, 
                "reason": "UNSTABLE SLOPE + RAIN (ISRO Threshold)",
                "source": "ISRO Cartosat DEM"
            }

        # RULE 3: AI Model Validation
        if ai_prediction_score < 40:
            final_risk = "CRITICAL"
            reason = "AI Model Alert (Landslide Probability > 80%)"
        elif ai_prediction_score < 70:
            final_risk = "MODERATE"
            reason = "AI Model Caution"

        return {
            "risk": final_risk,
            "score": score,
            "reason": reason,
            "source": "RouteAI Fusion Engine"
        }

class DecisionEngine:
    """
    GOVERNANCE LAYER:
    Converts raw Risk Assessments into Formal Action Proposals.
    AI generates the 'Draft Order', Human signs the 'Final Order'.
    """
    
    @staticmethod
    def create_proposal(risk_data, lat, lng):
        """
        Input: Risk Dictionary (from SafetyGovernance)
        Output: A formal 'Decision Proposal' object for the Dashboard Queue.
        """
        proposal_id = f"CMD-{str(uuid.uuid4())[:8].upper()}"
        
        # 1. Map Risk Level to Standard Operating Procedure (SOP)
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
            
        # 2. Structure the Official Proposal
        return {
            "id": proposal_id,
            "timestamp": time.time(),
            "type": recommended_action,
            "target_zone": {
                "lat": lat, 
                "lng": lng, 
                "radius": "5km"
            },
            "reason": risk_data["reason"],
            "ai_confidence": risk_data.get("score", 0),
            "source_intel": risk_data.get("source", "Unknown"),
            "status": "PENDING_APPROVAL", # Waiting for Human Authorization
            "urgency": urgency
        }
