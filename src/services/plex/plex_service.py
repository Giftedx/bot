import logging
from typing import List, Optional

from plexapi.server import PlexServer
from plexapi.media import Media

logger = logging.getLogger('PlexService')

class ServiceError(Exception):
    pass

class PlaybackResult:  # Placeholder, adapt
    def __init__(self, status:str, media_id:str):
        self.status = status
        self.title = "Placeholder Title" # Add to the addendum as required field

class BaseService: #Placeholder. I am unsure if needed at this stage, or there's some BaseService
    pass

class PlexService(BaseService):
    def __init__(self, config):
        self.base_url = config.plex_base_url  # Assuming configuration as dict
        self.token = config.plex_token # Same as before
        self.server: Optional[PlexServer] = None

    async def initialize(self) -> None:
        try:
            self.server = PlexServer(self.base_url, self.token)
            await self.health_check()
        except Exception as e:
            logger.error(f"Plex initialization failed: {str(e)}")
            raise ServiceError("Plex initialization failed")

    async def health_check(self):
      # Placeholder, assuming it exists or refactor from existing
      pass
    
    async def search_media(self, query: str) -> List[Media]:
        results = self.server.search(query)
        return [self._convert_to_media(r) for r in results]


    def _convert_to_media(self, r): #Placeholder, should implement according with search_media.
        return r
    
    async def play_media(self, media_id: str) -> PlaybackResult:
        client = self._get_active_client() # Missing and unknown
        media = self.server.fetchItem(int(media_id))
        client.playMedia(media)
        return PlaybackResult(status="playing", media_id=media_id)
      
    def _get_active_client(self): #Dummy
       pass