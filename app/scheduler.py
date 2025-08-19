import asyncio, yaml
from pathlib import Path
from typing import List
from .sources.newsapi import NewsAPISource
from .sources.reddit import RedditSource
from .sources.generic_json import GenericJSONSource
from .db import init_db, already_seen, mark_seen
from .models import Article

def build_sources(config_path: Path):
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    feeds = cfg.get("feeds", [])
    sources = []
    for f in feeds:
        if not f.get("enabled", True): continue
        t = f.get("type")
        name = f.get("name", t)
        params = f.get("params", {})
        if t == "newsapi":
            sources.append(NewsAPISource(name, params))
        elif t == "reddit":
            sources.append(RedditSource(name, params))
        elif t == "generic_json":
            sources.append(GenericJSONSource(name, params))
    return sources, cfg.get("poll_interval_seconds", 300)

async def poll_once(sources: List):
    all_new = []
    for s in sources:
        try:
            arts = await s.fetch()
            for a in arts:
                if not already_seen(a.source, a.external_id):
                    mark_seen(a.source, a.external_id, a.title)
                    all_new.append(a)
        except Exception as e:
            print(f"[WARN] Source {getattr(s,'name','?')} failed: {e}")
    return all_new

async def run_poll_loop(config_path: Path, on_articles):
    init_db()
    sources, interval = build_sources(config_path)
    print(f"Loaded {len(sources)} sources; polling every {interval}s")
    while True:
        new_articles = await poll_once(sources)
        if new_articles:
            await on_articles(new_articles)
        await asyncio.sleep(interval)
