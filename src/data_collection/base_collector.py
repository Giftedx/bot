"""
Base collector class that implements common functionality for data collection.
This serves as the foundation for specific collectors like game data, Discord data, etc.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import aiohttp
import json
import os
from datetime import datetime, timedelta
import redis

from .config import COLLECTION_CONFIG, CACHE_CONFIG

logger = logging.getLogger(__name__)

class BaseCollector:
    """Base class for data collection implementations."""
    
    def __init__(self, name: str, cache_enabled: bool = True):
        self.name = name
        self.cache_enabled = cache_enabled
        self.config = COLLECTION_CONFIG
        self.session: Optional[aiohttp.ClientSession] = None
        self.redis: Optional[redis.Redis] = None
        
        if cache_enabled:
            self._setup_cache()
    
    def _setup_cache(self):
        """Initialize caching mechanisms."""
        try:
            self.redis = redis.Redis(
                host=CACHE_CONFIG['redis']['host'],
                port=CACHE_CONFIG['redis']['port'],
                db=CACHE_CONFIG['redis']['db']
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Redis cache initialized for {self.name}")
        except redis.ConnectionError:
            logger.warning(f"Redis connection failed for {self.name}, falling back to file cache")
            self.redis = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def fetch_data(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> Any:
        """Fetch data from a URL with retries and caching."""
        cache_key = f"{self.name}:{url}:{json.dumps(params or {})}"
        
        # Try cache first
        if self.cache_enabled:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Fetch from source
        session = await self._get_session()
        retries = 0
        
        while retries < self.config['max_retries']:
            try:
                async with session.get(url, params=params, headers=headers, timeout=self.config['timeout']) as response:
                    if response.status == 200:
                        data = await response.json()
                        if self.cache_enabled:
                            await self._save_to_cache(cache_key, data)
                        return data
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 5))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                    else:
                        response.raise_for_status()
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}, attempt {retries + 1}/{self.config['max_retries']}")
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
            
            retries += 1
            await asyncio.sleep(2 ** retries)  # Exponential backoff
        
        raise Exception(f"Failed to fetch data from {url} after {self.config['max_retries']} attempts")
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache."""
        if self.redis:
            try:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Redis cache error: {str(e)}")
        
        # Fallback to file cache
        cache_file = os.path.join(CACHE_CONFIG['file_cache']['base_path'], f"{key}.json")
        if os.path.exists(cache_file):
            try:
                modified_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
                if datetime.now() - modified_time < timedelta(seconds=self.config['cache_duration']):
                    with open(cache_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"File cache error: {str(e)}")
        
        return None
    
    async def _save_to_cache(self, key: str, data: Any):
        """Save data to cache."""
        if self.redis:
            try:
                self.redis.setex(
                    key,
                    self.config['cache_duration'],
                    json.dumps(data)
                )
                return
            except Exception as e:
                logger.error(f"Redis cache save error: {str(e)}")
        
        # Fallback to file cache
        try:
            cache_dir = CACHE_CONFIG['file_cache']['base_path']
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_file = os.path.join(cache_dir, f"{key}.json")
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"File cache save error: {str(e)}")
    
    async def process_batch(self, items: List[Any], batch_size: Optional[int] = None) -> List[Any]:
        """Process items in batches."""
        if batch_size is None:
            batch_size = self.config['batch_size']
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[self.process_item(item) for item in batch],
                return_exceptions=True
            )
            results.extend([r for r in batch_results if not isinstance(r, Exception)])
        return results
    
    async def process_item(self, item: Any) -> Any:
        """Process a single item. Override in subclasses."""
        raise NotImplementedError
    
    async def collect(self) -> Any:
        """Main collection method. Override in subclasses."""
        raise NotImplementedError
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        
        if self.redis:
            self.redis.close()
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.cleanup() 