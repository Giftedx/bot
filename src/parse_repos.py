from typing import Tuple, List, Optional
import re
from pathlib import Path
from data.repositories import Repository, RepositoryManager

def parse_repo_line(line: str, next_lines: List[str]) -> Optional[Tuple[str, str, str, List[str]]]:
    # Extract repo name and description
    match = re.match(r'\d+\.\s+([^(]+)\s*(?:\(([^)]+)\))?\s*-?\s*(.*)', line.strip())
    if not match:
        return None
    
    name = match.group(1).strip()
    url = match.group(2).strip() if match.group(2) else None
    description = match.group(3).strip()
    features = []
    
    # Extract features from indented lines
    for next_line in next_lines:
        if re.match(r'\s*-\s+', next_line):
            feature = next_line.strip('- ').strip()
            if feature:
                # If this is the first feature and no description, use it as description
                if not description and not features:
                    description = feature
                else:
                    features.append(feature)
        else:
            break
    
    return name, url, description, features

def parse_markdown_file(file_path: str) -> RepositoryManager:
    manager = RepositoryManager()
    current_category = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    category_mapping = {
        'Core Discord Libraries': 'core_libraries',
        'AI Integration Bots': 'ai_integration',
        'Multi-Purpose Bots': 'multi_purpose',
        'Study Tools': 'study_tools',
        'Media & Voice': 'media_voice',
        'Game Integration': 'game_integration',
        'Image & Media Processing': 'image_processing',
        'Utility Tools': 'utility_tools',
        'Plex Integration': 'plex_integration'
    }
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # Check if line is a category header
        if line.startswith('##'):
            category_name = line.lstrip('#').strip()
            current_category = category_mapping.get(category_name)
            i += 1
            continue
        
        # Skip lines that don't start with a number (not a repository entry)
        if not re.match(r'\d+\.', line):
            i += 1
            continue
            
        if current_category:
            # Get next lines for feature extraction
            next_lines = []
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith('-')):
                if lines[j].strip():
                    next_lines.append(lines[j])
                j += 1
            
            parsed = parse_repo_line(line, next_lines)
            if parsed:
                name, url, description, features = parsed
                repo = Repository(
                    name=name,
                    url=url,
                    description=description,
                    category=current_category,
                    features=features
                )
                manager.add_repository(repo)
            i = j
        else:
            i += 1
    
    return manager

def main():
    # Parse the markdown file
    repo_file = Path('notes/repo-list.md')
    manager = parse_markdown_file(repo_file)
    
    # Export to YAML for easier viewing/editing
    output_file = Path('src/data/repositories.yaml')
    manager.export_to_yaml(output_file)
    
    print(f"Successfully parsed repositories and saved to {output_file}")
    
    # Print some statistics
    total_repos = sum(len(repos) for repos in manager.categories.values())
    print(f"\nTotal repositories: {total_repos}")
    print("\nRepositories by category:")
    for category, repos in manager.categories.items():
        print(f"- {category}: {len(repos)}")

if __name__ == '__main__':
    main() 