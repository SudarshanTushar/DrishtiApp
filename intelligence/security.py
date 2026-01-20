from fastapi import Header, HTTPException

class SecurityGate:
    """
    Simulates a Government-Grade Security Gateway.
    Verifies that the request comes from an authorized Admin Console.
    """
    
    @staticmethod
    def verify_admin(x_gov_key: str = Header(None)):
        # The Secret Key used in the Demo
        DEMO_KEY = "NDRF-COMMAND-2026-SECURE"
        
        if x_gov_key == DEMO_KEY:
            return x_gov_key
            
        # If key is missing or wrong -> Block Access
        raise HTTPException(status_code=401, detail="⛔ ACCESS DENIED: Invalid Governance Token")
        
    @staticmethod
    def system_health_check():
        return {"status": "SECURE", "database": "CONNECTED"}
