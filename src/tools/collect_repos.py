"""Script to collect and analyze OSRS-related repositories."""
import asyncio
import logging
import os
from typing import Dict, List
import git
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OSRS repositories to analyze
OSRS_REPOS = [
    "oldschoolgg/oldschoolbot",
    "oldschoolgg/oldschooljs",
    "runelite/runelite",
    "open-osrs/runelite",
    "osrsbox/osrsbox-db"
]

class RepoCollector:
    """Collect and analyze OSRS-related repositories."""
    
    def __init__(self, base_path: str = "repos"):
        """Initialize collector with base path for repos."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
    def collect_all(self) -> Dict[str, str]:
        """Collect all configured repositories."""
        results = {}
        for repo in OSRS_REPOS:
            try:
                path = self.clone_repo(repo)
                results[repo] = path
                logger.info(f"Successfully cloned {repo}")
            except Exception as e:
                logger.error(f"Failed to clone {repo}: {e}")
        return results
    
    def clone_repo(self, repo_name: str) -> str:
        """Clone a repository and return its path."""
        repo_path = self.base_path / repo_name.split('/')[-1]
        
        if repo_path.exists():
            logger.info(f"Repository {repo_name} already exists, pulling latest changes")
            repo = git.Repo(repo_path)
            origin = repo.remotes.origin
            origin.pull()
            return str(repo_path)
            
        logger.info(f"Cloning {repo_name}")
        git.Repo.clone_from(
            f"https://github.com/{repo_name}.git",
            str(repo_path)
        )
        return str(repo_path)
    
    def analyze_repo(self, repo_path: str) -> Dict:
        """Analyze a repository for relevant code patterns."""
        patterns = {
            'minigames': [],
            'combat': [],
            'skills': [],
            'items': [],
            'npcs': []
        }
        
        # Walk through repository
        for root, _, files in os.walk(repo_path):
            for file in files:
                if not file.endswith(('.py', '.js', '.java')):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        
                        # Look for relevant patterns
                        if 'minigame' in content:
                            patterns['minigames'].append(file_path)
                        if 'combat' in content or 'battle' in content:
                            patterns['combat'].append(file_path)
                        if 'skill' in content:
                            patterns['skills'].append(file_path)
                        if 'item' in content:
                            patterns['items'].append(file_path)
                        if 'npc' in content:
                            patterns['npcs'].append(file_path)
                except Exception as e:
                    logger.error(f"Failed to analyze {file_path}: {e}")
                    
        return patterns

def main():
    """Main entry point."""
    collector = RepoCollector()
    
    # Collect repositories
    repos = collector.collect_all()
    
    # Analyze repositories
    all_patterns = {}
    for repo_name, repo_path in repos.items():
        logger.info(f"Analyzing {repo_name}")
        patterns = collector.analyze_repo(repo_path)
        all_patterns[repo_name] = patterns
        
    # Log results
    for repo_name, patterns in all_patterns.items():
        logger.info(f"\nResults for {repo_name}:")
        for category, files in patterns.items():
            logger.info(f"{category}: {len(files)} relevant files")

if __name__ == "__main__":
    main() 