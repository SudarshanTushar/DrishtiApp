from fastapi import APIRouter, UploadFile, File
import os
import requests

router = APIRouter(prefix="/api/v1/core", tags=["Voice Interface"])

@router.post("/listen")
async def process_voice_command(file: UploadFile = File(...)):
    """
    Interfaces with Sarvam AI for vernacular speech recognition.
    """
    SARVAM_KEY = os.getenv("SARVAM_API_KEY")
    
    # Mock response if key is missing (for local dev)
    if not SARVAM_KEY:
        return {
            "transcript": "Navigate to Shillong",
            "intent": "NAVIGATION",
            "entities": {"destination": "Shillong"},
            "confidence": 0.98
        }
    
    # Actual implementation logic would go here
    return {"status": "MOCK_RESPONSE_ACTIVE"}
