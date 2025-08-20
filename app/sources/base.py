from typing import List, Optional
from ..models import Article

class BaseSource:
    """
    Abstract base class for all content sources.
    Every source must implement `fetch()` to return a list of Article objects.
    """

    def __init__(self, name: str, max_articles: Optional[int] = None):
        self.name = name
        # Allows sources like NewsAPI to enforce a limit (e.g. 6 articles)
        self.max_articles = max_articles

    async def fetch(self) -> List[Article]:
        """
        Fetch new articles and return them as a list of Article objects.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement fetch()")