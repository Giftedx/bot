"""
Repository scanner that clones and analyzes repositories from various sources.
Handles cloning, code analysis, and data extraction from Git repositories.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import git
from github import Github
import gitlab

from ..base_collector import BaseCollector
from ..config import REPO_SOURCES

logger = logging.getLogger(__name__)


class RepoScanner(BaseCollector):
    """Scanner for Git repositories from various sources."""

    def __init__(self, github_token: Optional[str] = None, gitlab_token: Optional[str] = None):
        super().__init__("repo_scanner")
        self.github_token = github_token
        self.gitlab_token = gitlab_token
        self.github_client = Github(github_token) if github_token else None
        self.gitlab_client = (
            gitlab.Gitlab("https://gitlab.com", private_token=gitlab_token)
            if gitlab_token
            else None
        )

        # Base paths for cloned repos
        self.base_path = os.path.join("repos")
        self.reference_path = os.path.join("reference_repos")

        # Ensure directories exist
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.reference_path, exist_ok=True)

    async def collect(self) -> Dict[str, Any]:
        """Collect repository data from all configured sources."""
        data = {
            "github": await self._collect_github_repos(),
            "gitlab": await self._collect_gitlab_repos(),
        }
        return data

    async def _collect_github_repos(self) -> List[Dict[str, Any]]:
        """Collect data from GitHub repositories."""
        repos_data = []

        if not self.github_client:
            logger.warning("GitHub token not provided, skipping GitHub repositories")
            return repos_data

        for repo_path in REPO_SOURCES["github"]:
            try:
                # Get repository information
                repo = self.github_client.get_repo(repo_path)

                # Clone or update repository
                local_path = os.path.join(self.reference_path, repo_path.replace("/", "_"))
                await self._clone_or_update_repo(repo.clone_url, local_path)

                # Collect repository data
                repo_data = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "topics": repo.get_topics(),
                    "last_updated": repo.updated_at.isoformat(),
                    "local_path": local_path,
                    "analysis": await self._analyze_repo(local_path),
                }
                repos_data.append(repo_data)

            except Exception as e:
                logger.error(f"Error collecting data for GitHub repo {repo_path}: {str(e)}")

        return repos_data

    async def _collect_gitlab_repos(self) -> List[Dict[str, Any]]:
        """Collect data from GitLab repositories."""
        repos_data = []

        if not self.gitlab_client:
            logger.warning("GitLab token not provided, skipping GitLab repositories")
            return repos_data

        for repo_path in REPO_SOURCES["gitlab"]:
            try:
                # Get repository information
                project = self.gitlab_client.projects.get(repo_path)

                # Clone or update repository
                local_path = os.path.join(self.reference_path, repo_path.replace("/", "_"))
                await self._clone_or_update_repo(project.http_url_to_repo, local_path)

                # Collect repository data
                repo_data = {
                    "name": project.name,
                    "full_name": project.path_with_namespace,
                    "description": project.description,
                    "stars": project.star_count,
                    "forks": project.forks_count,
                    "language": project.predominant_language,
                    "topics": project.topics,
                    "last_updated": project.last_activity_at,
                    "local_path": local_path,
                    "analysis": await self._analyze_repo(local_path),
                }
                repos_data.append(repo_data)

            except Exception as e:
                logger.error(f"Error collecting data for GitLab repo {repo_path}: {str(e)}")

        return repos_data

    async def _clone_or_update_repo(self, repo_url: str, local_path: str):
        """Clone a repository or update it if it already exists."""
        try:
            if os.path.exists(local_path):
                # Update existing repository
                repo = git.Repo(local_path)
                origin = repo.remotes.origin
                origin.pull()
                logger.info(f"Updated repository at {local_path}")
            else:
                # Clone new repository
                git.Repo.clone_from(repo_url, local_path)
                logger.info(f"Cloned repository to {local_path}")
        except Exception as e:
            logger.error(f"Error cloning/updating repository {repo_url}: {str(e)}")
            raise

    async def _analyze_repo(self, repo_path: str) -> Dict[str, Any]:
        """Analyze a repository's contents."""
        analysis = {
            "file_types": {},
            "dependencies": {},
            "code_stats": {"total_lines": 0, "code_lines": 0, "comment_lines": 0, "blank_lines": 0},
            "api_endpoints": [],
            "config_files": [],
        }

        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Skip .git directory
                if ".git" in file_path:
                    continue

                # Update file type stats
                ext = os.path.splitext(file)[1]
                analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1

                # Analyze specific file types
                if file in ["package.json", "requirements.txt", "build.gradle", "pom.xml"]:
                    analysis["dependencies"].update(await self._parse_dependencies(file_path))

                # Analyze code files
                if ext in [".py", ".js", ".java", ".cpp", ".h", ".c", ".cs"]:
                    stats = await self._analyze_code_file(file_path)
                    for key, value in stats.items():
                        analysis["code_stats"][key] += value

                # Look for API endpoints
                if ext in [".py", ".js", ".java"]:
                    endpoints = await self._find_api_endpoints(file_path)
                    analysis["api_endpoints"].extend(endpoints)

                # Track config files
                if file.endswith((".json", ".yaml", ".yml", ".ini", ".conf")):
                    analysis["config_files"].append(os.path.relpath(file_path, repo_path))

        return analysis

    async def _parse_dependencies(self, file_path: str) -> Dict[str, str]:
        """Parse dependency information from various dependency files."""
        deps = {}

        try:
            if file_path.endswith("package.json"):
                with open(file_path, "r") as f:
                    data = json.load(f)
                    deps.update(data.get("dependencies", {}))
                    deps.update(data.get("devDependencies", {}))

            elif file_path.endswith("requirements.txt"):
                with open(file_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            name = line.split("==")[0].split(">=")[0].split("<=")[0]
                            deps[name] = line[len(name) :].strip("=<>")

            # Add more dependency file formats as needed

        except Exception as e:
            logger.error(f"Error parsing dependencies from {file_path}: {str(e)}")

        return deps

    async def _analyze_code_file(self, file_path: str) -> Dict[str, int]:
        """Analyze a code file for basic statistics."""
        stats = {"total_lines": 0, "code_lines": 0, "comment_lines": 0, "blank_lines": 0}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                in_multiline_comment = False

                for line in f:
                    stats["total_lines"] += 1
                    line = line.strip()

                    if not line:
                        stats["blank_lines"] += 1
                    elif line.startswith(("/*", "/**")) and "*/" in line:
                        stats["comment_lines"] += 1
                    elif line.startswith(("/*", "/**")):
                        in_multiline_comment = True
                        stats["comment_lines"] += 1
                    elif "*/" in line and in_multiline_comment:
                        in_multiline_comment = False
                        stats["comment_lines"] += 1
                    elif in_multiline_comment:
                        stats["comment_lines"] += 1
                    elif line.startswith(("#", "//", "--")):
                        stats["comment_lines"] += 1
                    else:
                        stats["code_lines"] += 1

        except Exception as e:
            logger.error(f"Error analyzing code file {file_path}: {str(e)}")

        return stats

    async def _find_api_endpoints(self, file_path: str) -> List[Dict[str, str]]:
        """Find API endpoints in code files."""
        endpoints = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # Look for common API patterns
                patterns = [
                    r'@app.route\([\'"](.+?)[\'"]\)',  # Flask
                    r'@api.route\([\'"](.+?)[\'"]\)',  # Flask-RESTful
                    r'router.get\([\'"](.+?)[\'"]\)',  # Express.js
                    r'router.post\([\'"](.+?)[\'"]\)',
                    r'router.put\([\'"](.+?)[\'"]\)',
                    r'router.delete\([\'"](.+?)[\'"]\)',
                    r'@GetMapping\([\'"](.+?)[\'"]\)',  # Spring
                    r'@PostMapping\([\'"](.+?)[\'"]\)',
                    r'@PutMapping\([\'"](.+?)[\'"]\)',
                    r'@DeleteMapping\([\'"](.+?)[\'"]\)',
                ]

                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        endpoints.append(
                            {
                                "path": match.group(1),
                                "file": os.path.basename(file_path),
                                "line": content.count("\n", 0, match.start()) + 1,
                            }
                        )

        except Exception as e:
            logger.error(f"Error finding API endpoints in {file_path}: {str(e)}")

        return endpoints

    async def process_item(self, item: Any) -> Any:
        """Process a single item (implemented for BaseCollector compatibility)."""
        return item
