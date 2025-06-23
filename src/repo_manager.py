#!/usr/bin/env python3
"""
Master repository management script.
Combines functionality from multiple repository management scripts into a single tool.
"""
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("repo_manager.log")],
)
logger = logging.getLogger(__name__)


class Repository:
    """Represents a repository with metadata."""

    def __init__(
        self,
        name: str,
        url: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None,
        features: List[str] = None,
        language: Optional[str] = None,
        stars: Optional[int] = None,
        last_updated: Optional[datetime] = None,
        tags: List[str] = None,
        metadata: Dict = None,
    ):
        self.name = name
        self.url = url
        self.category = category
        self.description = description
        self.features = features or []
        self.language = language
        self.stars = stars
        self.last_updated = last_updated
        self.tags = tags or []
        self.metadata = metadata or {}


class RepositoryManager:
    """Manages repository operations including cloning, analysis, and metadata updates."""

    def __init__(self, base_dir: str = "repos"):
        """Initialize repository manager."""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.repositories: Dict[str, List[Repository]] = {}

    def extract_repos_from_md(self, md_file: Path) -> List[str]:
        """Extract repository names from markdown file."""
        repos = []
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Find all repository references in format owner/repo
                matches = re.findall(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", content)
                for match in matches:
                    if "/" in match and not match.startswith(("http", "git@")):
                        repos.append(match)
            return list(set(repos))  # Remove duplicates
        except Exception as e:
            logger.error(f"Failed to read {md_file}: {e}")
            return []

    def clone_repository(self, repo: str, category: Optional[str] = None) -> bool:
        """Clone a single repository."""
        try:
            if "/" not in repo:
                logger.warning(f"Invalid repository format: {repo}")
                return False

            owner, repo_name = repo.split("/", 1)

            # Determine target directory
            if category:
                target_dir = self.base_dir / category / owner
            else:
                target_dir = self.base_dir / owner
            target_dir.mkdir(parents=True, exist_ok=True)

            repo_path = target_dir / repo_name

            # Skip if already exists
            if repo_path.exists():
                logger.info(f"Repository {repo} already exists at {repo_path}")
                return True

            # Construct repository URL
            if not repo.startswith(("http://", "https://", "git@")):
                repo_url = f"https://github.com/{repo}.git"
            else:
                repo_url = repo

            # Clone repository
            logger.info(f"Cloning {repo}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"Successfully cloned {repo}")
                return True
            else:
                logger.error(f"Failed to clone {repo}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error cloning {repo}: {e}")
            return False

    def move_repositories(self, source_dir: Path, target_dir: Optional[Path] = None) -> None:
        """Move repositories from source directory to target directory."""
        if not source_dir.exists():
            logger.info(f"Source directory {source_dir} does not exist")
            return

        target_dir = target_dir or self.base_dir
        target_dir.mkdir(exist_ok=True)

        for item in source_dir.iterdir():
            if item.is_dir():
                dst = target_dir / item.name
                if dst.exists():
                    logger.info(f"Directory {item.name} already exists in target")
                    continue
                try:
                    shutil.move(str(item), str(dst))
                    logger.info(f"Moved {item.name} to {target_dir}")
                except Exception as e:
                    logger.error(f"Failed to move {item.name}: {e}")

    def analyze_repository(self, repo_path: Path) -> Dict:
        """Analyze a repository for patterns and implementations."""
        patterns = {
            "language": None,
            "dependencies": [],
            "features": [],
            "api_usage": [],
            "documentation": [],
        }

        if not repo_path.exists():
            return patterns

        try:
            # Detect primary language
            patterns["language"] = self._detect_primary_language(repo_path)

            # Find dependencies
            patterns["dependencies"] = self._find_dependencies(repo_path)

            # Analyze features and API usage
            patterns["features"] = self._analyze_features(repo_path)
            patterns["api_usage"] = self._analyze_api_usage(repo_path)

            # Check documentation
            patterns["documentation"] = self._analyze_documentation(repo_path)

        except Exception as e:
            logger.error(f"Error analyzing {repo_path}: {e}")

        return patterns

    def _detect_primary_language(self, path: Path) -> Optional[str]:
        """Detect primary programming language used in the repository."""
        extensions = {}

        for root, _, files in os.walk(path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        if not extensions:
            return None

        # Map extensions to languages
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".java": "Java",
            ".ts": "TypeScript",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP",
        }

        # Find most common extension
        most_common = max(extensions.items(), key=lambda x: x[1])[0]
        return language_map.get(most_common)

    def _find_dependencies(self, path: Path) -> List[str]:
        """Find project dependencies."""
        dependencies = []

        # Check common dependency files
        dep_files = [
            "requirements.txt",
            "package.json",
            "pom.xml",
            "build.gradle",
            "Cargo.toml",
            "go.mod",
        ]

        for dep_file in dep_files:
            file_path = path / dep_file
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if dep_file == "requirements.txt":
                            dependencies.extend(
                                [
                                    line.split("==")[0].strip()
                                    for line in content.splitlines()
                                    if line.strip() and not line.startswith("#")
                                ]
                            )
                        elif dep_file == "package.json":
                            data = json.loads(content)
                            dependencies.extend(list(data.get("dependencies", {}).keys()))
                except Exception as e:
                    logger.error(f"Error reading {dep_file}: {e}")

        return list(set(dependencies))

    def _analyze_features(self, path: Path) -> List[str]:
        """Analyze repository features."""
        features = set()

        # Look for common feature indicators in file names and contents
        feature_patterns = [
            (r"api|rest|graphql", "API Integration"),
            (r"auth|login|oauth", "Authentication"),
            (r"test|spec|pytest", "Testing"),
            (r"docker|container", "Containerization"),
            (r"ci|travis|github/workflows", "CI/CD"),
            (r"docs|documentation", "Documentation"),
        ]

        for root, dirs, files in os.walk(path):
            for item in dirs + files:
                for pattern, feature in feature_patterns:
                    if re.search(pattern, item.lower()):
                        features.add(feature)

        return list(features)

    def _analyze_api_usage(self, path: Path) -> List[str]:
        """Analyze API usage patterns."""
        apis = set()

        # Look for common API patterns
        api_patterns = [
            (r"discord.*api", "Discord API"),
            (r"github.*api", "GitHub API"),
            (r"rest.*api", "REST API"),
            (r"graphql", "GraphQL"),
            (r"oauth", "OAuth"),
            (r"webhook", "Webhooks"),
        ]

        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".py", ".js", ".java", ".ts")):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            content = f.read().lower()
                            for pattern, api in api_patterns:
                                if re.search(pattern, content):
                                    apis.add(api)
                    except Exception:
                        continue

        return list(apis)

    def _analyze_documentation(self, path: Path) -> List[str]:
        """Analyze repository documentation."""
        docs = []

        # Check for common documentation files
        doc_files = ["README.md", "CONTRIBUTING.md", "CHANGELOG.md", "docs/", "wiki/", "API.md"]

        for doc in doc_files:
            doc_path = path / doc
            if doc_path.exists():
                docs.append(doc.rstrip("/"))

        return docs


