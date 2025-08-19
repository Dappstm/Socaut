import os, httpx, uuid, json
from pathlib import Path
from typing import Optional

ELEVEN_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

def synthesize_elevenlabs(text: str, voice_id: str, out_dir: Path) -> Path:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.7}
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"voice_{uuid.uuid4().hex}.mp3"
    with httpx.Client(timeout=120) as client:
        with client.stream("POST", ELEVEN_TTS_URL.format(voice_id=voice_id), headers=headers, json=payload) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
    return out_path
