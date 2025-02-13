import sys
import discord
import os
from pathlib import Path

def main():
    venv_path = Path(sys.prefix)
    project_path = Path(__file__).parent
    
    print("=== Virtual Environment Test ===")
    print(f"Python version: {sys.version}")
    print(f"Virtual env location: {venv_path}")
    print(f"Project location: {project_path}")
    print(f"\nInstalled packages:")
    
    try:
        import pkg_resources
        for pkg in pkg_resources.working_set:
            print(f"- {pkg.key} {pkg.version}")
    except Exception as e:
        print(f"Error listing packages: {e}")

    # Test discord.py import
    print("\nTesting discord.py:")
    print(f"Discord.py version: {discord.__version__}")
    
    # Create test file to verify write permissions
    test_file = project_path / 'venv_test.txt'
    try:
        test_file.write_text('Virtual environment test successful!')
        print(f"\nCreated test file at: {test_file}")
    except Exception as e:
        print(f"Error writing test file: {e}")

if __name__ == "__main__":
    main()
