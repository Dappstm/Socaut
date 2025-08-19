import os
from typing import Tuple
from .models import Script
from jinja2 import Template

# OpenAI SDK (chat completions)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

SCRIPT_TMPL = Template(
"""Write a 40-second TikTok/YouTube Shorts script in a hype, fast-paced tone.
Make it extremely clickbait (but add the phrase "(not clickbait)" in the title).
Structure it with:
1) HOOK (<= 10 words, shocking, pattern interrupt)
2) PAYOFF (explain the trick/tool in concrete steps)
3) CTA (follow/save/share).

Return JSON with keys: title, hook, body, cta.
Topic context:
{{ context }}
"""
)

def use_openai(context: str) -> Script:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        raise RuntimeError("OPENAI_API_KEY missing or openai SDK not installed.")
    client = OpenAI(api_key=api_key)
    prompt = SCRIPT_TMPL.render(context=context)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role":"system", "content":"You are a master shorts scriptwriter."},
            {"role":"user", "content": prompt}
        ],
        temperature=0.9,
    )
    text = resp.choices[0].message.content
    # Best-effort JSON extraction
    import json, re
    json_str = text.strip().strip('`')
    json_str = re.sub(r'^json\n', '', json_str, flags=re.I)
    try:
        data = json.loads(json_str)
    except Exception:
        # fallback split
        data = {"title":"", "hook":"", "body":text, "cta":""}
    full = f"{data.get('hook','')}. {data.get('body','')}. {data.get('cta','')}"
    return Script(
        title=(data.get("title") or "").strip(),
        hook=(data.get("hook") or "").strip(),
        body=(data.get("body") or "").strip(),
        cta=(data.get("cta") or "").strip(),
        full_text=full.strip()
    )

def generate_script(context: str) -> Script:
    # Extendable: add other providers (Ollama local, OpenRouter, etc.)
    return use_openai(context)
