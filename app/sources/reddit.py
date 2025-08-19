import httpx, asyncio
from typing import List
from .base import BaseSource
from ..models import Article

REDDIT_URL_TMPL = "https://www.reddit.com/r/{sub}/{sort}.json"

class RedditSource(BaseSource):
    def __init__(self, name: str, params: dict):
        super().__init__(name)
        self.params = params

    async def fetch(self) -> List[Article]:
        subs = self.params.get("subreddits", [])
        sort = self.params.get("sort", "hot")
        limit = self.params.get("limit", 10)
        headers = {"User-Agent": "shorts-factory/1.0"}
        out = []
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            for sub in subs:
                r = await client.get(REDDIT_URL_TMPL.format(sub=sub, sort=sort), params={"limit": limit})
                if r.status_code != 200:
                    continue
                data = r.json()
                for child in data.get("data", {}).get("children", []):
                    d = child.get("data", {})
                    out.append(Article(
                        source=f"{self.name}:{sub}",
                        external_id=d.get("id"),
                        title=d.get("title",""),
                        url="https://www.reddit.com" + d.get("permalink",""),
                        body=d.get("selftext","") or d.get("url_overridden_by_dest","")
                    ))
        return out
