import requests
import json
import os
from datetime import datetime
from pathlib import Path

def fetch_ge_data():
    """
    Fetches Grand Exchange data from the OSRS API
    Includes:
    - Latest prices
    - Price trends
    - Trading volume
    - Item details
    """
    base_url = "https://prices.runescape.wiki/api/v1/osrs"
    headers = {
        'User-Agent': 'OSRS Bot Data Fetcher - Development/Testing'
    }
    
    endpoints = {
        'latest': '/latest',
        'mapping': '/mapping',
        '5m': '/5m',
        '1h': '/1h',
        'timeseries': '/timeseries'
    }

    data = {}
    
    for endpoint_name, endpoint in endpoints.items():
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers)
            response.raise_for_status()
            data[endpoint_name] = response.json()
        except Exception as e:
            print(f"Error fetching {endpoint_name} data: {str(e)}")
            data[endpoint_name] = None

    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/ge")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "ge_data.json", 'w') as f:
        json.dump(data, f, indent=4)

    return data

def fetch_hiscores_data(username):
    """
    Fetches player hiscores data from the OSRS API
    """
    base_url = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"
    
    try:
        response = requests.get(f"{base_url}?player={username}")
        response.raise_for_status()
        
        # Parse the response
        skills_data = {}
        lines = response.text.split('\n')
        
        skill_names = [
            'overall', 'attack', 'defence', 'strength', 'hitpoints', 'ranged',
            'prayer', 'magic', 'cooking', 'woodcutting', 'fletching', 'fishing',
            'firemaking', 'crafting', 'smithing', 'mining', 'herblore', 'agility',
            'thieving', 'slayer', 'farming', 'runecraft', 'hunter', 'construction'
        ]
        
        for idx, skill in enumerate(skill_names):
            if idx < len(lines):
                rank, level, xp = lines[idx].split(',')
                skills_data[skill] = {
                    'rank': int(rank),
                    'level': int(level),
                    'xp': int(xp)
                }
        
        return skills_data
    except Exception as e:
        print(f"Error fetching hiscores data: {str(e)}")
        return None

if __name__ == "__main__":
    fetch_ge_data()
    # Example hiscores fetch:
    # fetch_hiscores_data("zezima") 