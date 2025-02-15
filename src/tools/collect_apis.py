"""Script to collect data from OSRS-related APIs."""
import asyncio
import logging
import json
from typing import Dict, List, Optional
import aiohttp
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API endpoints
OSRS_APIS = {
    'wiki': {
        'base_url': 'https://api.weirdgloop.org/exchange/history/osrs/latest',
        'endpoints': {
            'all_items': '',  # Empty string means use base_url as is
            'item_detail': '/item/',  # Append item ID
            'item_history': '/history/'  # Append item ID
        }
    },
    'prices': {
        'base_url': 'https://prices.runescape.wiki/api/v1/osrs',
        'endpoints': {
            'latest': '/latest',
            'mapping': '/mapping',
            '5m': '/5m',
            '1h': '/1h'
        }
    },
    'ge': {
        'base_url': 'https://secure.runescape.com/m=itemdb_oldschool/api',
        'endpoints': {
            'categories': '/catalogue/category.json',
            'items': '/catalogue/items.json?category={category_id}&alpha={letter}&page={page}'
        }
    }
}

class APICollector:
    """Collect data from OSRS-related APIs."""
    
    def __init__(self, output_path: str = "src/osrs/data/api"):
        """Initialize collector with output path."""
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Create aiohttp session."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            
    async def collect_all(self):
        """Collect data from all configured APIs."""
        async with self:
            for api_name, api_config in OSRS_APIS.items():
                logger.info(f"Collecting data from {api_name} API")
                try:
                    await self.collect_api_data(api_name, api_config)
                except Exception as e:
                    logger.error(f"Failed to collect data from {api_name}: {e}")
                    
    async def collect_api_data(self, api_name: str, api_config: Dict):
        """Collect data from a specific API."""
        base_url = api_config['base_url']
        
        for endpoint_name, endpoint_path in api_config['endpoints'].items():
            # Special handling for GE API
            if api_name == 'ge' and endpoint_name == 'items':
                await self.collect_ge_items()
                continue
                
            url = f"{base_url}{endpoint_path}"
            logger.info(f"Fetching {endpoint_name} from {api_name}")
            
            try:
                headers = {
                    'User-Agent': 'OSRS Discord Bot - Data Collection'
                }
                
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.save_data(api_name, endpoint_name, data)
                    else:
                        logger.error(
                            f"Failed to fetch {endpoint_name} from {api_name}: "
                            f"Status {response.status}"
                        )
            except Exception as e:
                logger.error(
                    f"Error fetching {endpoint_name} from {api_name}: {e}"
                )
                
    async def collect_ge_items(self):
        """Collect items from the GE API."""
        # First get categories
        url = f"{OSRS_APIS['ge']['base_url']}{OSRS_APIS['ge']['endpoints']['categories']}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    categories = await response.json()
                    self.save_data('ge', 'categories', categories)
                    
                    # Now collect items from each category
                    for category in categories['alpha']:
                        category_id = category['letter']
                        for letter in 'abcdefghijklmnopqrstuvwxyz':
                            page = 1
                            while True:
                                items_url = f"{OSRS_APIS['ge']['base_url']}/catalogue/items.json?category={category_id}&alpha={letter}&page={page}"
                                
                                async with self.session.get(items_url) as items_response:
                                    if items_response.status == 200:
                                        items = await items_response.json()
                                        if not items.get('items'):
                                            break
                                            
                                        self.save_data(
                                            'ge', 
                                            f'items_cat{category_id}_letter{letter}_page{page}',
                                            items
                                        )
                                        page += 1
                                    else:
                                        break
                else:
                    logger.error(f"Failed to fetch GE categories: Status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching GE data: {e}")
                
    def save_data(self, api_name: str, endpoint_name: str, data: Dict):
        """Save collected data to file."""
        output_file = self.output_path / f"{api_name}_{endpoint_name}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {api_name} {endpoint_name} data to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save {api_name} {endpoint_name} data: {e}")

async def main():
    """Main entry point."""
    collector = APICollector()
    await collector.collect_all()

if __name__ == "__main__":
    asyncio.run(main()) 