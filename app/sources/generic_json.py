import os, httpx, asyncio, json
from typing import List
from .base import BaseSource
from ..models import Article

def env_expand(value: str) -> str:
    # allows ${ENV_NAME} placeholders inside config
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env = value[2:-1]
        return os.getenv(env, "")
    return value

class GenericJSONSource(BaseSource):
    def __init__(self, name: str, params: dict):
        super().__init__(name)
        self.params = params

    async def fetch(self) -> List[Article]:
        method = self.params.get("method", "GET").upper()
        url = self.params.get("url")
        headers = {k: env_expand(v) for k,v in (self.params.get("headers") or {}).items()}
        query = {k: env_expand(v) for k,v in (self.params.get("query") or {}).items()}
        body = self.params.get("body")
        async with httpx.AsyncClient(timeout=30, headers=headers) as client:
            if method == "POST":
                r = await client.post(url, params=query, json=body)
            else:
                r = await client.get(url, params=query)
            r.raise_for_status()
            data = r.json()

        # naive extraction; for complex JSON use your own adapter
        titles = []
        bodies = []
        urls = []

        # Try simple array
        if isinstance(data, list):
            for idx, item in enumerate(data):
                titles.append(str(item.get("title","item")))
                bodies.append(str(item.get("summary") or item.get("content") or ""))
                urls.append(str(item.get("url") or ""))
        else:
            # if config provided json_path_* arrays (flattened), we accept them as pre-extracted
            jp_t = self.params.get("json_path_title")
            jp_b = self.params.get("json_path_body")
            jp_u = self.params.get("json_path_url")
            if jp_t and jp_b:
                # Expect arrays at data[jp_t] if dotted? Keep simple for template purposes
                pass

            # Best-effort common structures
            items = data.get("items") or data.get("results") or data.get("data") or []
            if isinstance(items, dict): items = items.get("items", [])
            for item in items:
                titles.append(str(item.get("title","item")))
                bodies.append(str(item.get("summary") or item.get("content") or ""))
                urls.append(str(item.get("url") or ""))

        out = []
        for i, t in enumerate(titles):
            out.append(Article(
                source=self.name,
                external_id=(urls[i] or t[:80]),
                title=t,
                url=urls[i] if i < len(urls) else None,
                body=bodies[i] if i < len(bodies) else None,
            ))
        return out
