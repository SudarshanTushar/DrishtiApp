# backend/intelligence/governance.py

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
