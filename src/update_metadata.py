import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import re
from github import Github
from github.Repository import Repository as GithubRepo
from data.repositories import Repository, RepositoryManager
from rich.console import Console
from rich.progress import Progress
import time

console = Console()

def extract_repo_info(url: str) -> Optional[tuple[str, str]]:
    """Extract owner and repo name from GitHub URL."""
    patterns = [
        r'github\.com/([^/]+)/([^/]+)',  # Regular GitHub URL
        r'([^/]+)/([^/]+)'               # Owner/repo format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None

def get_github_metadata(repo: Repository, github_client: Github) -> Dict:
    """Fetch metadata for a repository from GitHub."""
    if not repo.url:
        return {}
        
    repo_info = extract_repo_info(repo.url)
    if not repo_info:
        return {}
        
    owner, repo_name = repo_info
    
    try:
        github_repo: GithubRepo = github_client.get_repo(f"{owner}/{repo_name}")
        
        return {
            'stars': github_repo.stargazers_count,
            'language': github_repo.language,
            'last_updated': github_repo.updated_at,
            'description': github_repo.description or repo.description,
            'tags': [topic for topic in github_repo.get_topics()],
            'metadata': {
                'forks': github_repo.forks_count,
                'open_issues': github_repo.open_issues_count,
                'watchers': github_repo.watchers_count,
                'default_branch': github_repo.default_branch,
                'license': github_repo.license.name if github_repo.license else None,
                'created_at': github_repo.created_at.isoformat() if github_repo.created_at else None,
            }
        }
    except Exception as e:
        console.print(f"[yellow]Warning: Failed to fetch metadata for {owner}/{repo_name}: {str(e)}[/yellow]")
        return {}

def update_repository_metadata(token: Optional[str] = None):
    """Update metadata for all repositories with GitHub URLs."""
    # Load repositories
    repo_file = Path('src/data/repositories.yaml')
    if not repo_file.exists():
        console.print("[red]Repository data not found. Please run parse_repos.py first.[/red]")
        return
        
    manager = RepositoryManager.from_yaml(repo_file)
    
    # Initialize GitHub client
    github_client = Github(token) if token else Github()
    
    total_repos = sum(len(repos) for repos in manager.categories.values())
    updated_count = 0
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Updating repository metadata...", total=total_repos)
        
        for category, repos in manager.categories.items():
            for repo in repos:
                if repo.url and 'github.com' in repo.url:
                    metadata = get_github_metadata(repo, github_client)
                    if metadata:
                        # Update repository with new metadata
                        repo.stars = metadata.get('stars', repo.stars)
                        repo.language = metadata.get('language', repo.language)
                        repo.last_updated = metadata.get('last_updated', repo.last_updated)
                        repo.description = metadata.get('description', repo.description)
                        repo.tags = metadata.get('tags', repo.tags)
                        repo.metadata.update(metadata.get('metadata', {}))
                        updated_count += 1
                    
                    # Respect GitHub API rate limits
                    time.sleep(0.5)
                
                progress.update(task, advance=1)
    
    # Save updated data
    manager.export_to_yaml(repo_file)
    
    console.print(f"\n[green]Successfully updated metadata for {updated_count} repositories[/green]")
    
def main():
    # Get GitHub token from environment variable
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        console.print("[yellow]Warning: No GITHUB_TOKEN environment variable found. Using unauthenticated access (rate limits apply)[/yellow]")
    
    update_repository_metadata(token)

if __name__ == '__main__':
    main() 