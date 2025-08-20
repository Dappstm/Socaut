import os, httpx, asyncio, random, datetime
from typing import List
from .base import BaseSource
from ..models import Article

API_KEY = os.getenv("NEWSAPI_KEY")

# Endpoint templates
ENDPOINTS = {
    "techcrunch": "https://newsapi.org/v2/top-headlines?sources=techcrunch",
    "us_business": "https://newsapi.org/v2/top-headlines?country=us&category=business",
    "wsj": "https://newsapi.org/v2/everything?domains=wsj.com",
}

class NewsAPISource(BaseSource):
    def __init__(self, name: str = "newsapi"):
        super().__init__(name)

    async def fetch(self) -> List[Article]:
        if not API_KEY:
            return []

        results: List[Article] = []
        async with httpx.AsyncClient(timeout=30) as client:
            # --- 1. TechCrunch (latest 2)
            tc_resp = await client.get(ENDPOINTS["techcrunch"], params={"apiKey": API_KEY})
            tc_data = tc_resp.json().get("articles", [])
            for item in tc_data[:2]:
                results.append(self._to_article("techcrunch", item))

            # --- 2. US Business (latest 2)
            bus_resp = await client.get(ENDPOINTS["us_business"], params={"apiKey": API_KEY})
            bus_data = bus_resp.json().get("articles", [])
            for item in bus_data[:2]:
                results.append(self._to_article("us_business", item))

            # --- 3. WSJ (random 2 from last 6 months)
            six_months_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).date().isoformat()
            wsj_resp = await client.get(ENDPOINTS["wsj"], params={
                "apiKey": API_KEY,
                "from": six_months_ago,
                "sortBy": "publishedAt",
                "pageSize": 50,  # grab a batch
            })
            wsj_data = wsj_resp.json().get("articles", [])
            if len(wsj_data) > 2:
                chosen = random.sample(wsj_data, 2)
            else:
                chosen = wsj_data
            for item in chosen:
                results.append(self._to_article("wsj", item))

        return results

    def _to_article(self, source: str, item: dict) -> Article:
        aid = item.get("url") or item.get("title", "")[:80]
        return Article(
            source=source,
            external_id=aid,
            title=(item.get("title") or "").strip(),
            url=item.get("url"),
            body=item.get("content") or item.get("description") or "",
        )