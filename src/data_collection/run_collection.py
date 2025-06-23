"""
Script to orchestrate the data collection process.
Runs all configured collectors and aggregates their data.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

from .game_data.pokemon_collector import PokemonDataCollector
from .api_integration.repo_scanner import RepoScanner
from .api_integration.game_repo_scanner import GameRepoScanner
from .config import API_CONFIG, COLLECTION_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataCollectionOrchestrator:
    """Orchestrates the data collection process across all collectors."""

    def __init__(self):
        self.collectors = {
            "pokemon": PokemonDataCollector(),
            "repos": RepoScanner(
                github_token=os.getenv("GITHUB_TOKEN"), gitlab_token=os.getenv("GITLAB_TOKEN")
            ),
            "game_repos": GameRepoScanner(),
        }

        # Create output directory
        self.output_dir = "data/collected"
        os.makedirs(self.output_dir, exist_ok=True)

    async def run_collection(self):
        """Run all collectors and aggregate their data."""
        collection_start = datetime.now()
        logger.info("Starting data collection process")

        try:
            # Run collectors concurrently
            collection_tasks = [
                self._run_collector(name, collector) for name, collector in self.collectors.items()
            ]

            results = await asyncio.gather(*collection_tasks, return_exceptions=True)

            # Process results
            collection_data = {}
            for name, result in zip(self.collectors.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Collector {name} failed: {str(result)}")
                    collection_data[name] = {"error": str(result)}
                else:
                    collection_data[name] = result

            # Save collection results
            timestamp = collection_start.strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"collection_{timestamp}.json")

            collection_metadata = {
                "timestamp": collection_start.isoformat(),
                "duration": (datetime.now() - collection_start).total_seconds(),
                "collectors": list(self.collectors.keys()),
            }

            with open(output_file, "w") as f:
                json.dump({"metadata": collection_metadata, "data": collection_data}, f, indent=2)

            logger.info(f"Data collection completed. Results saved to {output_file}")

            # Generate collection report
            await self._generate_report(collection_data, collection_metadata)

        except Exception as e:
            logger.error(f"Error in data collection process: {str(e)}")
            raise
        finally:
            # Cleanup
            await self._cleanup_collectors()

    async def _run_collector(self, name: str, collector: Any) -> Dict[str, Any]:
        """Run a single collector with timeout."""
        try:
            logger.info(f"Starting collector: {name}")
            async with collector:
                return await asyncio.wait_for(
                    collector.collect(), timeout=COLLECTION_CONFIG["timeout"]
                )
        except asyncio.TimeoutError:
            logger.error(f"Collector {name} timed out")
            raise
        except Exception as e:
            logger.error(f"Error in collector {name}: {str(e)}")
            raise

    async def _cleanup_collectors(self):
        """Clean up all collectors."""
        for name, collector in self.collectors.items():
            try:
                await collector.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up collector {name}: {str(e)}")

    async def _generate_report(self, collection_data: Dict[str, Any], metadata: Dict[str, Any]):
        """Generate a report summarizing the collection results."""
        report_file = os.path.join(self.output_dir, f"report_{metadata['timestamp']}.txt")

        try:
            with open(report_file, "w") as f:
                f.write("Data Collection Report\n")
                f.write("=" * 50 + "\n\n")

                # Write metadata
                f.write("Collection Information:\n")
                f.write(f"Timestamp: {metadata['timestamp']}\n")
                f.write(f"Duration: {metadata['duration']:.2f} seconds\n")
                f.write(f"Collectors: {', '.join(metadata['collectors'])}\n\n")

                # Write collector summaries
                for name, data in collection_data.items():
                    f.write(f"\n{name.upper()} Collector Summary:\n")
                    f.write("-" * 30 + "\n")

                    if "error" in data:
                        f.write(f"Error: {data['error']}\n")
                        continue

                    if name == "pokemon":
                        self._write_pokemon_summary(f, data)
                    elif name == "repos":
                        self._write_repo_summary(f, data)
                    elif name == "game_repos":
                        self._write_game_repo_summary(f, data)

                    f.write("\n")

            logger.info(f"Collection report generated: {report_file}")

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")

    def _write_pokemon_summary(self, f, data: Dict[str, Any]):
        """Write Pokemon data summary to report."""
        api_data = data.get("api_data", {})
        rom_data = data.get("rom_data", {})

        f.write(f"API Data:\n")
        f.write(f"- Pokemon: {len(api_data.get('pokemon', []))}\n")
        f.write(f"- Moves: {len(api_data.get('moves', []))}\n")
        f.write(f"- Items: {len(api_data.get('items', []))}\n")
        f.write(f"- Locations: {len(api_data.get('locations', []))}\n\n")

        f.write(f"ROM Data:\n")
        for game, game_data in rom_data.items():
            f.write(f"- {game}:\n")
            f.write(f"  - Pokemon: {len(game_data.get('pokemon', []))}\n")
            f.write(f"  - Moves: {len(game_data.get('moves', []))}\n")
            f.write(f"  - Maps: {len(game_data.get('maps', []))}\n")
            f.write(f"  - Items: {len(game_data.get('items', []))}\n")

    def _write_repo_summary(self, f, data: Dict[str, Any]):
        """Write repository data summary to report."""
        github_data = data.get("github", [])
        gitlab_data = data.get("gitlab", [])

        f.write(f"GitHub Repositories: {len(github_data)}\n")
        for repo in github_data:
            f.write(f"- {repo['full_name']}:\n")
            f.write(f"  - Stars: {repo['stars']}\n")
            f.write(f"  - Language: {repo['language']}\n")
            f.write(f"  - Last Updated: {repo['last_updated']}\n")

            analysis = repo.get("analysis", {})
            f.write(f"  - Code Stats:\n")
            for stat, value in analysis.get("code_stats", {}).items():
                f.write(f"    - {stat}: {value}\n")
            f.write(f"  - API Endpoints: {len(analysis.get('api_endpoints', []))}\n")
            f.write("\n")

        f.write(f"\nGitLab Repositories: {len(gitlab_data)}\n")
        for repo in gitlab_data:
            f.write(f"- {repo['full_name']}:\n")
            f.write(f"  - Stars: {repo['stars']}\n")
            f.write(f"  - Language: {repo['language']}\n")
            f.write(f"  - Last Updated: {repo['last_updated']}\n")

            analysis = repo.get("analysis", {})
            f.write(f"  - Code Stats:\n")
            for stat, value in analysis.get("code_stats", {}).items():
                f.write(f"    - {stat}: {value}\n")
            f.write(f"  - API Endpoints: {len(analysis.get('api_endpoints', []))}\n")
            f.write("\n")

    def _write_game_repo_summary(self, f, data: Dict[str, Any]):
        """Write game repository data summary to report."""
        for game_type, game_data in data.items():
            f.write(f"\n{game_type.upper()} Game Data:\n")
            f.write("-" * 30 + "\n")

            if game_type == "pokemon":
                self._write_pokemon_repo_summary(f, game_data)
            elif game_type == "osrs":
                self._write_osrs_repo_summary(f, game_data)
            elif game_type == "fortnite":
                self._write_fortnite_repo_summary(f, game_data)
            elif game_type == "cookie_clicker":
                self._write_cookie_clicker_repo_summary(f, game_data)

    def _write_pokemon_repo_summary(self, f, data: Dict[str, Any]):
        """Write Pokemon repository summary."""
        f.write("Games:\n")
        for game_name, game_data in data.get("games", {}).items():
            f.write(f"- {game_name}:\n")
            f.write(f"  - ROM Structures: {len(game_data.get('rom_data', {}))}\n")
            f.write(f"  - Maps: {len(game_data.get('maps', []))}\n")
            f.write(f"  - Scripts: {len(game_data.get('scripts', []))}\n")
            f.write(f"  - Constants: {len(game_data.get('constants', {}))}\n")

            assets = game_data.get("assets", {})
            f.write(f"  - Assets:\n")
            for asset_type, assets_list in assets.items():
                f.write(f"    - {asset_type}: {len(assets_list)}\n")

        f.write("\nTools:\n")
        for tool_name, tool_data in data.get("tools", {}).items():
            f.write(f"- {tool_name}:\n")
            f.write(f"  - APIs: {len(tool_data.get('apis', []))}\n")
            f.write(f"  - Dependencies: {len(tool_data.get('dependencies', {}))}\n")
            f.write(f"  - Documentation: {len(tool_data.get('docs', []))}\n")

    def _write_osrs_repo_summary(self, f, data: Dict[str, Any]):
        """Write OSRS repository summary."""
        f.write("Game Data:\n")
        for category, items in data.get("game_data", {}).items():
            f.write(f"- {category}: {len(items)}\n")

        f.write("\nTools:\n")
        for tool_name, tool_data in data.get("tools", {}).items():
            f.write(f"- {tool_name}:\n")
            f.write(f"  - Features: {len(tool_data.get('features', []))}\n")
            f.write(f"  - APIs: {len(tool_data.get('apis', []))}\n")
            f.write(f"  - Dependencies: {len(tool_data.get('dependencies', {}))}\n")

    def _write_fortnite_repo_summary(self, f, data: Dict[str, Any]):
        """Write Fortnite repository summary."""
        f.write("Research:\n")
        for research_name, research_data in data.get("research", {}).items():
            f.write(f"- {research_name}:\n")
            f.write(f"  - Features: {len(research_data.get('features', []))}\n")
            f.write(f"  - APIs: {len(research_data.get('apis', []))}\n")
            f.write(f"  - Documentation: {len(research_data.get('docs', []))}\n")

    def _write_cookie_clicker_repo_summary(self, f, data: Dict[str, Any]):
        """Write Cookie Clicker repository summary."""
        f.write("Game:\n")
        for category, items in data.get("game", {}).items():
            f.write(f"- {category}: {len(items)}\n")

        f.write("\nMods:\n")
        for mod_name, mod_data in data.get("mods", {}).items():
            f.write(f"- {mod_name}:\n")
            f.write(f"  - Features: {len(mod_data.get('features', []))}\n")
            f.write(f"  - Dependencies: {len(mod_data.get('dependencies', {}))}\n")


async def main():
    """Main entry point for data collection."""
    orchestrator = DataCollectionOrchestrator()
    await orchestrator.run_collection()


if __name__ == "__main__":
    asyncio.run(main())
