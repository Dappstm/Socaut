from typing import List
from .models import Article

class BaseSource:
    name: str
    def __init__(self, name: str):
        self.name = name

    async def fetch(self) -> List[Article]:
        raise NotImplementedError
