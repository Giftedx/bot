import sqlite3
from typing import Optional, Dict, List, Any, Tuple
import json
from pathlib import Path

from ..core.player_stats import PlayerStats


class DatabaseManager:
    def __init__(self, db_path: str = "osrs_bot.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        """Initialize the database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_player(self, discord_id: int, username: str) -> int:
        """Create a new player record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Insert player
            cursor.execute(
                """
                INSERT INTO players (discord_id, username)
                VALUES (?, ?)
                ON CONFLICT (discord_id) DO UPDATE SET
                    username = excluded.username,
                    last_seen = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (discord_id, username),
            )
            player_id = cursor.fetchone()[0]

            # Create stats record if it doesn't exist
            cursor.execute(
                """
                INSERT INTO player_stats (player_id)
                VALUES (?)
                ON CONFLICT (player_id) DO NOTHING
                """,
                (player_id,),
            )

            return player_id

    def get_player_stats(self, player_id: int) -> Optional[PlayerStats]:
        """Get player stats from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM player_stats
                WHERE player_id = ?
                """,
                (player_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            return PlayerStats(
                attack=row["attack_level"],
                strength=row["strength_level"],
                defence=row["defence_level"],
                ranged=row["ranged_level"],
                magic=row["magic_level"],
                prayer=row["prayer_level"],
                hitpoints=row["hitpoints_level"],
                mining=row["mining_level"],
                smithing=row["smithing_level"],
                fishing=row["fishing_level"],
                cooking=row["cooking_level"],
                woodcutting=row["woodcutting_level"],
                firemaking=row["firemaking_level"],
                crafting=row["crafting_level"],
                fletching=row["fletching_level"],
                herblore=row["herblore_level"],
                agility=row["agility_level"],
                thieving=row["thieving_level"],
                slayer=row["slayer_level"],
                farming=row["farming_level"],
                runecrafting=row["runecrafting_level"],
                construction=row["construction_level"],
                hunter=row["hunter_level"],
                attack_xp=row["attack_xp"],
                strength_xp=row["strength_xp"],
                defence_xp=row["defence_xp"],
                ranged_xp=row["ranged_xp"],
                magic_xp=row["magic_xp"],
                prayer_xp=row["prayer_xp"],
                hitpoints_xp=row["hitpoints_xp"],
                mining_xp=row["mining_xp"],
                smithing_xp=row["smithing_xp"],
                fishing_xp=row["fishing_xp"],
                cooking_xp=row["cooking_xp"],
                woodcutting_xp=row["woodcutting_xp"],
                firemaking_xp=row["firemaking_xp"],
                crafting_xp=row["crafting_xp"],
                fletching_xp=row["fletching_xp"],
                herblore_xp=row["herblore_xp"],
                agility_xp=row["agility_xp"],
                thieving_xp=row["thieving_xp"],
                slayer_xp=row["slayer_xp"],
                farming_xp=row["farming_xp"],
                runecrafting_xp=row["runecrafting_xp"],
                construction_xp=row["construction_xp"],
                hunter_xp=row["hunter_xp"],
            )

    def update_player_stats(self, player_id: int, stats: PlayerStats):
        """Update player stats in database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE player_stats
                SET
                    attack_level = ?, strength_level = ?, defence_level = ?,
                    ranged_level = ?, magic_level = ?, prayer_level = ?,
                    hitpoints_level = ?, mining_level = ?, smithing_level = ?,
                    fishing_level = ?, cooking_level = ?, woodcutting_level = ?,
                    firemaking_level = ?, crafting_level = ?, fletching_level = ?,
                    herblore_level = ?, agility_level = ?, thieving_level = ?,
                    slayer_level = ?, farming_level = ?, runecrafting_level = ?,
                    construction_level = ?, hunter_level = ?,
                    attack_xp = ?, strength_xp = ?, defence_xp = ?,
                    ranged_xp = ?, magic_xp = ?, prayer_xp = ?,
                    hitpoints_xp = ?, mining_xp = ?, smithing_xp = ?,
                    fishing_xp = ?, cooking_xp = ?, woodcutting_xp = ?,
                    firemaking_xp = ?, crafting_xp = ?, fletching_xp = ?,
                    herblore_xp = ?, agility_xp = ?, thieving_xp = ?,
                    slayer_xp = ?, farming_xp = ?, runecrafting_xp = ?,
                    construction_xp = ?, hunter_xp = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE player_id = ?
                """,
                (
                    stats.attack,
                    stats.strength,
                    stats.defence,
                    stats.ranged,
                    stats.magic,
                    stats.prayer,
                    stats.hitpoints,
                    stats.mining,
                    stats.smithing,
                    stats.fishing,
                    stats.cooking,
                    stats.woodcutting,
                    stats.firemaking,
                    stats.crafting,
                    stats.fletching,
                    stats.herblore,
                    stats.agility,
                    stats.thieving,
                    stats.slayer,
                    stats.farming,
                    stats.runecrafting,
                    stats.construction,
                    stats.hunter,
                    stats.attack_xp,
                    stats.strength_xp,
                    stats.defence_xp,
                    stats.ranged_xp,
                    stats.magic_xp,
                    stats.prayer_xp,
                    stats.hitpoints_xp,
                    stats.mining_xp,
                    stats.smithing_xp,
                    stats.fishing_xp,
                    stats.cooking_xp,
                    stats.woodcutting_xp,
                    stats.firemaking_xp,
                    stats.crafting_xp,
                    stats.fletching_xp,
                    stats.herblore_xp,
                    stats.agility_xp,
                    stats.thieving_xp,
                    stats.slayer_xp,
                    stats.farming_xp,
                    stats.runecrafting_xp,
                    stats.construction_xp,
                    stats.hunter_xp,
                    player_id,
                ),
            )

    def record_combat(
        self,
        player_id: int,
        opponent_type: str,
        opponent_id: int,
        winner_id: int,
        total_damage_dealt: int,
        total_damage_taken: int,
        experience_gained: float,
        drops: List[Dict[str, Any]],
    ) -> int:
        """Record a combat encounter."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO combat_history (
                    player_id, opponent_type, opponent_id, winner_id,
                    total_damage_dealt, total_damage_taken,
                    experience_gained, drops_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    player_id,
                    opponent_type,
                    opponent_id,
                    winner_id,
                    total_damage_dealt,
                    total_damage_taken,
                    experience_gained,
                    json.dumps(drops),
                ),
            )
            return cursor.fetchone()[0]

    def record_combat_hit(
        self,
        combat_id: int,
        attacker_id: int,
        defender_id: int,
        damage: int,
        hit_type: str,
        accuracy: float,
        max_hit: int,
    ):
        """Record a combat hit."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO combat_hits (
                    combat_id, attacker_id, defender_id,
                    damage, hit_type, accuracy, max_hit
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (combat_id, attacker_id, defender_id, damage, hit_type, accuracy, max_hit),
            )

    def get_combat_history(self, player_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent combat history for a player."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM combat_history
                WHERE player_id = ?
                ORDER BY start_time DESC
                LIMIT ?
                """,
                (player_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_hiscores(
        self, skill: Optional[str] = None, limit: int = 10
    ) -> List[Tuple[str, int, float]]:
        """Get hiscores for total level or a specific skill."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if skill:
                # Get hiscores for specific skill
                cursor.execute(
                    f"""
                    SELECT p.username, ps.{skill}_level, ps.{skill}_xp
                    FROM player_stats ps
                    JOIN players p ON p.id = ps.player_id
                    ORDER BY ps.{skill}_xp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            else:
                # Get hiscores for total level
                cursor.execute(
                    """
                    SELECT 
                        p.username,
                        (
                            ps.attack_level + ps.strength_level + ps.defence_level +
                            ps.ranged_level + ps.magic_level + ps.prayer_level +
                            ps.hitpoints_level + ps.mining_level + ps.smithing_level +
                            ps.fishing_level + ps.cooking_level + ps.woodcutting_level +
                            ps.firemaking_level + ps.crafting_level + ps.fletching_level +
                            ps.herblore_level + ps.agility_level + ps.thieving_level +
                            ps.slayer_level + ps.farming_level + ps.runecrafting_level +
                            ps.construction_level + ps.hunter_level
                        ) as total_level,
                        (
                            ps.attack_xp + ps.strength_xp + ps.defence_xp +
                            ps.ranged_xp + ps.magic_xp + ps.prayer_xp +
                            ps.hitpoints_xp + ps.mining_xp + ps.smithing_xp +
                            ps.fishing_xp + ps.cooking_xp + ps.woodcutting_xp +
                            ps.firemaking_xp + ps.crafting_xp + ps.fletching_xp +
                            ps.herblore_xp + ps.agility_xp + ps.thieving_xp +
                            ps.slayer_xp + ps.farming_xp + ps.runecrafting_xp +
                            ps.construction_xp + ps.hunter_xp
                        ) as total_xp
                    FROM player_stats ps
                    JOIN players p ON p.id = ps.player_id
                    ORDER BY total_xp DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            return [tuple(row) for row in cursor.fetchall()]
