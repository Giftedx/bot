"""OSRS item database implementation."""

import json
import logging
from typing import Dict, Optional
from pathlib import Path

from ..models import Item


logger = logging.getLogger('ItemDatabase')


class ItemDatabase:
    """Manages the OSRS item database."""
    
    def __init__(self):
        self.items: Dict[str, Item] = {}
        self.items_by_name: Dict[str, Item] = {}
    
    async def load_items(self) -> None:
        """Load items from the JSON data file."""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'items.json'
            with open(data_path, 'r') as f:
                items_data = json.load(f)
            
            for item_data in items_data:
                item = Item(
                    id=item_data['id'],
                    name=item_data['name'],
                    description=item_data['description'],
                    category=item_data['category'],
                    tradeable=item_data.get('tradeable', True),
                    stackable=item_data.get('stackable', False),
                    equipable=item_data.get('equipable', False),
                    high_alch_value=item_data.get('high_alch_value', 0),
                    low_alch_value=item_data.get('low_alch_value', 0),
                    ge_price=item_data.get('ge_price')
                )
                
                self.items[item.id] = item
                self.items_by_name[item.name.lower()] = item
            
            logger.info(f'Loaded {len(self.items)} items')
        except Exception as e:
            logger.error(f'Failed to load items: {e}')
            # Initialize with some basic items if loading fails
            self._initialize_basic_items()
    
    def _initialize_basic_items(self) -> None:
        """Initialize a basic set of items if loading from file fails."""
        basic_items = [
            {
                'id': 'coins',
                'name': 'Coins',
                'description': 'Lovely money!',
                'category': 'Currency',
                'stackable': True
            },
            {
                'id': 'bronze_sword',
                'name': 'Bronze Sword',
                'description': 'A basic sword made of bronze.',
                'category': 'Weapons',
                'equipable': True
            },
            {
                'id': 'oak_logs',
                'name': 'Oak Logs',
                'description': 'Logs cut from an oak tree.',
                'category': 'Materials'
            }
        ]
        
        for item_data in basic_items:
            item = Item(**item_data)
            self.items[item.id] = item
            self.items_by_name[item.name.lower()] = item
        
        logger.info('Initialized basic items')
    
    def get_item(self, item_id: str) -> Optional[Item]:
        """Get an item by its ID."""
        return self.items.get(item_id)
    
    def get_item_by_name(self, name: str) -> Optional[Item]:
        """Get an item by its name (case-insensitive)."""
        return self.items_by_name.get(name.lower())
    
    def search_items(self, query: str) -> list[Item]:
        """Search for items by name (partial match)."""
        query = query.lower()
        return [
            item for item in self.items.values()
            if query in item.name.lower()
        ] 