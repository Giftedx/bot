import requests
import json
from pathlib import Path
import re

def fetch_item_stats():
    """
    Fetches OSRS item stats and bonuses from the Wiki including:
    - Equipment stats
    - Combat bonuses
    - Requirements
    - Special effects
    - Weight
    """
    api_url = "https://oldschool.runescape.wiki/api.php"
    
    # First get a list of all equipment items
    params = {
        "action": "parse",
        "page": "Equipment",
        "format": "json",
        "prop": "wikitext"
    }
    
    item_stats = {}
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'parse' in data and 'wikitext' in data['parse']:
            wikitext = data['parse']['wikitext']['*']
            
            # Extract equipment categories and items
            categories = extract_equipment_categories(wikitext)
            
            # For each item, fetch its stats
            for category, items in categories.items():
                for item in items:
                    item_stats[item] = fetch_single_item_stats(api_url, item)
    
    except Exception as e:
        print(f"Error fetching equipment list: {str(e)}")
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/items")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "item_stats.json", 'w') as f:
        json.dump(item_stats, f, indent=4)
    
    return item_stats

def extract_equipment_categories(wikitext):
    """Extract equipment categories and their items"""
    categories = {
        'weapons': [],
        'armour': [],
        'shields': [],
        'ammunition': [],
        'accessories': []
    }
    
    for category in categories.keys():
        # Find section for this category
        section_pattern = f"==\s*{category.title()}\s*==\n(.*?)(?===|\Z)"
        sections = re.findall(section_pattern, wikitext, re.DOTALL)
        
        if sections:
            # Extract items (usually in list format or tables)
            item_pattern = r'\|\s*item\s*=\s*(.*?)(?=\||\})'
            items = re.findall(item_pattern, sections[0], re.DOTALL)
            categories[category].extend([item.strip() for item in items if item.strip()])
    
    return categories

def fetch_single_item_stats(api_url, item_name):
    """Fetch stats for a single item"""
    params = {
        "action": "parse",
        "page": item_name,
        "format": "json",
        "prop": "wikitext"
    }
    
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'parse' in data and 'wikitext' in data['parse']:
            wikitext = data['parse']['wikitext']['*']
            
            # Extract all relevant stats
            stats = {
                'name': item_name,
                'combat_stats': extract_combat_stats(wikitext),
                'requirements': extract_item_requirements(wikitext),
                'special_effects': extract_special_effects(wikitext),
                'weight': extract_weight(wikitext)
            }
            
            return stats
    
    except Exception as e:
        print(f"Error fetching stats for {item_name}: {str(e)}")
        return None

def extract_combat_stats(wikitext):
    """Extract combat-related stats from item wikitext"""
    stats = {
        'attack_bonus': {},
        'defence_bonus': {},
        'other_bonuses': {}
    }
    
    # Attack bonuses
    attack_types = ['stab', 'slash', 'crush', 'magic', 'ranged']
    for attack_type in attack_types:
        pattern = f'\|\s*{attack_type}\s*=\s*([+-]?\d+)'
        matches = re.findall(pattern, wikitext, re.DOTALL)
        if matches:
            stats['attack_bonus'][attack_type] = int(matches[0])
    
    # Defence bonuses
    defence_types = ['stab', 'slash', 'crush', 'magic', 'ranged']
    for defence_type in defence_types:
        pattern = f'\|\s*{defence_type} def\s*=\s*([+-]?\d+)'
        matches = re.findall(pattern, wikitext, re.DOTALL)
        if matches:
            stats['defence_bonus'][defence_type] = int(matches[0])
    
    # Other bonuses
    other_stats = ['strength', 'ranged_strength', 'magic_damage', 'prayer']
    for stat in other_stats:
        pattern = f'\|\s*{stat}\s*=\s*([+-]?\d+)'
        matches = re.findall(pattern, wikitext, re.DOTALL)
        if matches:
            stats['other_bonuses'][stat] = int(matches[0])
    
    return stats

def extract_item_requirements(wikitext):
    """Extract item requirements from wikitext"""
    requirements = {}
    
    # Skill requirements
    skills = ['attack', 'strength', 'defence', 'ranged', 'magic', 'prayer']
    for skill in skills:
        pattern = f'\|\s*{skill} req\s*=\s*(\d+)'
        matches = re.findall(pattern, wikitext, re.DOTALL)
        if matches:
            requirements[skill] = int(matches[0])
    
    # Quest requirements
    quest_pattern = r'\|\s*quest\s*=\s*(.*?)(?=\||\})'
    quest_matches = re.findall(quest_pattern, wikitext, re.DOTALL)
    if quest_matches:
        requirements['quests'] = [quest.strip() for quest in quest_matches if quest.strip()]
    
    return requirements

def extract_special_effects(wikitext):
    """Extract special effects or attributes from wikitext"""
    effects = []
    
    # Look for special effect descriptions
    effect_pattern = r'\|\s*special\s*=\s*(.*?)(?=\||\})'
    effect_matches = re.findall(effect_pattern, wikitext, re.DOTALL)
    
    if effect_matches:
        effects.extend([effect.strip() for effect in effect_matches if effect.strip()])
    
    return effects

def extract_weight(wikitext):
    """Extract item weight from wikitext"""
    weight_pattern = r'\|\s*weight\s*=\s*([\d.]+)'
    weight_matches = re.findall(weight_pattern, wikitext, re.DOTALL)
    
    if weight_matches:
        return float(weight_matches[0])
    
    return None

if __name__ == "__main__":
    fetch_item_stats() 