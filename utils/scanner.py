import os
import logging
from pathlib import Path
import sys

logger = logging.getLogger('Scanner')

def verify_project_structure(root_dir: str) -> None:
    """Verify and create necessary project directories"""
    required_dirs = ['cogs', 'utils', 'config', 'logs']
    root = Path(root_dir)
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"Created missing directory: {dir_path}")

def scan_codebase(root_dir: str) -> dict:
    """Scan entire codebase and return file info"""
    print("Starting scan...", flush=True)  # Debug print
    
    # First verify/create necessary directories
    verify_project_structure(root_dir)
    
    codebase = {
        'python_files': [],
        'directories': [],
        'cogs': [],
        'utils': [],
        'config': []
    }
    
    print(f"Scanning directory: {root_dir}", flush=True)  # Debug print
    
    try:
        for root, dirs, files in os.walk(root_dir):
            rel_path = os.path.relpath(root, root_dir)
            print(f"In directory: {rel_path}", flush=True)  # Debug print
            codebase['directories'].append(rel_path)
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    print(f"Found file: {filepath}", flush=True)  # Debug print
                    rel_filepath = os.path.relpath(filepath, root_dir)
                    codebase['python_files'].append(rel_filepath)
                    print(f"Found Python file: {rel_filepath}")
                    
                    if 'cogs' in filepath:
                        codebase['cogs'].append(rel_filepath)
                    elif 'utils' in filepath:
                        codebase['utils'].append(rel_filepath)
                    elif 'config' in filepath:
                        codebase['config'].append(rel_filepath)
    except Exception as e:
        print(f"Error during scan: {e}", flush=True)  # Debug print
        raise
        
    return codebase

def analyze_imports(filepath: str) -> list:
    """Analyze imports in a Python file"""
    imports = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line.strip())
    return imports
