import os
import re
import subprocess
from pathlib import Path

def extract_repo_names(content):
    # Regular expression to match GitHub repository references
    repo_pattern = r'(?:github\.com/)?([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)'
    repos = []
    
    # Find all matches in the content
    for line in content.split('\n'):
        # Skip empty lines and headers
        if not line.strip() or line.startswith('#'):
            continue
            
        # Look for repository references in parentheses or after github.com
        matches = re.findall(repo_pattern, line)
        if matches:
            repos.extend(matches)
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(repos))

def clone_repositories(repos, base_dir):
    base_path = Path(base_dir)
    base_path.mkdir(exist_ok=True)
    
    for repo in repos:
        # Create category subdirectory based on the owner
        owner = repo.split('/')[0]
        owner_dir = base_path / owner
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
    # Read the repo-list.md file
    with open('notes/repo-list.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract repository names
    repos = extract_repo_names(content)
    
    # Clone repositories
    clone_repositories(repos, 'reference_repos')

if __name__ == '__main__':
    main() 