"""Database integration layer to unify different storage systems."""

import logging
from typing import Optional, Dict, Any

from src.core.database import DatabaseManager as CoreDB
from src.core.battle_database import BattleDatabase
from src.osrs.database.models import Database as OSRSDB

logger = logging.getLogger(__name__)


class DatabaseIntegration:
    """Unified interface for all database operations."""

    def __init__(
        self,
        core_db_path: str = "data/bot.db",
        osrs_db_path: str = "data/osrs_bot.db",
        pg_dsn: Optional[str] = None,
    ):
        """Initialize database connections.

        Args:
            core_db_path: Path to core SQLite database
            osrs_db_path: Path to OSRS SQLite database
            pg_dsn: PostgreSQL connection string for battle system
        """
        self.core_db = CoreDB(core_db_path)
        self.osrs_db = OSRSDB(osrs_db_path)
        self.battle_db = None
        if pg_dsn:
            import asyncpg

            self.battle_db = BattleDatabase(asyncpg.create_pool(pg_dsn))

    async def get_player_profile(self, discord_id: int) -> Dict[str, Any]:
        """Get complete player profile from all systems.

        Args:
            discord_id: Discord user ID

        Returns:
            Combined player data from all systems
        """
        # Get core player data
        core_data = self.core_db.get_player(str(discord_id))
        if not core_data:
            return {}

        # Get OSRS data if exists
        osrs_data = self.osrs_db.get_player(discord_id)

        # Get battle stats if available
        battle_stats = {}
        if self.battle_db:
            battle_stats = await self.battle_db.get_player_stats(discord_id, None)

        return {"core": core_data, "osrs": osrs_data or {}, "battle": battle_stats}

    def save_player_data(
        self,
        discord_id: int,
        username: str,
        core_data: Optional[Dict[str, Any]] = None,
        osrs_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save player data across systems.

        Args:
            discord_id: Discord user ID
            username: Player username
            core_data: Core system data
            osrs_data: OSRS specific data
        """
        if core_data:
            self.core_db.save_player(str(discord_id), username, core_data)

        if osrs_data:
            player = self.osrs_db.get_player(discord_id)
            if player:
                # Update existing
                self.osrs_db.update_skills(player["id"], osrs_data.get("skills", {}))
                if "inventory" in osrs_data:
                    self.osrs_db.update_inventory(player["id"], osrs_data["inventory"])
                if "equipment" in osrs_data:
                    self.osrs_db.update_equipment(player["id"], osrs_data["equipment"])
            else:
                # Create new
                self.osrs_db.create_player(discord_id, username)

    def cleanup(self) -> None:
        """Clean up all database connections."""
        self.core_db.close()
        self.osrs_db.close()
        # Battle DB cleanup handled by connection pool
