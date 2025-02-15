import os
from pathlib import Path
import subprocess
from typing import Optional
from data.repositories import RepositoryManager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

def clone_repository(url: str, target_dir: Path, category: str) -> bool:
    """Clone a single repository."""
    if not url:
        return False
        
    # Convert GitHub URL format to git URL
    if not url.startswith('git@') and not url.startswith('https://'):
        url = f'https://github.com/{url}.git'
    
    # Create category directory
    category_dir = target_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract repo name from URL
    repo_name = url.split('/')[-1].replace('.git', '')
    repo_dir = category_dir / repo_name
    
    # Skip if already exists
    if repo_dir.exists():
        console.print(f"[yellow]Repository {repo_name} already exists, skipping...[/yellow]")
        return True
    
    try:
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(repo_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
        else:
            console.print(f"[red]Failed to clone {url}: {result.stderr}[/red]")
            return False
    except Exception as e:
        console.print(f"[red]Error cloning {url}: {str(e)}[/red]")
        return False

def main():
    # Load repositories
    repo_file = Path('src/data/repositories.yaml')
    if not repo_file.exists():
        console.print("[red]Repository data not found. Please run parse_repos.py first.[/red]")
        return
    
    manager = RepositoryManager.from_yaml(repo_file)
    
    # Create repos directory
    repos_dir = Path('repos')
    repos_dir.mkdir(exist_ok=True)
    
    total_repos = sum(len(repos) for repos in manager.categories.values())
    successful = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Cloning repositories...", total=total_repos)
        
        for category, repos in manager.categories.items():
            for repo in repos:
                if repo.url:
                    progress.update(task, description=f"[cyan]Cloning {repo.name}...")
                    if clone_repository(repo.url, repos_dir, category):
                        successful += 1
                    else:
                        failed += 1
                progress.advance(task)
    
    # Print summary
    console.print(f"\n[green]Successfully cloned {successful} repositories[/green]")
    if failed > 0:
        console.print(f"[red]Failed to clone {failed} repositories[/red]")

if __name__ == '__main__':
    main() 