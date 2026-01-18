import os
import requests
import time

SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

async def process_voice_command(file_bytes, filename, content_type):
    """
    Sends audio to Sarvam AI and detects user intent.
    Returns: { "status", "translated_text", "target", "intent" }
    """
    api_key = os.getenv("SARVAM_API_KEY")

    # 1. Check for API Key (Simulation Fallback)
    if not api_key or api_key == "API_KEY":
        print("⚠️ No Real API Key. Simulating Voice Response.")
        time.sleep(1)
        return {
            "status": "success",
            "translated_text": "Navigate to Shillong",
            "target": "Shillong",
            "intent": "NAVIGATION"
        }

    # 2. Real API Call
    try:
        files = {"file": (filename, file_bytes, content_type)}
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        if response.status_code == 200:
            result = response.json()
            transcript = result.get("transcript", "")
            return parse_intent(transcript)
        else:
            print(f"❌ Sarvam API Error: {response.text}")
            return {"status": "error", "message": "Translation Failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def parse_intent(text):
    """Analyzes text to find Destination or SOS keywords."""
    text_lower = text.lower()
    intent = "NAVIGATION"
    target = "Unknown"

    # SOS Detection
    if "help" in text_lower or "sos" in text_lower or "emergency" in text_lower:
        intent = "SOS_TRIGGER"

    # Destination Detection (Simple Keyword Matching)
    cities = ["shillong", "kohima", "guwahati", "agartala", "itanagar", "imphal", "aizawl"]
    for city in cities:
        if city in text_lower:
            target = city.capitalize()
            break
            
    return {
        "status": "success",
        "translated_text": text,
        "target": target,
        "intent": intent
    }
