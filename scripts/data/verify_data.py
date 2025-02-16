#!/usr/bin/env python3
"""
Script to verify the integrity of our data files and generate statistics.
This script checks for data consistency and generates a summary of what we've collected.
"""
import json
import logging
from pathlib import Path
import sys
from typing import Dict, Any, List, Set
from collections import Counter

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.append(str(src_path))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("verify_data.log")
    ]
)
logger = logging.getLogger(__name__)

class DataVerifier:
    """Verifies data integrity and generates statistics."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.data_dir = src_path / "data"
        self.data = {}
        self.stats = {}
        
    def load_data(self):
        """Load all data files."""
        data_files = [
            "items.json",
            "monsters.json",
            "npcs.json",
            "objects.json",
            "locations.json",
            "shops.json"
        ]
        
        for file_name in data_files:
            file_path = self.data_dir / file_name
            if file_path.exists():
                with open(file_path, "r") as f:
                    self.data[file_name] = json.load(f)
                logger.info(f"Loaded {len(self.data[file_name])} entries from {file_name}")
            else:
                logger.warning(f"File {file_name} not found")
                
    def verify_items(self):
        """Verify item data integrity."""
        items = self.data.get("items.json", {})
        stats = {
            "total_items": len(items),
            "equipable_items": 0,
            "stackable_items": 0,
            "tradeable_items": 0,
            "items_with_requirements": 0,
            "items_with_quest_requirements": 0,
            "items_by_type": Counter(),
            "items_with_stats": 0
        }
        
        for item_id, item in items.items():
            if item.get("equipable"):
                stats["equipable_items"] += 1
            if item.get("stackable"):
                stats["stackable_items"] += 1
            if item.get("tradeable"):
                stats["tradeable_items"] += 1
            if item.get("requirements"):
                stats["items_with_requirements"] += 1
            if item.get("quest_requirements"):
                stats["items_with_quest_requirements"] += 1
            if item.get("equipment_stats"):
                stats["items_with_stats"] += 1
            stats["items_by_type"][item.get("type", "UNKNOWN")] += 1
            
        self.stats["items"] = stats
        
    def verify_monsters(self):
        """Verify monster data integrity."""
        monsters = self.data.get("monsters.json", {})
        stats = {
            "total_monsters": len(monsters),
            "monsters_with_drops": 0,
            "monsters_with_locations": 0,
            "monsters_by_type": Counter(),
            "average_combat_level": 0,
            "monsters_with_special_attacks": 0
        }
        
        total_combat_level = 0
        combat_level_count = 0
        
        for monster_id, monster in monsters.items():
            if monster.get("drop_table"):
                stats["monsters_with_drops"] += 1
            if monster.get("locations"):
                stats["monsters_with_locations"] += 1
            if monster.get("special_attacks"):
                stats["monsters_with_special_attacks"] += 1
            stats["monsters_by_type"][monster.get("type", "UNKNOWN")] += 1
            
            combat_level = monster.get("combat_level")
            if combat_level:
                total_combat_level += combat_level
                combat_level_count += 1
                
        if combat_level_count > 0:
            stats["average_combat_level"] = total_combat_level / combat_level_count
            
        self.stats["monsters"] = stats
        
    def verify_objects(self):
        """Verify object data integrity."""
        objects = self.data.get("objects.json", {})
        stats = {
            "total_objects": len(objects),
            "objects_by_type": Counter(),
            "objects_with_requirements": 0,
            "objects_with_actions": 0
        }
        
        for object_id, object_data in objects.items():
            stats["objects_by_type"][object_data.get("object_type", "UNKNOWN")] += 1
            if object_data.get("requirements"):
                stats["objects_with_requirements"] += 1
            if object_data.get("actions"):
                stats["objects_with_actions"] += 1
                
        self.stats["objects"] = stats
        
    def verify_locations(self):
        """Verify location data integrity."""
        locations = self.data.get("locations.json", {})
        stats = {
            "total_locations": len(locations),
            "locations_by_type": Counter(),
            "locations_with_coordinates": 0,
            "locations_with_requirements": 0,
            "locations_with_features": 0
        }
        
        for location_id, location in locations.items():
            stats["locations_by_type"][location.get("location_type", "UNKNOWN")] += 1
            if location.get("coordinates"):
                stats["locations_with_coordinates"] += 1
            if location.get("requirements"):
                stats["locations_with_requirements"] += 1
            if location.get("features"):
                stats["locations_with_features"] += 1
                
        self.stats["locations"] = stats
        
    def verify_shops(self):
        """Verify shop data integrity."""
        shops = self.data.get("shops.json", {})
        stats = {
            "total_shops": len(shops),
            "shops_by_type": Counter(),
            "shops_with_stock": 0,
            "shops_with_requirements": 0
        }
        
        for shop_id, shop in shops.items():
            stats["shops_by_type"][shop.get("shop_type", "UNKNOWN")] += 1
            if shop.get("stock"):
                stats["shops_with_stock"] += 1
            if shop.get("requirements"):
                stats["shops_with_requirements"] += 1
                
        self.stats["shops"] = stats
        
    def verify_npcs(self):
        """Verify NPC data integrity."""
        npcs = self.data.get("npcs.json", {})
        stats = {
            "total_npcs": len(npcs),
            "npcs_by_type": Counter(),
            "npcs_with_dialogue": 0,
            "npcs_with_locations": 0
        }
        
        for npc_id, npc in npcs.items():
            stats["npcs_by_type"][npc.get("npc_type", "UNKNOWN")] += 1
            if npc.get("dialogue"):
                stats["npcs_with_dialogue"] += 1
            if npc.get("locations"):
                stats["npcs_with_locations"] += 1
                
        self.stats["npcs"] = stats
        
    def verify_cross_references(self):
        """Verify cross-references between different data types."""
        stats = {
            "item_references": {
                "in_monsters": 0,
                "in_shops": 0
            },
            "location_references": {
                "in_monsters": 0,
                "in_npcs": 0,
                "in_shops": 0
            },
            "npc_references": {
                "in_locations": 0
            }
        }
        
        # Check item references
        items = set(self.data.get("items.json", {}).keys())
        for monster in self.data.get("monsters.json", {}).values():
            drop_table = monster.get("drop_table", [])
            if isinstance(drop_table, list):
                for drop in drop_table:
                    if isinstance(drop, dict) and drop.get("item") in items:
                        stats["item_references"]["in_monsters"] += 1
                    elif isinstance(drop, str) and drop in items:
                        stats["item_references"]["in_monsters"] += 1
                        
        for shop in self.data.get("shops.json", {}).values():
            stock = shop.get("stock", [])
            if isinstance(stock, list):
                for item in stock:
                    if isinstance(item, dict) and item.get("id") in items:
                        stats["item_references"]["in_shops"] += 1
                    elif isinstance(item, str) and item in items:
                        stats["item_references"]["in_shops"] += 1
                        
        # Check location references
        locations = set(self.data.get("locations.json", {}).keys())
        for monster in self.data.get("monsters.json", {}).values():
            monster_locations = monster.get("locations", [])
            if isinstance(monster_locations, list):
                for location in monster_locations:
                    if isinstance(location, str) and location in locations:
                        stats["location_references"]["in_monsters"] += 1
                        
        for npc in self.data.get("npcs.json", {}).values():
            npc_locations = npc.get("locations", [])
            if isinstance(npc_locations, list):
                for location in npc_locations:
                    if isinstance(location, str) and location in locations:
                        stats["location_references"]["in_npcs"] += 1
                        
        for shop in self.data.get("shops.json", {}).values():
            shop_location = shop.get("location")
            if isinstance(shop_location, str) and shop_location in locations:
                stats["location_references"]["in_shops"] += 1
                
        # Check NPC references
        npcs = set(self.data.get("npcs.json", {}).keys())
        for location in self.data.get("locations.json", {}).values():
            location_npcs = location.get("npcs", [])
            if isinstance(location_npcs, list):
                for npc in location_npcs:
                    if isinstance(npc, str) and npc in npcs:
                        stats["npc_references"]["in_locations"] += 1
                        
        self.stats["cross_references"] = stats
        
    def print_stats(self):
        """Print statistics in a readable format."""
        print("\n=== OSRS Data Statistics ===\n")
        
        # Items
        print("Items:")
        print(f"  Total: {self.stats['items']['total_items']}")
        print(f"  Equipable: {self.stats['items']['equipable_items']}")
        print(f"  Stackable: {self.stats['items']['stackable_items']}")
        print(f"  Tradeable: {self.stats['items']['tradeable_items']}")
        print(f"  With Requirements: {self.stats['items']['items_with_requirements']}")
        print(f"  With Quest Requirements: {self.stats['items']['items_with_quest_requirements']}")
        print(f"  With Equipment Stats: {self.stats['items']['items_with_stats']}")
        print("\n  Types:")
        for type_name, count in self.stats['items']['items_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # Monsters
        print("\nMonsters:")
        print(f"  Total: {self.stats['monsters']['total_monsters']}")
        print(f"  With Drops: {self.stats['monsters']['monsters_with_drops']}")
        print(f"  With Locations: {self.stats['monsters']['monsters_with_locations']}")
        print(f"  With Special Attacks: {self.stats['monsters']['monsters_with_special_attacks']}")
        print(f"  Average Combat Level: {self.stats['monsters']['average_combat_level']:.1f}")
        print("\n  Types:")
        for type_name, count in self.stats['monsters']['monsters_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # Objects
        print("\nObjects:")
        print(f"  Total: {self.stats['objects']['total_objects']}")
        print(f"  With Requirements: {self.stats['objects']['objects_with_requirements']}")
        print(f"  With Actions: {self.stats['objects']['objects_with_actions']}")
        print("\n  Types:")
        for type_name, count in self.stats['objects']['objects_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # Locations
        print("\nLocations:")
        print(f"  Total: {self.stats['locations']['total_locations']}")
        print(f"  With Coordinates: {self.stats['locations']['locations_with_coordinates']}")
        print(f"  With Requirements: {self.stats['locations']['locations_with_requirements']}")
        print(f"  With Features: {self.stats['locations']['locations_with_features']}")
        print("\n  Types:")
        for type_name, count in self.stats['locations']['locations_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # Shops
        print("\nShops:")
        print(f"  Total: {self.stats['shops']['total_shops']}")
        print(f"  With Stock: {self.stats['shops']['shops_with_stock']}")
        print(f"  With Requirements: {self.stats['shops']['shops_with_requirements']}")
        print("\n  Types:")
        for type_name, count in self.stats['shops']['shops_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # NPCs
        print("\nNPCs:")
        print(f"  Total: {self.stats['npcs']['total_npcs']}")
        print(f"  With Dialogue: {self.stats['npcs']['npcs_with_dialogue']}")
        print(f"  With Locations: {self.stats['npcs']['npcs_with_locations']}")
        print("\n  Types:")
        for type_name, count in self.stats['npcs']['npcs_by_type'].most_common():
            print(f"    {type_name}: {count}")
            
        # Cross References
        print("\nCross References:")
        print("  Item References:")
        print(f"    In Monster Drops: {self.stats['cross_references']['item_references']['in_monsters']}")
        print(f"    In Shop Stock: {self.stats['cross_references']['item_references']['in_shops']}")
        print("  Location References:")
        print(f"    In Monster Spawns: {self.stats['cross_references']['location_references']['in_monsters']}")
        print(f"    In NPC Locations: {self.stats['cross_references']['location_references']['in_npcs']}")
        print(f"    In Shop Locations: {self.stats['cross_references']['location_references']['in_shops']}")
        print("  NPC References:")
        print(f"    In Location NPCs: {self.stats['cross_references']['npc_references']['in_locations']}")
        
    def verify_all(self):
        """Run all verifications."""
        self.load_data()
        self.verify_items()
        self.verify_monsters()
        self.verify_objects()
        self.verify_locations()
        self.verify_shops()
        self.verify_npcs()
        self.verify_cross_references()
        self.print_stats()

def main():
    """Main function to verify data."""
    try:
        verifier = DataVerifier()
        verifier.verify_all()
        
    except Exception as e:
        logger.error(f"Error verifying data: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 