import requests
import json
from pathlib import Path
import re

def fetch_clue_data():
    """
    Fetches OSRS clue scroll data from the Wiki including:
    - Clue types
    - Clue steps and solutions
    - Rewards
    - Requirements
    - Hot/Cold locations
    - Coordinate locations
    """
    api_url = "https://oldschool.runescape.wiki/api.php"
    
    clue_types = [
        "Beginner clue scroll",
        "Easy clue scroll",
        "Medium clue scroll",
        "Hard clue scroll",
        "Elite clue scroll",
        "Master clue scroll"
    ]
    
    clue_data = {}
    
    for clue_type in clue_types:
        params = {
            "action": "parse",
            "page": clue_type,
            "format": "json",
            "prop": "wikitext"
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'wikitext' in data['parse']:
                wikitext = data['parse']['wikitext']['*']
                
                # Extract clue information
                clue_info = {
                    'type': clue_type,
                    'steps': extract_steps(wikitext),
                    'rewards': extract_rewards(wikitext),
                    'requirements': extract_requirements(wikitext)
                }
                
                # If it's a hard+ clue, get coordinate clue locations
                if any(difficulty in clue_type.lower() for difficulty in ['hard', 'elite', 'master']):
                    clue_info['coordinate_locations'] = fetch_coordinate_locations()
                
                clue_data[clue_type] = clue_info
        
        except Exception as e:
            print(f"Error fetching data for {clue_type}: {str(e)}")
            continue
    
    # Fetch hot/cold locations separately
    try:
        clue_data['hot_cold_locations'] = fetch_hot_cold_locations()
    except Exception as e:
        print(f"Error fetching hot/cold locations: {str(e)}")
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/clues")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "clue_data.json", 'w') as f:
        json.dump(clue_data, f, indent=4)
    
    return clue_data

def extract_steps(wikitext):
    """Extract clue steps from wikitext"""
    steps = []
    # Find sections containing steps
    step_sections = re.findall(r'==\s*Steps\s*==\n(.*?)(?===|\Z)', wikitext, re.DOTALL)
    
    for section in step_sections:
        # Extract individual steps (usually in list format)
        step_matches = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|\Z)', section, re.DOTALL)
        steps.extend([step.strip() for step in step_matches])
    
    return steps

def extract_rewards(wikitext):
    """Extract rewards from wikitext"""
    rewards = []
    # Find reward tables
    reward_sections = re.findall(r'==\s*Rewards?\s*==\n(.*?)(?===|\Z)', wikitext, re.DOTALL)
    
    for section in reward_sections:
        # Extract items from reward tables
        reward_matches = re.findall(r'\|\s*Item\s*=\s*(.*?)(?=\||\})', section, re.DOTALL)
        rewards.extend([reward.strip() for reward in reward_matches])
    
    return rewards

def extract_requirements(wikitext):
    """Extract requirements from wikitext"""
    requirements = []
    # Find requirement sections
    req_sections = re.findall(r'==\s*Requirements?\s*==\n(.*?)(?===|\Z)', wikitext, re.DOTALL)
    
    for section in req_sections:
        # Extract requirements (usually in list format)
        req_matches = re.findall(r'\*\s*(.*?)(?=\n\*|\n\n|\Z)', section, re.DOTALL)
        requirements.extend([req.strip() for req in req_matches])
    
    return requirements

def fetch_coordinate_locations():
    """Fetch coordinate clue locations"""
    params = {
        "action": "parse",
        "page": "Coordinate clue",
        "format": "json",
        "prop": "wikitext"
    }
    
    try:
        response = requests.get("https://oldschool.runescape.wiki/api.php", params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'parse' in data and 'wikitext' in data['parse']:
            wikitext = data['parse']['wikitext']['*']
            
            # Extract coordinates and locations
            coord_matches = re.findall(r'\|\s*(\d{2}°\d{2}[NS]\s*\d{2}°\d{2}[EW])\s*\|\s*(.*?)(?=\||\})', wikitext, re.DOTALL)
            
            return [{
                'coordinates': coord.strip(),
                'location': loc.strip()
            } for coord, loc in coord_matches]
    
    except Exception as e:
        print(f"Error fetching coordinate locations: {str(e)}")
        return []

def fetch_hot_cold_locations():
    """Fetch hot/cold clue locations"""
    params = {
        "action": "parse",
        "page": "Hot Cold",
        "format": "json",
        "prop": "wikitext"
    }
    
    try:
        response = requests.get("https://oldschool.runescape.wiki/api.php", params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'parse' in data and 'wikitext' in data['parse']:
            wikitext = data['parse']['wikitext']['*']
            
            # Extract locations
            location_matches = re.findall(r'\|\s*Location\s*=\s*(.*?)(?=\||\})', wikitext, re.DOTALL)
            
            return [loc.strip() for loc in location_matches]
    
    except Exception as e:
        print(f"Error fetching hot/cold locations: {str(e)}")
        return []

if __name__ == "__main__":
    fetch_clue_data() 