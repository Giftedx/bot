import os
from pathlib import Path

def main():
    print("=== Bot Project Scanner ===")
    
    # Get current directory
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    
    print(f"Current dir: {current_dir}")
    print(f"Script dir: {script_dir}")
    
    # Check if utils exists
    utils_dir = script_dir / 'utils'
    if not utils_dir.exists():
        print("Creating utils directory")
        utils_dir.mkdir(parents=True)
    
    # Check basic project structure
    for dirname in ['cogs', 'logs', 'config']:
        dir_path = script_dir / dirname
        if not dir_path.exists():
            print(f"Creating {dirname} directory")
            dir_path.mkdir(parents=True)

    print("\nProject structure:")
    for entry in script_dir.iterdir():
        print(f"- {entry.name}")

if __name__ == "__main__":
    main()
