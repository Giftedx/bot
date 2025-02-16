import requests
import json
from pathlib import Path
from datetime import datetime

def fetch_world_data():
    """
    Fetches OSRS world data including:
    - World numbers
    - Player counts
    - World types (PVP, skill total, etc)
    - World locations
    - Activity focus
    """
    base_url = "https://oldschool.runescape.com/slu"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        worlds_data = response.json()
        
        # Process and structure the data
        processed_data = {
            'timestamp': datetime.now().isoformat(),
            'total_players': 0,
            'worlds': {}
        }
        
        for world in worlds_data['worlds']:
            world_number = world['id']
            processed_data['worlds'][world_number] = {
                'players': world['players'],
                'location': world['location'],
                'type': world['type'],
                'activity': world['activity'],
                'members': world['members']
            }
            processed_data['total_players'] += world['players']
        
        # Create data directory if it doesn't exist
        output_dir = Path("src/osrs/data/worlds")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the data
        with open(output_dir / "worlds_data.json", 'w') as f:
            json.dump(processed_data, f, indent=4)
            
        return processed_data
    
    except Exception as e:
        print(f"Error fetching world data: {str(e)}")
        return None

if __name__ == "__main__":
    fetch_world_data() 