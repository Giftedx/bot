import requests
import json
from pathlib import Path
import re

def fetch_achievement_diary_data():
    """
    Fetches OSRS Achievement Diary data from the Wiki including:
    - Diary areas
    - Task lists and requirements
    - Rewards
    - Difficulty levels
    """
    api_url = "https://oldschool.runescape.wiki/api.php"
    
    diary_areas = [
        "Ardougne Diary",
        "Desert Diary",
        "Falador Diary",
        "Fremennik Diary",
        "Kandarin Diary",
        "Karamja Diary",
        "Kourend & Kebos Diary",
        "Lumbridge & Draynor Diary",
        "Morytania Diary",
        "Varrock Diary",
        "Western Provinces Diary",
        "Wilderness Diary"
    ]
    
    diary_data = {}
    
    for area in diary_areas:
        params = {
            "action": "parse",
            "page": area,
            "format": "json",
            "prop": "wikitext"
        }
        
        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'wikitext' in data['parse']:
                wikitext = data['parse']['wikitext']['*']
                
                # Extract diary information
                diary_info = {
                    'area': area,
                    'difficulties': extract_difficulties(wikitext),
                    'tasks': extract_tasks(wikitext),
                    'rewards': extract_rewards(wikitext)
                }
                
                diary_data[area] = diary_info
        
        except Exception as e:
            print(f"Error fetching data for {area}: {str(e)}")
            continue
    
    # Create data directory if it doesn't exist
    output_dir = Path("src/osrs/data/achievement_diaries")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the data
    with open(output_dir / "achievement_diary_data.json", 'w') as f:
        json.dump(diary_data, f, indent=4)
    
    return diary_data

def extract_difficulties(wikitext):
    """Extract difficulty levels and their requirements"""
    difficulties = {}
    difficulty_levels = ['Easy', 'Medium', 'Hard', 'Elite']
    
    for level in difficulty_levels:
        # Find section for this difficulty
        section_pattern = f"==\s*{level}\s*==\n(.*?)(?===|\Z)"
        sections = re.findall(section_pattern, wikitext, re.DOTALL)
        
        if sections:
            # Extract requirements
            req_pattern = r'\|\s*requirement\s*=\s*(.*?)(?=\||\})'
            requirements = re.findall(req_pattern, sections[0], re.DOTALL)
            
            difficulties[level] = {
                'requirements': [req.strip() for req in requirements if req.strip()]
            }
    
    return difficulties

def extract_tasks(wikitext):
    """Extract tasks for each difficulty level"""
    tasks = {}
    difficulty_levels = ['Easy', 'Medium', 'Hard', 'Elite']
    
    for level in difficulty_levels:
        # Find section for this difficulty
        section_pattern = f"==\s*{level}\s*==\n(.*?)(?===|\Z)"
        sections = re.findall(section_pattern, wikitext, re.DOTALL)
        
        if sections:
            # Extract tasks
            task_pattern = r'\|\s*task\s*=\s*(.*?)(?=\||\})'
            task_matches = re.findall(task_pattern, sections[0], re.DOTALL)
            
            tasks[level] = [task.strip() for task in task_matches if task.strip()]
    
    return tasks

def extract_rewards(wikitext):
    """Extract rewards for each difficulty level"""
    rewards = {}
    difficulty_levels = ['Easy', 'Medium', 'Hard', 'Elite']
    
    for level in difficulty_levels:
        # Find reward section for this difficulty
        section_pattern = f"==\s*{level}.*?Rewards?\s*==\n(.*?)(?===|\Z)"
        sections = re.findall(section_pattern, wikitext, re.DOTALL)
        
        if sections:
            # Extract rewards (usually in list format)
            reward_pattern = r'\*\s*(.*?)(?=\n\*|\n\n|\Z)'
            reward_matches = re.findall(reward_pattern, sections[0], re.DOTALL)
            
            rewards[level] = [reward.strip() for reward in reward_matches if reward.strip()]
    
    return rewards

if __name__ == "__main__":
    fetch_achievement_diary_data() 