import os, httpx, math, shutil
from pathlib import Path
from typing import List, Tuple

PIXABAY_IMG = "https://pixabay.com/api/"
PIXABAY_VID = "https://pixabay.com/api/videos/"

def pixabay_search(query: str, out_dir: Path, max_items: int = 5) -> Tuple[list, list]:
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        raise RuntimeError("PIXABAY_API_KEY missing")
    params = {"key": key, "q": query, "safesearch":"true", "per_page": max_items}
    out_dir.mkdir(parents=True, exist_ok=True)
    imgs, vids = [], []
    with httpx.Client(timeout=30) as client:
        ri = client.get(PIXABAY_IMG, params=params)
        if ri.status_code == 200:
            for hit in ri.json().get("hits", []):
                url = hit.get("largeImageURL") or hit.get("webformatURL")
                if url: imgs.append(url)
        rv = client.get(PIXABAY_VID, params=params)
        if rv.status_code == 200:
            for hit in rv.json().get("hits", []):
                v = hit.get("videos", {}).get("medium", {}).get("url") or hit.get("videos", {}).get("small", {}).get("url")
                if v: vids.append(v)
    # download
    img_paths, vid_paths = [], []
    for u in imgs[:max_items]:
        p = out_dir / os.path.basename(u.split("?")[0])
        try:
            with httpx.stream("GET", u, timeout=120) as r:
                r.raise_for_status()
                with open(p, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            img_paths.append(p)
        except Exception:
            continue
    for u in vids[:max_items]:
        p = out_dir / os.path.basename(u.split("?")[0])
        try:
            with httpx.stream("GET", u, timeout=300) as r:
                r.raise_for_status()
                with open(p, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            vid_paths.append(p)
        except Exception:
            continue
    return img_paths, vid_paths
