# GOVERNMENT AUTHENTICATION MODULE
# Simulates OAuth2 / Parichay (Gov Login)

def verify_token(token):
    """
    Verifies the JWT token from the mobile client.
    """
    if not token:
        return False
    # Mock validation
    return {"user_id": "GOV_OFFICIAL_101", "clearance": "TOP_SECRET"}

def dpdp_mask_data(user_data):
    """
    Ensures DPDP Act Compliance by masking PII.
    """
    # Remove sensitive fields before logging
    safe_data = user_data.copy()
    if 'phone' in safe_data:
        safe_data['phone'] = 'REDACTED'
    return safe_data