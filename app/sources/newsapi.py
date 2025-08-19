import os, httpx, asyncio
from typing import List
from .base import BaseSource
from ..models import Article

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/everything"

class NewsAPISource(BaseSource):
    def __init__(self, name: str, params: dict):
        super().__init__(name)
        self.params = params

    async def fetch(self) -> List[Article]:
        key_env = self.params.get("api_key_env", "NEWSAPI_KEY")
        api_key = os.getenv(key_env)
        if not api_key:
            return []
        query = {k:v for k,v in self.params.items() if k not in ("api_key_env",)}
        headers = {"X-Api-Key": api_key}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(NEWSAPI_ENDPOINT, params=query, headers=headers)
            r.raise_for_status()
            data = r.json()
        out = []
        for item in data.get("articles", []):
            aid = item.get("url") or item.get("title","")[:80]
            out.append(Article(
                source=self.name,
                external_id=aid,
                title=item.get("title","").strip(),
                url=item.get("url"),
                body=(item.get("content") or item.get("description") or ""),
            ))
        return out
