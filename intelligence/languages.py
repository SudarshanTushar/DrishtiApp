# backend/intelligence/languages.py

class LanguageConfig:
    """
    Defines supported languages and offline fallback responses.
    """
    
    SUPPORTED_LANGUAGES = {
        "en-IN": "English (India)",
        "hi-IN": "Hindi (हिंदी)",
        "as-IN": "Assamese (অসমীয়া)"
    }

    # Offline Fallback Responses (When Sarvam AI is unreachable)
    OFFLINE_RESPONSES = {
        "en-IN": {
            "SAFE": "Route is safe. Proceed with caution.",
            "RISK": "Warning. High risk detected. Do not proceed.",
            "SOS": "Emergency mode activated. Alerting authorities."
        },
        "hi-IN": {
            "SAFE": "रास्ता सुरक्षित है। सावधानी से आगे बढ़ें।",
            "RISK": "चेतावनी। खतरा है। आगे न बढ़ें।",
            "SOS": "आपातकालीन मोड सक्रिय। अधिकारियों को सूचित किया जा रहा है।"
        },
        "as-IN": {
            "SAFE": "पथ सुरक्षित। सावधान থাকিব।",
            "RISK": "सतर्क। বিপদ আছে। আগ नাবাঢ়িব।",
            "SOS": "জৰুৰীকালীন সেৱা সক্ৰিয়।"
        }
    }

    @staticmethod
    def get_config():
        return {
            "languages": LanguageConfig.SUPPORTED_LANGUAGES,
            "offline_pack": LanguageConfig.OFFLINE_RESPONSES
        }
