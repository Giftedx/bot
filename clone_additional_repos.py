import os
import subprocess
from pathlib import Path

def clone_repository(repo: str, base_dir: str):
    """Clone a repository into the specified directory"""
    owner = repo.split('/')[0]
    owner_dir = Path(base_dir) / owner
    owner_dir.mkdir(exist_ok=True)
    
    repo_url = f"https://github.com/{repo}.git"
    repo_path = owner_dir / repo.split('/')[1]
    
    if not repo_path.exists():
        print(f"Cloning {repo}...")
        try:
            subprocess.run(['git', 'clone', '--depth', '1', repo_url, str(repo_path)], 
                         check=True, capture_output=True, text=True)
            print(f"Successfully cloned {repo}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {repo}: {e.stderr}")
    else:
        print(f"Repository {repo} already exists, skipping...")

def main():
    # Additional valuable OSRS-related repositories
    additional_repos = [
        # Core OSRS API Wrappers and Libraries
        "gc/osrs-json-api",
        "attilathedud/osrs_bot_detector",
        "runelite/runelite",
        "open-osrs/runelite",
        "runelite/plugin-hub",
        "osrsbox/osrsbox-api",
        "osrsbox/osrsbox-db",
        
        # OSRS Bot Frameworks and Tools
        "Bushtit/osrs-tools",
        "Explv/osrs-pathfinder",
        "Explv/Explv.github.io",
        "Rune-Status/OSRS-Cache-Tools",
        
        # Game Mechanics and Data
        "0xNeffarion/osrs-cache-parser",
        "Joshua-F/cs2-scripts",
        "Mark7625/osrs-data-converter",
        "runelite/cache",
        
        # Additional Bot Implementations
        "Zezima-sudo/osrs-bot",
        "Rune-Status/osrs-private-server",
        "rswiki-api/rswiki-api",
        "molgoatkirby/osrs_public",
        
        # Community Tools and Resources
        "wise-old-man/wise-old-man",
        "maxswa/osrs-json-hiscores",
        "osrs-tracker/osrs-tracker-api",
        "osrs-tracker/osrs-tracker",
    ]
    
    for repo in additional_repos:
        clone_repository(repo, 'reference_repos')

if __name__ == '__main__':
    main() 