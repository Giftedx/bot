import requests
import json
from pathlib import Path
import re

def fetch_formula_data():
    """
    Fetches OSRS formulas and calculations from the Wiki including:
    - Combat level calculation
    - Combat stat calculations
    - Experience tables
    - Drop rate calculations
    - Prayer point calculations
    """
    api_url = "https://oldschool.runescape.wiki/api.php"
    
    formula_pages = {
        'combat': "Combat level",
        'experience': "Experience",
        'damage': "Maximum hit",
        'prayer': "Prayer",
        'drop_rates': "Drop rate",
        'hit_chance': "Hit chance"
    }
    
    formula_data = {}
    
    for category, page in formula_pages.items():
        params = {
            "action": "parse",
            "page": page,
            "format": "json",
            "prop": "wikitext"
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'wikitext' in data['parse']:
                wikitext = data['parse']['wikitext']['*']
                
                # Extract formulas based on category
                if category == 'combat':
                    formula_data[category] = extract_combat_formulas(wikitext)
                elif category == 'experience':
                    formula_data[category] = extract_experience_tables(wikitext)
                elif category == 'damage':
                    formula_data[category] = extract_damage_formulas(wikitext)
                elif category == 'prayer':
                    formula_data[category] = extract_prayer_formulas(wikitext)
                elif category == 'drop_rates':
                    formula_data[category] = extract_drop_rate_formulas(wikitext)
                elif category == 'hit_chance':
                    formula_data[category] = extract_hit_chance_formulas(wikitext)
        
        except Exception as e:
            print(f"Error fetching data for {page}: {str(e)}")
            continue
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/formulas")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "formula_data.json", 'w') as f:
        json.dump(formula_data, f, indent=4)
    
    return formula_data

def extract_combat_formulas(wikitext):
    """Extract combat level calculation formulas"""
    formulas = {
        'combat_level': {},
        'style_bonuses': {},
        'effective_levels': {}
    }
    
    # Extract main combat formula
    combat_pattern = r'\{\{Combat formula(.*?)\}\}'
    combat_matches = re.findall(combat_pattern, wikitext, re.DOTALL)
    
    if combat_matches:
        formulas['combat_level']['formula'] = combat_matches[0].strip()
    
    # Extract style bonuses
    style_pattern = r'\|\s*style\s*=\s*(.*?)(?=\||\})'
    style_matches = re.findall(style_pattern, wikitext, re.DOTALL)
    
    for match in style_matches:
        if '=' in match:
            style, bonus = match.split('=')
            formulas['style_bonuses'][style.strip()] = int(bonus.strip())
    
    return formulas

def extract_experience_tables(wikitext):
    """Extract experience tables and level calculations"""
    tables = {
        'level_to_xp': {},
        'xp_to_level': {},
        'virtual_levels': {}
    }
    
    # Extract level-to-xp formula
    level_pattern = r'\|\s*level\s*=\s*(\d+)\s*\|\s*xp\s*=\s*(\d+)'
    level_matches = re.findall(level_pattern, wikitext, re.DOTALL)
    
    for level, xp in level_matches:
        tables['level_to_xp'][int(level)] = int(xp)
    
    return tables

def extract_damage_formulas(wikitext):
    """Extract maximum hit and damage calculation formulas"""
    formulas = {
        'melee': {},
        'ranged': {},
        'magic': {}
    }
    
    # Extract damage formulas for each combat style
    for style in ['melee', 'ranged', 'magic']:
        pattern = f'\|\s*{style}\s*=\s*(.*?)(?=\||\}})'
        matches = re.findall(pattern, wikitext, re.DOTALL)
        
        if matches:
            formulas[style]['formula'] = matches[0].strip()
    
    return formulas

def extract_prayer_formulas(wikitext):
    """Extract prayer point and drain rate formulas"""
    formulas = {
        'drain_rate': {},
        'prayer_bonus': {},
        'restoration': {}
    }
    
    # Extract prayer formulas
    drain_pattern = r'\|\s*drain\s*=\s*(.*?)(?=\||\})'
    drain_matches = re.findall(drain_pattern, wikitext, re.DOTALL)
    
    if drain_matches:
        formulas['drain_rate']['formula'] = drain_matches[0].strip()
    
    return formulas

def extract_drop_rate_formulas(wikitext):
    """Extract drop rate calculation formulas"""
    formulas = {
        'standard_drops': {},
        'rare_drops': {},
        'ring_of_wealth': {}
    }
    
    # Extract drop rate formulas
    rate_pattern = r'\|\s*rate\s*=\s*(.*?)(?=\||\})'
    rate_matches = re.findall(rate_pattern, wikitext, re.DOTALL)
    
    if rate_matches:
        formulas['standard_drops']['formula'] = rate_matches[0].strip()
    
    return formulas

def extract_hit_chance_formulas(wikitext):
    """Extract accuracy and hit chance formulas"""
    formulas = {
        'accuracy': {},
        'defence': {},
        'hit_chance': {}
    }
    
    # Extract hit chance formulas
    chance_pattern = r'\|\s*chance\s*=\s*(.*?)(?=\||\})'
    chance_matches = re.findall(chance_pattern, wikitext, re.DOTALL)
    
    if chance_matches:
        formulas['hit_chance']['formula'] = chance_matches[0].strip()
    
    return formulas

if __name__ == "__main__":
    fetch_formula_data() 