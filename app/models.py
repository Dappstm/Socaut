from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class Article(BaseModel):
    source: str
    external_id: str
    title: str
    url: Optional[str] = None
    body: Optional[str] = None
    published_at: Optional[datetime] = None
    topic: Optional[str] = None

class Script(BaseModel):
    title: str
    hook: str
    body: str
    cta: str
    full_text: str

class VideoJob(BaseModel):
    article: Article
    script: Script
    voice_id: str
    bgm_path: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    output_video_path: Optional[str] = None
    upload_youtube: bool = True
    upload_tiktok: bool = False
