import os
from pathlib import Path

def create_dir(path: Path):
    """Create directory and its __init__.py file"""
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / '__init__.py'
    if not init_file.exists():
        init_file.touch()

def main():
    base_dir = Path('src/osrs')
    
    # Main directories
    dirs = [
        'activities',
        'core',
        'data',
        'features',
        'models',
        'resources',
        'utils'
    ]
    
    # Core subdirectories
    core_dirs = [
        'bank',
        'combat',
        'economy',
        'skills'
    ]
    
    # Feature subdirectories
    feature_dirs = [
        'poh',
        'pets'
    ]
    
    # Create main directories
    for dir_name in dirs:
        create_dir(base_dir / dir_name)
    
    # Create core subdirectories
    for dir_name in core_dirs:
        create_dir(base_dir / 'core' / dir_name)
    
    # Create feature subdirectories
    for dir_name in feature_dirs:
        create_dir(base_dir / 'features' / dir_name)
    
    print("Directory structure created successfully")

if __name__ == '__main__':
    main() 