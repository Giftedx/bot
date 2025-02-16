#!/usr/bin/env python3
"""
Repository cloning script for development.
Handles cloning of reference repositories and development dependencies.
"""
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("clone_repos.log")
    ]
)
logger = logging.getLogger(__name__)

class RepoManager:
    """Manages repository cloning and organization."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize repository manager."""
        self.base_dir = base_dir or Path("reference_repos")
        self.base_dir.mkdir(exist_ok=True)
        
    def clone_repository(self, repo: str, category: str) -> bool:
        """Clone a repository into a category directory."""
        try:
            # Extract owner and repo name
            if "/" not in repo:
                logger.warning(f"Invalid repository format: {repo}")
                return False
                
            owner, repo_name = repo.split("/", 1)
            
            # Create category directory
            category_dir = self.base_dir / category
            category_dir.mkdir(exist_ok=True)
            
            # Create owner directory
            owner_dir = category_dir / owner
            owner_dir.mkdir(exist_ok=True)
            
            # Full path for repository
            repo_dir = owner_dir / repo_name
            
            # Skip if already exists
            if repo_dir.exists():
                logger.info(f"Repository already exists: {repo}")
                return True
                
            # Construct repository URL
            if not repo.startswith(("http://", "https://", "git@")):
                repo_url = f"https://github.com/{repo}.git"
            else:
                repo_url = repo
                
            # Clone repository
            logger.info(f"Cloning {repo}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned {repo}")
                return True
            else:
                logger.error(f"Failed to clone {repo}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error cloning {repo}: {e}")
            return False
            
    def clone_repositories(self, repos: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clone multiple repositories organized by category."""
        results = {
            "success": [],
            "failed": []
        }
        
        total = sum(len(repos_list) for repos_list in repos.values())
        completed = 0
        
        for category, repo_list in repos.items():
            logger.info(f"\nCloning {category} repositories...")
            
            for repo in repo_list:
                completed += 1
                progress = (completed / total) * 100
                
                print(f"Progress: {progress:.1f}% ({completed}/{total})", end="\r")
                
                if self.clone_repository(repo, category):
                    results["success"].append(repo)
                else:
                    results["failed"].append(repo)
                    
        print()  # New line after progress
        return results

def get_reference_repos() -> Dict[str, List[str]]:
    """Get list of reference repositories to clone."""
    return {
        "core": [
            "runelite/runelite",
            "open-osrs/runelite",
            "runelite/plugin-hub",
            "osrsbox/osrsbox-db",
            "osrsbox/osrsbox-api"
        ],
        "tools": [
            "Explv/osrs-pathfinder",
            "Bushtit/osrs-tools",
            "Rune-Status/OSRS-Cache-Tools",
            "0xNeffarion/osrs-cache-parser"
        ],
        "api": [
            "gc/osrs-json-api",
            "maxswa/osrs-json-hiscores",
            "rswiki-api/rswiki-api"
        ],
        "data": [
            "osrsbox/item-db-tools",
            "osrsbox/osrsbox-data",
            "osrsbox/osrsbox-db-data"
        ],
        "community": [
            "wise-old-man/wise-old-man",
            "osrs-tracker/osrs-tracker",
            "osrs-tracker/osrs-tracker-api"
        ],
        "discord": [
            "runelite/runelite-discord-bot",
            "wise-old-man/wise-old-man-discord-bot"
        ]
    }

def main() -> None:
    """Main function for repository cloning."""
    print("Repository Cloning Tool\n")
    
    # Initialize repository manager
    manager = RepoManager()
    
    # Get repositories to clone
    repos = get_reference_repos()
    
    # Print cloning plan
    print("Repositories to clone:")
    for category, repo_list in repos.items():
        print(f"\n{category.title()}:")
        for repo in repo_list:
            print(f"  - {repo}")
            
    # Confirm with user
    response = input("\nProceed with cloning? (y/N) ").lower()
    if response != "y":
        print("Cloning cancelled.")
        sys.exit(0)
        
    # Clone repositories
    print("\nStarting clone operations...")
    results = manager.clone_repositories(repos)
    
    # Print results
    print("\nCloning Results:")
    print(f"Successfully cloned: {len(results['success'])}")
    print(f"Failed to clone: {len(results['failed'])}")
    
    if results["failed"]:
        print("\nFailed repositories:")
        for repo in results["failed"]:
            print(f"  - {repo}")
            
    print("\nCheck clone_repos.log for detailed information.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCloning cancelled.")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1) 