"""
This file contains static data for the OSRS game simulation.
"""
from typing import Dict, List, Any

class FishingSpot:
    def __init__(self, name: str, required_level: int, fish_types: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.fish_types = fish_types
        self.tool_required = tool_required

FISHING_SPOTS = {
    'lumbridge': FishingSpot('Lumbridge Fishing Spot', 1, [
        {'name': 'Shrimp', 'xp': 10, 'level_req': 1, 'chance': 0.7},
        {'name': 'Anchovy', 'xp': 15, 'level_req': 5, 'chance': 0.3}
    ], 'Small Fishing Net'),
    'karamja': FishingSpot('Karamja Dock', 5, [
        {'name': 'Sardine', 'xp': 20, 'level_req': 5, 'chance': 0.6},
        {'name': 'Herring', 'xp': 30, 'level_req': 10, 'chance': 0.4}
    ], 'Fishing Rod'),
    'barbarian': FishingSpot('Barbarian Village', 20, [
        {'name': 'Pike', 'xp': 60, 'level_req': 25, 'chance': 0.5},
        {'name': 'Salmon', 'xp': 70, 'level_req': 30, 'chance': 0.5}
    ], 'Fly Fishing Rod')
}

COOKABLE_ITEMS = {
    'Shrimp': {'level_req': 1, 'xp': 30, 'burn_chance': 0.3},
    'Anchovy': {'level_req': 1, 'xp': 30, 'burn_chance': 0.3},
    'Sardine': {'level_req': 1, 'xp': 40, 'burn_chance': 0.3},
    'Herring': {'level_req': 5, 'xp': 50, 'burn_chance': 0.3},
    'Pike': {'level_req': 20, 'xp': 80, 'burn_chance': 0.3},
    'Salmon': {'level_req': 25, 'xp': 90, 'burn_chance': 0.3}
}

class MiningSpot:
    def __init__(self, name: str, required_level: int, ores: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.ores = ores
        self.tool_required = tool_required

MINING_SPOTS = {
    'lumbridge': MiningSpot('Lumbridge Swamp Mine', 1, [
        {'name': 'Copper ore', 'xp': 17.5, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2},
        {'name': 'Tin ore', 'xp': 17.5, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2}
    ], 'Bronze pickaxe'),
    'varrock': MiningSpot('Varrock East Mine', 15, [
        {'name': 'Iron ore', 'xp': 35, 'level_req': 15, 'chance': 0.6, 'respawn_time': 3},
        {'name': 'Coal', 'xp': 50, 'level_req': 30, 'chance': 0.4, 'respawn_time': 4}
    ], 'Steel pickaxe'),
    'mining_guild': MiningSpot('Mining Guild', 60, [
        {'name': 'Mithril ore', 'xp': 80, 'level_req': 55, 'chance': 0.4, 'respawn_time': 6},
        {'name': 'Adamantite ore', 'xp': 95, 'level_req': 70, 'chance': 0.2, 'respawn_time': 8}
    ], 'Rune pickaxe')
}

PICKAXES = {
    'Bronze pickaxe': {'level_req': 1, 'power': 1},
    'Iron pickaxe': {'level_req': 1, 'power': 2},
    'Steel pickaxe': {'level_req': 5, 'power': 3},
    'Mithril pickaxe': {'level_req': 20, 'power': 4},
    'Adamant pickaxe': {'level_req': 30, 'power': 5},
    'Rune pickaxe': {'level_req': 40, 'power': 6},
    'Dragon pickaxe': {'level_req': 60, 'power': 7}
}

class WoodcuttingSpot:
    def __init__(self, name: str, required_level: int, trees: List[Dict[str, Any]], tool_required: str):
        self.name = name
        self.required_level = required_level
        self.trees = trees
        self.tool_required = tool_required

WOODCUTTING_SPOTS = {
    'lumbridge': WoodcuttingSpot('Lumbridge Trees', 1, [
        {'name': 'Normal logs', 'xp': 25, 'level_req': 1, 'chance': 0.8, 'respawn_time': 2},
        {'name': 'Oak logs', 'xp': 37.5, 'level_req': 15, 'chance': 0.6, 'respawn_time': 3}
    ], 'Bronze axe'),
    'draynor': WoodcuttingSpot('Draynor Village', 15, [
        {'name': 'Willow logs', 'xp': 67.5, 'level_req': 30, 'chance': 0.5, 'respawn_time': 4},
        {'name': 'Maple logs', 'xp': 100, 'level_req': 45, 'chance': 0.4, 'respawn_time': 5}
    ], 'Steel axe'),
    'seers': WoodcuttingSpot("Seers' Village", 60, [
        {'name': 'Yew logs', 'xp': 175, 'level_req': 60, 'chance': 0.3, 'respawn_time': 7},
        {'name': 'Magic logs', 'xp': 250, 'level_req': 75, 'chance': 0.2, 'respawn_time': 10}
    ], 'Rune axe')
}

AXES = {
    'Bronze axe': {'level_req': 1, 'power': 1},
    'Iron axe': {'level_req': 1, 'power': 2},
    'Steel axe': {'level_req': 5, 'power': 3},
    'Mithril axe': {'level_req': 20, 'power': 4},
    'Adamant axe': {'level_req': 30, 'power': 5},
    'Rune axe': {'level_req': 40, 'power': 6},
    'Dragon axe': {'level_req': 60, 'power': 7}
}

CRAFTABLE_ITEMS = {
    'Bronze bar': {
        'level_req': 1,
        'xp': 12.5,
        'materials': {
            'Copper ore': 1,
            'Tin ore': 1
        }
    },
    'Iron bar': {
        'level_req': 15,
        'xp': 25,
        'materials': {
            'Iron ore': 1
        }
    },
    'Steel bar': {
        'level_req': 30,
        'xp': 37.5,
        'materials': {
            'Iron ore': 1,
            'Coal': 2
        }
    },
    'Mithril bar': {
        'level_req': 50,
        'xp': 50,
        'materials': {
            'Mithril ore': 1,
            'Coal': 4
        }
    },
    'Adamantite bar': {
        'level_req': 70,
        'xp': 75,
        'materials': {
            'Adamantite ore': 1,
            'Coal': 6
        }
    }
}

JEWELRY_ITEMS = {
    'Gold ring': {
        'level_req': 5,
        'xp': 15,
        'materials': {
            'Gold bar': 1
        }
    },
    'Sapphire ring': {
        'level_req': 20,
        'xp': 40,
        'materials': {
            'Gold bar': 1,
            'Sapphire': 1
        }
    },
    'Emerald ring': {
        'level_req': 27,
        'xp': 55,
        'materials': {
            'Gold bar': 1,
            'Emerald': 1
        }
    },
    'Ruby ring': {
        'level_req': 34,
        'xp': 70,
        'materials': {
            'Gold bar': 1,
            'Ruby': 1
        }
    },
    'Diamond ring': {
        'level_req': 43,
        'xp': 85,
        'materials': {
            'Gold bar': 1,
            'Diamond': 1
        }
    }
} 