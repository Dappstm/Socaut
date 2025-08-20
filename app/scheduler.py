import asyncio, yaml
from pathlib import Path
from typing import List, Callable
from .sources.newsapi import NewsAPISource
from .db import init_db, already_seen, mark_seen
from .models import Article

def build_sources(config_path: Path):
    """
    Build only NewsAPI sources from config.yaml.
    NewsAPISource is special: it always produces 6 articles (2 per feed type).
    """
    cfg = yaml.safe_load(open(config_path, "r", encoding="utf-8"))
    feeds = cfg.get("feeds", [])
    sources = []
    for f in feeds:
        if not f.get("enabled", True):
            continue
        if f.get("type") == "newsapi":
            name = f.get("name", "newsapi")
            sources.append(NewsAPISource(name))
    return sources, cfg.get("poll_interval_seconds", 300)

async def poll_once(sources: List) -> List[Article]:
    """
    Fetch new articles from all sources and filter out already-seen ones.
    """
    all_new: List[Article] = []
    for s in sources:
        try:
            arts = await s.fetch()
            for a in arts:
                if not already_seen(a.source, a.external_id):
                    mark_seen(a.source, a.external_id, a.title)
                    all_new.append(a)
        except Exception as e:
            print(f"[WARN] Source {getattr(s, 'name', '?')} failed: {e}")
    return all_new

async def run_poll_loop(config_path: Path, on_articles: Callable[[List[Article]], None]):
    """
    Initialize DB, build sources, and poll them at interval forever.
    Each poll ensures NewsAPISource yields 6 fresh articles for video generation.
    """
    init_db()
    sources, interval = build_sources(config_path)
    print(f"Loaded {len(sources)} sources; polling every {interval}s")

    while True:
        new_articles = await poll_once(sources)
        if new_articles:
            print(f"[INFO] Got {len(new_articles)} new articles")
            await on_articles(new_articles)
        else:
            print("[INFO] No new articles this cycle")
        await asyncio.sleep(interval)