from typing import List, Tuple
from pathlib import Path
import math, shutil, os

def naive_segments(text: str, audio_duration: float) -> List[Tuple[str, float, float]]:
    # Split into sentences by punctuation. Allocate time proportionally by length.
    import re
    parts = [p.strip() for p in re.split(r'[.!?\n]+', text) if p.strip()]
    if not parts:
        return []
    total_len = sum(len(p) for p in parts)
    t = 0.0
    segs = []
    for p in parts:
        dur = max(0.6, audio_duration * (len(p) / max(1, total_len)))
        segs.append((p, t, min(audio_duration, t + dur)))
        t += dur
        if t >= audio_duration: break
    if segs and segs[-1][2] < audio_duration:
        segs[-1] = (segs[-1][0], segs[-1][1], audio_duration)
    return segs

def whisper_segments(audio_path: Path) -> List[Tuple[str, float, float]]:
    try:
        import whisper
    except Exception:
        raise RuntimeError("openai-whisper not installed. Install to enable accurate caption timing.")
    model = whisper.load_model(os.getenv("WHISPER_MODEL","tiny"))
    result = model.transcribe(str(audio_path))
    segs = []
    for s in result.get("segments", []):
        segs.append((s.get("text","").strip(), float(s["start"]), float(s["end"])))
    return segs
