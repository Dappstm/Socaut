import os
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    load_dotenv(override=True)
    outdir = Path(os.getenv("OUTPUT_DIR", "output"))
    outdir.mkdir(parents=True, exist_ok=True)
    Path("secrets").mkdir(exist_ok=True, parents=True)
    return outdir

def get_env(name: str, default: str = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val
