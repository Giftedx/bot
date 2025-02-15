import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_requirements():
    """Install Python package requirements"""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        logger.error("requirements.txt not found")
        sys.exit(1)

    logger.info("Installing Python package requirements...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        logger.info("Successfully installed requirements")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e}")
        sys.exit(1)

def setup_data_directories():
    """Create necessary data directories"""
    dirs = [
        "data/cache/osrs",
        "data/osrs",
        "logs"
    ]
    
    for dir_path in dirs:
        path = Path(__file__).parent.parent / dir_path
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

def main():
    """Set up the development environment"""
    logger.info("Setting up development environment...")
    
    # Install requirements
    install_requirements()
    
    # Create directories
    setup_data_directories()
    
    logger.info("Development environment setup complete")

if __name__ == "__main__":
    main() 