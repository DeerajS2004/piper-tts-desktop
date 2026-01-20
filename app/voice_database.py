#!/usr/bin/env python3
"""
Piper TTS Voice Database
Contains information about available voices and download URLs
"""

VOICE_DATABASE = {
    "en_US": {
        "en_US-lessac-medium": {
            "name": "Lessac (US Female)",
            "language": "English (US)",
            "gender": "Female",
            "quality": "Medium",
            "size_mb": 42,
            "description": "Clear American English female voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-medium.onnx.json"
        },
        "en_US-ryan-medium": {
            "name": "Ryan (US Male)",
            "language": "English (US)",
            "gender": "Male",
            "quality": "Medium",
            "size_mb": 43,
            "description": "Clear American English male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-ryan-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-ryan-medium.onnx.json"
        },
        "en_US-ryan-high": {
            "name": "Ryan HQ (US Male)",
            "language": "English (US)",
            "gender": "Male",
            "quality": "High",
            "size_mb": 82,
            "description": "High quality American English male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-ryan-high.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-ryan-high.onnx.json"
        },
        "en_US-lessac-high": {
            "name": "Lessac HQ (US Female)",
            "language": "English (US)",
            "gender": "Female",
            "quality": "High",
            "size_mb": 81,
            "description": "High quality American English female voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-high.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US-lessac-high.onnx.json"
        }
    },
    "en_GB": {
        "en_GB-alan-medium": {
            "name": "Alan (British Male)",
            "language": "English (British)",
            "gender": "Male",
            "quality": "Medium",
            "size_mb": 44,
            "description": "British English male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB-alan-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB-alan-medium.onnx.json"
        },
        "en_GB-semaine-medium": {
            "name": "Semaine (British Female)",
            "language": "English (British)",
            "gender": "Female",
            "quality": "Medium",
            "size_mb": 43,
            "description": "British English female voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB-semaine-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB-semaine-medium.onnx.json"
        }
    },
    "es": {
        "es-davefx-medium": {
            "name": "DaveFX (Spanish)",
            "language": "Spanish",
            "gender": "Male",
            "quality": "Medium",
            "size_mb": 42,
            "description": "Spanish male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es-davefx-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es-davefx-medium.onnx.json"
        }
    },
    "de": {
        "de-thorsten-medium": {
            "name": "Thorsten (German)",
            "language": "German",
            "gender": "Male",
            "quality": "Medium",
            "size_mb": 42,
            "description": "German male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de-thorsten-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de-thorsten-medium.onnx.json"
        }
    },
    "fr": {
        "fr-gilles-low": {
            "name": "Gilles (French)",
            "language": "French",
            "gender": "Male",
            "quality": "Medium",
            "size_mb": 41,
            "description": "French male voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr-gilles-low.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr-gilles-low.onnx.json"
        }
    },
    "hi": {
        "hi-medium": {
            "name": "Hindi",
            "language": "Hindi",
            "gender": "Female",
            "quality": "Medium",
            "size_mb": 40,
            "description": "Hindi female voice",
            "download_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/hi/hi-medium.onnx",
            "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/hi/hi-medium.onnx.json"
        }
    }
}

def get_all_voices():
    """Get all voices from database"""
    all_voices = []
    for lang_code, voices in VOICE_DATABASE.items():
        for voice_id, voice_info in voices.items():
            all_voices.append({
                "id": voice_id,
                **voice_info
            })
    return all_voices

def get_voice_by_id(voice_id):
    """Get voice info by ID"""
    for lang_code, voices in VOICE_DATABASE.items():
        if voice_id in voices:
            return {"id": voice_id, **voices[voice_id]}
    return None

def get_voices_by_language(language_code):
    """Get all voices for a specific language"""
    return VOICE_DATABASE.get(language_code, {})

def search_voices(query=""):
    """Search voices by name, language, or description"""
    query = query.lower()
    results = []
    
    for lang_code, voices in VOICE_DATABASE.items():
        for voice_id, voice_info in voices.items():
            if (query in voice_info["name"].lower() or
                query in voice_info["language"].lower() or
                query in voice_info["description"].lower() or
                query in voice_info["gender"].lower() or
                query in voice_id.lower()):
                results.append({
                    "id": voice_id,
                    **voice_info
                })
    
    return results