def main():
    """Main entry point for repository management."""
    try:
        # Initialize repository manager
        manager = RepositoryManager()

        # Define repository categories
        categories = {
            "core_libraries": [
                "discord.py/discord.py",
                "Rapptz/discord.py",
                "discord.js/discord.js",
                "discordjs/discord.js",
            ],
            "ai_integration": ["TuringAI-Team/turing-ai-api", "Zero6992/chatGPT-discord-bot"],
            "utility_tools": ["Bushtit/osrs-tools", "Explv/osrs-pathfinder"],
            "plex_integration": ["Tautulli/Tautulli", "plexinc/plex-media-player"],
        }

        # Clone repositories by category
        for category, repos in categories.items():
            logger.info(f"\nCloning {category} repositories...")
            for repo in repos:
                manager.clone_repository(repo, category)

        # Move any repositories from reference_repos
        reference_repos = Path("reference_repos")
        if reference_repos.exists():
            logger.info("\nMoving repositories from reference_repos...")
            manager.move_repositories(reference_repos)

            # Remove reference_repos if empty
            if reference_repos.exists() and not any(reference_repos.iterdir()):
                reference_repos.unlink()
                logger.info("Removed empty reference_repos directory")

        # Analyze repositories
        logger.info("\nAnalyzing repositories...")
        for repo_dir in manager.base_dir.rglob("*"):
            if repo_dir.is_dir() and (repo_dir / ".git").exists():
                analysis = manager.analyze_repository(repo_dir)
                logger.info(f"\nAnalysis for {repo_dir.name}:")
                for key, value in analysis.items():
                    if value:
                        logger.info(f"{key}: {value}")

        logger.info("\nRepository management completed successfully")

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
