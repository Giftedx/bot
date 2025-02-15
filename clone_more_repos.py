import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and a stream handler
file_handler = logging.FileHandler('clone_repos.log')
stream_handler = logging.StreamHandler()

# Create a formatter and set it for the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def clone_repository(repo: str, base_dir: str) -> None:
    """Clone a repository into the specified directory."""
    owner = repo.split('/')[0]
    owner_dir = Path(base_dir) / owner
    owner_dir.mkdir(exist_ok=True)
    
    repo_url = f"https://github.com/{repo}.git"
    repo_path = owner_dir / repo.split('/')[1]
    
    if not repo_path.exists():
        logger.info(f"Cloning {repo}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
                check=True, capture_output=True, text=True
            )
            logger.info(f"Successfully cloned {repo}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {repo}: {e.stderr}")
    else:
        logger.info(f"Repository {repo} already exists, skipping...")


def main() -> None:
    """Clone additional OSRS-related repositories."""
    additional_repos = [
        # ... (rest of the code remains the same)
    
    for repo in additional_repos:
        clone_repository(repo, 'reference_repos')
    
    logger.info("\nFinished cloning additional repositories")import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and a stream handler
file_handler = logging.FileHandler('clone_repos.log')
stream_handler = logging.StreamHandler()

# Create a formatter and set it for the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def clone_repository(repo: str, base_dir: str) -> None:
    """Clone a repository into the specified directory."""
    owner = repo.split('/')[0]
    owner_dir = Path(base_dir) / owner
    owner_dir.mkdir(exist_ok=True)
    
    repo_url = f"https://github.com/{repo}.git"
    repo_path = owner_dir / repo.split('/')[1]
    
    if not repo_path.exists():
        logger.info(f"Cloning {repo}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
                check=True, capture_output=True, text=True
            )
            logger.info(f"Successfully cloned {repo}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {repo}: {e.stderr}")
    else:
        logger.info(f"Repository {repo} already exists, skipping...")


def main() -> None:
    """Clone additional OSRS-related repositories."""
    additional_repos = [
        # ... (rest of the code remains the same)
    
    for repo in additional_repos:
        clone_repository(repo, 'reference_repos')
    
    logger.info("\nFinished cloning additional repositories")import logging
import subprocess
from pathlib import Path

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and a stream handler
file_handler = logging.FileHandler('clone_repos.log')
stream_handler = logging.StreamHandler()

# Create a formatter and set it for the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def clone_repository(repo: str, base_dir: str) -> None:
    """Clone a repository into the specified directory."""
    owner = repo.split('/')[0]
    owner_dir = Path(base_dir) / owner
    owner_dir.mkdir(exist_ok=True)
    
    repo_url = f"https://github.com/{repo}.git"
    repo_path = owner_dir / repo.split('/')[1]
    
    if not repo_path.exists():
        logger.info(f"Cloning {repo}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
                check=True, capture_output=True, text=True
            )
            logger.info(f"Successfully cloned {repo}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {repo}: {e.stderr}")
    else:
        logger.info(f"Repository {repo} already exists, skipping...")


def main() -> None:
    """Clone additional OSRS-related repositories."""
    additional_repos = [
        # Core Game Mechanics and Data
        "osrsbox/osrsbox-db",  # Comprehensive OSRS item/monster/object database
        "osrsbox/osrsbox-api",  # Python API for OSRS data
        "0xNeffarion/osrs-cache-parser",  # Cache parser and data extractor
        "Joshua-F/cs2-scripts",  # Decompiled CS2 (RuneScript) scripts
        "Mark7625/osrs-data-converter",  # Data conversion tools
        "runelite/cache",  # Cache tools and definitions
        
        # Bot Development and Tools
        "runelite/runelite",  # The most popular OSRS client
        "open-osrs/runelite",  # Fork with additional features
        "runelite/plugin-hub",  # Collection of RuneLite plugins
        "Explv/osrs-pathfinder",  # Advanced pathfinding implementation
        "Explv/Explv.github.io",  # Web-based OSRS tools
        "Bushtit/osrs-tools",  # Collection of OSRS tools
        "Rune-Status/OSRS-Cache-Tools",  # More cache tools
        
        # API Implementations
        "gc/osrs-json-api",  # JSON API for OSRS
        "maxswa/osrs-json-hiscores",  # Hiscores API
        "attilathedud/osrs_bot_detector",  # Bot detection tools
        "rswiki-api/rswiki-api",  # Wiki API implementation
        
        # Private Server and Game Logic
        "Rune-Status/osrs-private-server",  # Server implementation
        "apollo-rsps/apollo",  # Another server implementation
        "Anadyr/OSRSe",  # Emulator project
        "OrN/osrs-private-server",  # Alternative server implementation
        
        # Community Tools and Resources
        "wise-old-man/wise-old-man",  # Player progress tracking
        "osrs-tracker/osrs-tracker",  # Progress tracking tools
        "osrs-tracker/osrs-tracker-api",  # API for progress tracking
        "molgoatkirby/osrs_public",  # Public tools and utilities
        
        # Additional Resources
        "runelite/rl-api",  # RuneLite API
        "runelite/runelite-discord-bot",  # Discord integration
        "osrsbox/osrsbox-tooltips",  # Item tooltips implementation
        "osrsbox/osrsbox-utils",  # Utility functions
        
        # Combat and PvM Tools
        "simonwong/osrs-dps",  # DPS calculator
        "weirdgloop/osrs-dps-calc",  # Another DPS calculator
        "0xNeffarion/osrs-calc",  # Various OSRS calculators
        
        # Data Analysis and Tracking
        "osrsbox/item-db-tools",  # Item database tools
        "osrsbox/osrsbox-data",  # Raw game data
        "osrsbox/osrsbox-db-data",  # Processed game data
        
        # Quest and Achievement Tools
        "osrsbox/osrs-quest-tool",  # Quest helper tools
        "wise-old-man/wise-old-man-discord-bot",  # Achievement tracking
        
        # Market and Economy
        "ge-tracker/api",  # GE price tracking
        "osbuddy/osbuddy-exchange",  # Exchange data
    ]
    
    for repo in additional_repos:
        clone_repository(repo, 'reference_repos')
    
    logger.info("\nFinished cloning additional repositories")


if __name__ == '__main__':
    main()"""Script to clone additional OSRS-related repositories."""
import subprocess
from pathlib import Path


def clone_repository(repo: str, base_dir: str) -> None:
    """Clone a repository into the specified directory."""
    owner = repo.split('/')[0]
    owner_dir = Path(base_dir) / owner
    owner_dir.mkdir(exist_ok=True)
    
    repo_url = f"https://github.com/{repo}.git"
    repo_path = owner_dir / repo.split('/')[1]
    
    if not repo_path.exists():
        print(f"Cloning {repo}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
                check=True, capture_output=True, text=True
            )
            print(f"Successfully cloned {repo}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {repo}: {e.stderr}")
    else:
        print(f"Repository {repo} already exists, skipping...")


def main() -> None:
    """Clone additional OSRS-related repositories."""
    additional_repos = [
        # Core Game Mechanics and Data
        "osrsbox/osrsbox-db",  # Comprehensive OSRS item/monster/object database
        "osrsbox/osrsbox-api",  # Python API for OSRS data
        "0xNeffarion/osrs-cache-parser",  # Cache parser and data extractor
        "Joshua-F/cs2-scripts",  # Decompiled CS2 (RuneScript) scripts
        "Mark7625/osrs-data-converter",  # Data conversion tools
        "runelite/cache",  # Cache tools and definitions
        
        # Bot Development and Tools
        "runelite/runelite",  # The most popular OSRS client
        "open-osrs/runelite",  # Fork with additional features
        "runelite/plugin-hub",  # Collection of RuneLite plugins
        "Explv/osrs-pathfinder",  # Advanced pathfinding implementation
        "Explv/Explv.github.io",  # Web-based OSRS tools
        "Bushtit/osrs-tools",  # Collection of OSRS tools
        "Rune-Status/OSRS-Cache-Tools",  # More cache tools
        
        # API Implementations
        "gc/osrs-json-api",  # JSON API for OSRS
        "maxswa/osrs-json-hiscores",  # Hiscores API
        "attilathedud/osrs_bot_detector",  # Bot detection tools
        "rswiki-api/rswiki-api",  # Wiki API implementation
        
        # Private Server and Game Logic
        "Rune-Status/osrs-private-server",  # Server implementation
        "apollo-rsps/apollo",  # Another server implementation
        "Anadyr/OSRSe",  # Emulator project
        "OrN/osrs-private-server",  # Alternative server implementation
        
        # Community Tools and Resources
        "wise-old-man/wise-old-man",  # Player progress tracking
        "osrs-tracker/osrs-tracker",  # Progress tracking tools
        "osrs-tracker/osrs-tracker-api",  # API for progress tracking
        "molgoatkirby/osrs_public",  # Public tools and utilities
        
        # Additional Resources
        "runelite/rl-api",  # RuneLite API
        "runelite/runelite-discord-bot",  # Discord integration
        "osrsbox/osrsbox-tooltips",  # Item tooltips implementation
        "osrsbox/osrsbox-utils",  # Utility functions
        
        # Combat and PvM Tools
        "simonwong/osrs-dps",  # DPS calculator
        "weirdgloop/osrs-dps-calc",  # Another DPS calculator
        "0xNeffarion/osrs-calc",  # Various OSRS calculators
        
        # Data Analysis and Tracking
        "osrsbox/item-db-tools",  # Item database tools
        "osrsbox/osrsbox-data",  # Raw game data
        "osrsbox/osrsbox-db-data",  # Processed game data
        
        # Quest and Achievement Tools
        "osrsbox/osrs-quest-tool",  # Quest helper tools
        "wise-old-man/wise-old-man-discord-bot",  # Achievement tracking
        
        # Market and Economy
        "ge-tracker/api",  # GE price tracking
        "osbuddy/osbuddy-exchange",  # Exchange data
    ]
    
    for repo in additional_repos:
        clone_repository(repo, 'reference_repos')
    
    print("\nFinished cloning additional repositories")


if __name__ == '__main__':
    main() 