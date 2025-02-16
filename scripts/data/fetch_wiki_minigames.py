import requests
import json
from pathlib import Path
import mwparserfromhell
import re

def fetch_minigames_data():
    """
    Fetches OSRS minigame data from the Wiki including:
    - Minigame names and descriptions
    - Requirements
    - Rewards
    - Locations
    - Strategies
    """
    api_url = "https://oldschool.runescape.wiki/api.php"
    
    # List of known minigames to fetch
    minigames = [
        "Barbarian Assault",
        "Castle Wars",
        "Pest Control",
        "Fight Caves",
        "Inferno",
        "Volcanic Mine",
        "Tempoross",
        "Guardians of the Rift",
        "Chambers of Xeric",
        "Theatre of Blood",
        "Tombs of Amascut"
    ]
    
    minigames_data = {}
    
    for minigame in minigames:
        params = {
            "action": "parse",
            "page": minigame,
            "format": "json",
            "prop": "wikitext"
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'wikitext' in data['parse']:
                wikitext = data['parse']['wikitext']['*']
                parsed = mwparserfromhell.parse(wikitext)
                
                # Extract relevant information
                minigame_info = {
                    'name': minigame,
                    'requirements': extract_requirements(parsed),
                    'rewards': extract_rewards(parsed),
                    'location': extract_location(parsed),
                    'description': extract_description(parsed)
                }
                
                minigames_data[minigame] = minigame_info
        
        except Exception as e:
            print(f"Error fetching data for {minigame}: {str(e)}")
            continue
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/minigames")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "minigames_data.json", 'w') as f:
        json.dump(minigames_data, f, indent=4)
    
    return minigames_data

def extract_requirements(parsed_wikitext):
    """Extract requirements from parsed wikitext"""
    requirements = []
    for template in parsed_wikitext.filter_templates():
        if 'require' in template.name.lower():
            requirements.extend([param.value.strip_code() for param in template.params])
    return requirements

def extract_rewards(parsed_wikitext):
    """Extract rewards from parsed wikitext"""
    rewards = []
    for template in parsed_wikitext.filter_templates():
        if 'reward' in template.name.lower():
            rewards.extend([param.value.strip_code() for param in template.params])
    return rewards

def extract_location(parsed_wikitext):
    """Extract location from parsed wikitext"""
    for template in parsed_wikitext.filter_templates():
        if 'infobox' in template.name.lower():
            for param in template.params:
                if 'location' in param.name.lower():
                    return param.value.strip_code()
    return None

def extract_description(parsed_wikitext):
    """Extract description from parsed wikitext"""
    text = str(parsed_wikitext)
    # Find first paragraph after infobox
    match = re.search(r'\}\}(.*?)\n\n', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

if __name__ == "__main__":
    fetch_minigames_data() 