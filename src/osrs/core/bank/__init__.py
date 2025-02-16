"""OSRS bank implementation."""
from typing import Dict, List, Optional, Union, Any
from collections import defaultdict


class Bank:
    """Represents a bank of items and their quantities."""
    
    def __init__(self, items: Optional[Dict[str, int]] = None):
        """Initialize bank with optional items dictionary."""
        self._items: Dict[str, int] = defaultdict(int)
        if items:
            for item, qty in items.items():
                self.add(item, qty)

    def add(self, item: Union[str, int], quantity: int = 1) -> None:
        """Add quantity of item to bank."""
        if quantity <= 0:
            return
        
        item_id = str(item)
        self._items[item_id] += quantity

    def remove(self, item: Union[str, int], quantity: int = 1) -> bool:
        """
        Remove quantity of item from bank.
        Returns True if successful, False if insufficient quantity.
        """
        if quantity <= 0:
            return True
            
        item_id = str(item)
        if self._items[item_id] < quantity:
            return False
            
        self._items[item_id] -= quantity
        if self._items[item_id] == 0:
            del self._items[item_id]
        return True

    def has(self, item: Union[str, int], quantity: int = 1) -> bool:
        """Check if bank has at least quantity of item."""
        if quantity <= 0:
            return True
            
        item_id = str(item)
        return self._items[item_id] >= quantity

    def get(self, item: Union[str, int]) -> int:
        """Get quantity of item in bank."""
        item_id = str(item)
        return self._items[item_id]

    def items(self) -> Dict[str, int]:
        """Get dictionary of all items and their quantities."""
        return dict(self._items)

    def clear(self) -> None:
        """Remove all items from bank."""
        self._items.clear()

    def is_empty(self) -> bool:
        """Check if bank is empty."""
        return len(self._items) == 0

    def total_items(self) -> int:
        """Get total number of items (sum of all quantities)."""
        return sum(self._items.values())

    def unique_items(self) -> int:
        """Get number of unique items."""
        return len(self._items)

    def has_all(self, items: Dict[Union[str, int], int]) -> bool:
        """Check if bank has all items and quantities."""
        return all(self.has(item, qty) for item, qty in items.items())

    def remove_all(self, items: Dict[Union[str, int], int]) -> bool:
        """
        Remove all items and quantities.
        Returns True if successful, False if insufficient quantity of any item.
        """
        if not self.has_all(items):
            return False
            
        for item, qty in items.items():
            self.remove(item, qty)
        return True

    def add_all(self, items: Dict[Union[str, int], int]) -> None:
        """Add all items and quantities."""
        for item, qty in items.items():
            self.add(item, qty)

    def __eq__(self, other: Any) -> bool:
        """Check if two banks have identical contents."""
        if not isinstance(other, Bank):
            return False
        return self._items == other._items

    def __str__(self) -> str:
        """String representation of bank contents."""
        if not self._items:
            return "Empty bank"
        return ", ".join(f"{item}: {qty}" for item, qty in self._items.items())

    def __repr__(self) -> str:
        """Detailed string representation of bank."""
        return f"Bank({self._items})" 