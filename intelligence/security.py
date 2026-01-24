# backend/intelligence/security.py
from fastapi import Request, HTTPException, Security, Header
from fastapi.security import APIKeyHeader, APIKeyQuery
import os
import time

# Define Strategy: Check Header OR Query Param
api_key_header = APIKeyHeader(name="X-GOV-KEY", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

# The Master Key
MASTER_ADMIN_KEY = "NDRF-COMMAND-2026-SECURE"

class SecurityGate:
    """
    'Project Kavach' - The Shield.
    Protects Admin routes from unauthorized access.
    """

    @staticmethod
    async def verify_admin(
        key_header: str = Security(api_key_header),
        key_query: str = Security(api_key_query),
        authorization: str | None = Header(None),
    ):
        """
        Locks the route. Accepts X-GOV-KEY, api_key query, or Authorization: Bearer <MASTER_ADMIN_KEY>.
        """
        # 1. Bearer token in Authorization
        if authorization and authorization.startswith("Bearer ") and authorization.replace("Bearer ", "") == MASTER_ADMIN_KEY:
            return MASTER_ADMIN_KEY

        # 2. Header key
        if key_header == MASTER_ADMIN_KEY:
            return key_header
        
        # 3. URL Query Param (Backup for Demo)
        if key_query == MASTER_ADMIN_KEY:
            return key_query
            
        # 4. Fail if neither matches
        raise HTTPException(
            status_code=403, 
            detail="ACCESS DENIED: Government Clearance Required."
        )

    @staticmethod
    def system_health_check():
        return {
            "status": "OPERATIONAL",
            "timestamp": time.time(),
            "subsystems": {"AI": "ONLINE", "IOT": "CONNECTED", "AUTH": "ACTIVE"}
        }
