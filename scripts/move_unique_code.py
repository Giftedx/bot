import os
import shutil
from pathlib import Path

def ensure_dir(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)

def copy_dir_if_exists(src: Path, dest: Path, dir_name: str):
    """Copy directory if it exists and print status"""
    src_dir = src / dir_name
    dest_dir = dest / dir_name
    
    if src_dir.exists():
        print(f"Moving {dir_name} to {dest_dir}")
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(src_dir, dest_dir)
        return True
    return False

def main():
    # Create unique_osrs_code directory
    unique_code_dir = Path('unique_osrs_code')
    ensure_dir(unique_code_dir)
    
    # Create directories for organizing code
    src_dir = unique_code_dir / 'src'
    ensure_dir(src_dir)
    
    # Move core components
    copy_dir_if_exists(Path('temp_osrs/packages'), unique_code_dir, 'toolkit')
    copy_dir_if_exists(Path('temp_osrs/src'), src_dir, 'lib')
    copy_dir_if_exists(Path('temp_osrs/src'), src_dir, 'tasks')
    
    # Move data files
    data_src = Path('temp_osrs/data')
    data_dest = unique_code_dir / 'data'
    if data_src.exists():
        print(f"Moving data files to {data_dest}")
        if data_dest.exists():
            shutil.rmtree(data_dest)
        shutil.copytree(data_src, data_dest)
    
    # Create a README to document what we preserved
    readme_content = """# Unique OSRS Code

This directory contains unique code preserved from the temp_osrs directory:

## Directory Structure
- `src/` - Contains the source code
  - `lib/` - Core library implementations
  - `tasks/` - Task implementations for various game activities
- `toolkit/` - Utility package for OSRS bot development
- `data/` - Game data and configuration files

## Components

### Toolkit Package
A utility package containing various tools and helpers for OSRS bot development.
Original location: temp_osrs/packages/toolkit

### Lib Directory
Contains unique implementations and modifications, including:
- Custom bank image generation (bankImage.ts)
- Grand Exchange implementation (grandExchange.ts)
- Collection log system (collectionLogTask.ts)
- Custom minigames and activities
- Analytics and metrics tracking
- And more...

### Tasks Directory
Contains unique task implementations for various game activities.

### Data Directory
Contains important game data and configuration files:
- Combat achievements data
- Item data
- Command configurations
- And more...

Note: While some of this code may be based on oldschoolbot, it contains unique modifications and implementations that were worth preserving.

## Integration Instructions
To integrate this code with the main OSRS codebase:

1. The toolkit package should be kept as a separate package
2. Lib implementations should be merged with src/osrs/core/
3. Tasks should be integrated into appropriate locations in src/osrs/
4. Data files should be moved to src/osrs/data/
"""
    
    with open(unique_code_dir / 'README.md', 'w') as f:
        f.write(readme_content)
    
    print("Finished preserving unique code")
    
    # Now let's prepare for integration with existing OSRS codebase
    osrs_dir = Path('src/osrs')
    
    # Create necessary directories if they don't exist
    for dir_name in ['core', 'data', 'tasks']:
        ensure_dir(osrs_dir / dir_name)
    
    print("\nCode has been preserved and organized.")
    print("Ready to integrate with src/osrs/. Please review the preserved code before proceeding with integration.")

if __name__ == '__main__':
    main() 