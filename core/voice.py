import os
import requests
import time

SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"

async def process_voice_command(file_bytes, filename, content_type):
    api_key = os.getenv("SARVAM_API_KEY")

    # Simulation Fallback if no key
    if not api_key:
        time.sleep(1)
        return {
            "status": "success", "translated_text": "Navigate to Shillong",
            "target": "Shillong", "intent": "NAVIGATION"
        }

    try:
        files = {"file": (filename, file_bytes, content_type)}
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        response = requests.post(SARVAM_URL, headers=headers, files=files)
        
        transcript = response.json().get("transcript", "")
        
        # Intent Detection
        intent = "SOS_TRIGGER" if "help" in transcript.lower() else "NAVIGATION"
        target = "Shillong" if "shillong" in transcript.lower() else "Unknown"

        return {
            "status": "success", "translated_text": transcript,
            "target": target, "intent": intent
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
