from pathlib import Path
from typing import List, Optional, Dict
from data.repositories import Repository, RepositoryManager
import argparse
import re
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

console = Console()

def search_repositories(
    manager: RepositoryManager,
    query: str = None,
    category: str = None,
    language: str = None,
    min_stars: int = None,
    tags: List[str] = None,
    updated_since: datetime = None,
    sort_by: str = None,
    limit: int = None
) -> List[Repository]:
    """
    Advanced search for repositories with multiple filters and sorting options.
    
    Args:
        query: Search term for name/description/features
        category: Filter by category
        language: Filter by programming language
        min_stars: Minimum number of stars
        tags: List of tags to filter by
        updated_since: Filter by last update date
        sort_by: Sort results by ('stars', 'name', 'updated')
        limit: Limit number of results
    """
    results = []
    
    for cat, repos in manager.categories.items():
        if category and cat != category:
            continue
            
        for repo in repos:
            # Apply filters
            if query and not (
                query.lower() in repo.name.lower() or
                query.lower() in repo.description.lower() or
                any(query.lower() in feature.lower() for feature in repo.features)
            ):
                continue
                
            if language and repo.language and repo.language.lower() != language.lower():
                continue
                
            if min_stars and (not repo.stars or repo.stars < min_stars):
                continue
                
            if tags and not all(tag in repo.tags for tag in tags):
                continue
                
            if updated_since and (not repo.last_updated or repo.last_updated < updated_since):
                continue
                
            results.append(repo)
    
    # Sort results
    if sort_by:
        if sort_by == 'stars':
            results.sort(key=lambda x: (x.stars or 0), reverse=True)
        elif sort_by == 'name':
            results.sort(key=lambda x: x.name.lower())
        elif sort_by == 'updated':
            results.sort(key=lambda x: x.last_updated or datetime.min, reverse=True)
    
    # Apply limit
    if limit and limit > 0:
        results = results[:limit]
    
    return results

def print_repository_table(repos: List[Repository], detailed: bool = False):
    """Print repositories in a rich formatted table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Language", style="yellow")
    table.add_column("Stars", justify="right", style="blue")
    if detailed:
        table.add_column("Description")
        table.add_column("Features")
    
    for repo in repos:
        row = [
            repo.name,
            repo.category,
            repo.language or "N/A",
            str(repo.stars or "N/A")
        ]
        if detailed:
            row.extend([
                repo.description,
                "\n".join(f"• {f}" for f in repo.features) if repo.features else "N/A"
            ])
        table.add_row(*row)
    
    console.print(table)

def print_statistics(manager: RepositoryManager):
    """Print repository statistics."""
    stats = manager.get_statistics()
    
    console.print("\n[bold blue]Repository Statistics[/bold blue]")
    console.print(f"Total Repositories: {stats['total_repositories']}")
    console.print(f"Total Stars: {stats['total_stars']}")
    
    console.print("\n[bold green]Repositories by Category:[/bold green]")
    for category, count in stats['repositories_by_category'].items():
        console.print(f"• {category}: {count}")
    
    if stats['languages']:
        console.print("\n[bold yellow]Languages:[/bold yellow]")
        for lang, count in sorted(stats['languages'].items(), key=lambda x: x[1], reverse=True):
            console.print(f"• {lang}: {count}")

def export_markdown(repos: List[Repository], filename: str):
    """Export search results to a markdown file."""
    with open(filename, 'w') as f:
        f.write("# Repository Search Results\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for repo in repos:
            f.write(f"## {repo.name}\n")
            if repo.url:
                f.write(f"URL: {repo.url}\n")
            f.write(f"Category: {repo.category}\n")
            if repo.language:
                f.write(f"Language: {repo.language}\n")
            if repo.stars:
                f.write(f"Stars: {repo.stars}\n")
            f.write(f"\n{repo.description}\n\n")
            
            if repo.features:
                f.write("### Features\n")
                for feature in repo.features:
                    f.write(f"- {feature}\n")
            f.write("\n---\n\n")

def main():
    parser = argparse.ArgumentParser(description="Search Discord bot repositories")
    parser.add_argument("-q", "--query", help="Search query")
    parser.add_argument("-c", "--category", help="Filter by category")
    parser.add_argument("-l", "--language", help="Filter by programming language")
    parser.add_argument("-s", "--stars", type=int, help="Minimum number of stars")
    parser.add_argument("-t", "--tags", nargs="+", help="Filter by tags")
    parser.add_argument("-u", "--updated", type=int, help="Updated within days")
    parser.add_argument("--sort", choices=['stars', 'name', 'updated'], help="Sort results")
    parser.add_argument("--limit", type=int, help="Limit number of results")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed information")
    parser.add_argument("--stats", action="store_true", help="Show repository statistics")
    parser.add_argument("--export", help="Export results to markdown file")
    args = parser.parse_args()
    
    # Load repositories
    repo_file = Path('src/data/repositories.yaml')
    if not repo_file.exists():
        console.print("[red]Repository data not found. Please run parse_repos.py first.[/red]")
        return
    
    manager = RepositoryManager.from_yaml(repo_file)
    
    # Show statistics if requested
    if args.stats:
        print_statistics(manager)
        return
    
    # Prepare search parameters
    updated_since = None
    if args.updated:
        updated_since = datetime.now() - timedelta(days=args.updated)
    
    # Search repositories
    results = search_repositories(
        manager,
        query=args.query,
        category=args.category,
        language=args.language,
        min_stars=args.stars,
        tags=args.tags,
        updated_since=updated_since,
        sort_by=args.sort,
        limit=args.limit
    )
    
    if not results:
        console.print("[yellow]No repositories found matching your search criteria.[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(results)} matching repositories:[/green]")
    
    # Display results
    print_repository_table(results, args.detailed)
    
    # Export results if requested
    if args.export:
        export_markdown(results, args.export)
        console.print(f"\n[blue]Results exported to: {args.export}[/blue]")

if __name__ == '__main__':
    main() 