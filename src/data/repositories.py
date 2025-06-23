from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import yaml
from pathlib import Path


@dataclass
class Repository:
    name: str
    description: str
    category: str
    features: List[str]
    url: Optional[str] = None
    stars: Optional[int] = None
    last_updated: Optional[datetime] = None
    language: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert repository to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "features": self.features,
            "url": self.url,
            "stars": self.stars,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "language": self.language,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Repository":
        """Create repository from dictionary data."""
        if "last_updated" in data and data["last_updated"]:
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


class RepositoryManager:
    def __init__(self):
        self.categories = {
            "core_libraries": [],
            "ai_integration": [],
            "multi_purpose": [],
            "study_tools": [],
            "media_voice": [],
            "game_integration": [],
            "image_processing": [],
            "utility_tools": [],
            "plex_integration": [],
        }
        self._category_stats: Dict[str, Dict] = {}
        self._last_updated: Optional[datetime] = None

    def add_repository(self, repo: Repository) -> bool:
        """Add a repository to the manager. Returns True if successful."""
        if repo.category in self.categories:
            # Check for duplicates
            if not any(r.name == repo.name for r in self.categories[repo.category]):
                self.categories[repo.category].append(repo)
                self._last_updated = datetime.now()
                return True
        return False

    def remove_repository(self, name: str, category: str) -> bool:
        """Remove a repository by name and category. Returns True if successful."""
        if category in self.categories:
            initial_length = len(self.categories[category])
            self.categories[category] = [r for r in self.categories[category] if r.name != name]
            if len(self.categories[category]) < initial_length:
                self._last_updated = datetime.now()
                return True
        return False

    def get_repositories_by_category(self, category: str) -> List[Repository]:
        """Get all repositories in a category."""
        return self.categories.get(category, [])

    def get_repository_by_name(self, name: str) -> Optional[Repository]:
        """Find a repository by name across all categories."""
        for repos in self.categories.values():
            for repo in repos:
                if repo.name.lower() == name.lower():
                    return repo
        return None

    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the repositories."""
        stats = {
            "total_repositories": sum(len(repos) for repos in self.categories.values()),
            "repositories_by_category": {
                category: len(repos) for category, repos in self.categories.items()
            },
            "languages": {},
            "total_stars": 0,
            "last_updated": self._last_updated,
        }

        for repos in self.categories.values():
            for repo in repos:
                if repo.language:
                    stats["languages"][repo.language] = stats["languages"].get(repo.language, 0) + 1
                if repo.stars:
                    stats["total_stars"] += repo.stars

        return stats

    def export_to_yaml(self, filename: str):
        """Export repositories to YAML file."""
        data = {
            "metadata": {
                "last_updated": self._last_updated.isoformat() if self._last_updated else None,
                "statistics": self.get_statistics(),
            },
            "categories": {
                category: [repo.to_dict() for repo in repos]
                for category, repos in self.categories.items()
            },
        }

        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        with open(filename, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, filename: str) -> "RepositoryManager":
        """Create RepositoryManager from YAML file."""
        manager = cls()

        if not Path(filename).exists():
            return manager

        with open(filename, "r") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict) and "categories" in data:
            for category, repos in data["categories"].items():
                for repo_data in repos:
                    repo = Repository.from_dict(repo_data)
                    manager.add_repository(repo)

        if isinstance(data, dict) and "metadata" in data:
            if data["metadata"].get("last_updated"):
                manager._last_updated = datetime.fromisoformat(data["metadata"]["last_updated"])

        return manager

    def merge(self, other: "RepositoryManager") -> None:
        """Merge another RepositoryManager into this one."""
        for category, repos in other.categories.items():
            for repo in repos:
                self.add_repository(repo)
