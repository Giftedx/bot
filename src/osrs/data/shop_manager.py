"""Shop data manager for handling shop-related data."""

from typing import Dict, List, Optional
from .data_manager import DataManager

class ShopManager(DataManager):
    """Manages shop data and stock."""
    
    def __init__(self, data_dir: str = "src/osrs/data"):
        """Initialize the shop manager.
        
        Args:
            data_dir: Directory containing data files.
        """
        super().__init__(data_dir)
        self.SHOP_FILE = "shops.json"
        
    def get_shop(self, shop_id: str) -> Dict:
        """Get shop data by ID.
        
        Args:
            shop_id: The ID of the shop.
            
        Returns:
            Dict containing shop data.
            
        Raises:
            KeyError: If shop doesn't exist.
        """
        return self.get_data(self.SHOP_FILE, shop_id)
        
    def get_shops_by_location(self, location: str) -> List[Dict]:
        """Get all shops in a specific location.
        
        Args:
            location: Location to search for shops.
            
        Returns:
            List of shop data dictionaries.
        """
        shops = []
        all_shops = self.get_data(self.SHOP_FILE)
        
        for shop_id, shop_data in all_shops.items():
            if location in shop_data.get("locations", []):
                shops.append(shop_data)
                
        return shops
        
    def get_item_price(self, shop_id: str, item_id: str) -> Optional[int]:
        """Get the price of an item in a specific shop.
        
        Args:
            shop_id: The ID of the shop.
            item_id: The ID of the item.
            
        Returns:
            The price of the item or None if not sold.
        """
        shop = self.get_shop(shop_id)
        return shop.get("stock", {}).get(item_id, {}).get("price")
        
    def get_item_stock(self, shop_id: str, item_id: str) -> Optional[int]:
        """Get the current stock of an item in a specific shop.
        
        Args:
            shop_id: The ID of the shop.
            item_id: The ID of the item.
            
        Returns:
            The current stock or None if not sold.
        """
        shop = self.get_shop(shop_id)
        return shop.get("stock", {}).get(item_id, {}).get("stock")
        
    def check_requirements(self, shop_id: str) -> Dict:
        """Get the requirements for accessing a shop.
        
        Args:
            shop_id: The ID of the shop.
            
        Returns:
            Dict of requirements or empty dict if none.
        """
        shop = self.get_shop(shop_id)
        return shop.get("requirements", {}) 