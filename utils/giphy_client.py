import os
import logging
from typing import Dict, List, Optional
import giphy_client
from giphy_client.rest import ApiException

logger = logging.getLogger(__name__)


class GiphyClient:
    def __init__(self):
        try:
            api_key = os.getenv('GIPHY_API_KEY')
            if not api_key:
                raise ValueError(
                    "Giphy API key not found in environment variables"
                )
            
            self.api_instance = giphy_client.DefaultApi()
            self.api_key = api_key
        except Exception as e:
            logger.error(f"Failed to initialize Giphy client: {e}")
            raise

    async def search_gif(self, query: str, limit: int = 1) -> Optional[Dict]:
        """Search for a GIF on Giphy"""
        try:
            response = self.api_instance.gifs_search_get(
                self.api_key,
                query,
                limit=limit,
                rating='g'  # Keep it family friendly
            )
            if not response.data:
                return None

            gif = response.data[0]
            return {
                'url': gif.images.original.url,
                'title': gif.title,
                'id': gif.id,
                'preview': gif.images.fixed_height.url
            }
        except ApiException as e:
            logger.error(f"Giphy API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error searching GIF: {e}")
            return None

    async def trending_gifs(self, limit: int = 10) -> List[Dict]:
        """Get trending GIFs"""
        try:
            response = self.api_instance.gifs_trending_get(
                self.api_key,
                limit=limit,
                rating='g'
            )
            return [{
                'url': gif.images.original.url,
                'title': gif.title,
                'id': gif.id,
                'preview': gif.images.fixed_height.url
            } for gif in response.data]
        except ApiException as e:
            logger.error(f"Giphy API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting trending GIFs: {e}")
            return []

    async def random_gif(self, tag: Optional[str] = None) -> Optional[Dict]:
        """Get a random GIF, optionally with a tag"""
        try:
            response = self.api_instance.gifs_random_get(
                self.api_key,
                tag=tag,
                rating='g'
            )
            if not response.data:
                return None

            gif = response.data
            return {
                'url': gif.images.original.url,
                'title': gif.title,
                'id': gif.id,
                'preview': gif.images.fixed_height.url
            }
        except ApiException as e:
            logger.error(f"Giphy API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting random GIF: {e}")
            return None