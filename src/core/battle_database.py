"""Database handler for battle systems."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

from src.core.battle_manager import BattleType


class BattleDatabase:
    """Handles battle-related database operations."""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def record_battle(
        self,
        battle_id: str,
        battle_type: BattleType,
        challenger_id: int,
        opponent_id: int,
        winner_id: Optional[int],
        battle_data: Dict[str, Any],
    ) -> None:
        """Record a completed battle."""
        async with self.pool.acquire() as conn:
            # Record battle history
            await conn.execute(
                """
                INSERT INTO battle_history (
                    battle_id, battle_type, challenger_id, opponent_id,
                    winner_id, end_time, turns, battle_data
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                battle_id,
                battle_type.value,
                challenger_id,
                opponent_id,
                winner_id,
                datetime.now(),
                battle_data.get("turns", 0),
                battle_data,
            )

            # Update player stats
            for player_id in [challenger_id, opponent_id]:
                won = player_id == winner_id
                await self._update_player_stats(conn, player_id, battle_type, won)

    async def record_rewards(self, battle_id: str, player_id: int, rewards: Dict[str, Any]) -> None:
        """Record battle rewards."""
        await self.pool.execute(
            """
            INSERT INTO battle_rewards (
                battle_id, player_id, xp_gained, coins_gained,
                items_gained, special_rewards
            ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
            battle_id,
            player_id,
            rewards.get("xp", 0),
            rewards.get("coins", 0),
            rewards.get("items"),
            rewards.get("special_rewards"),
        )

    async def get_player_stats(self, player_id: int, battle_type: BattleType) -> Dict[str, Any]:
        """Get player's battle statistics."""
        return await self.pool.fetchrow(
            """
            SELECT * FROM battle_stats
            WHERE player_id = $1 AND battle_type = $2
            """,
            player_id,
            battle_type.value,
        )

    async def get_player_rating(self, player_id: int, battle_type: BattleType) -> Tuple[int, float]:
        """Get player's battle rating and uncertainty."""
        row = await self.pool.fetchrow(
            """
            SELECT rating, uncertainty FROM battle_ratings
            WHERE player_id = $1 AND battle_type = $2
            """,
            player_id,
            battle_type.value,
        )
        return row["rating"], row["uncertainty"] if row else (1000, 350.0)

    async def update_ratings(
        self,
        battle_type: BattleType,
        winner_id: int,
        loser_id: int,
        k_factor: float = 32.0,
    ) -> None:
        """Update players' ratings using ELO system."""
        async with self.pool.acquire() as conn:
            # Get current ratings
            winner_rating, _ = await self.get_player_rating(winner_id, battle_type)
            loser_rating, _ = await self.get_player_rating(loser_id, battle_type)

            # Calculate rating changes
            rating_diff = loser_rating - winner_rating
            exp_score = 1 / (1 + 10 ** (rating_diff / 400))
            rating_change = k_factor * (1 - exp_score)

            # Update ratings
            await conn.executemany(
                """
                INSERT INTO battle_ratings (player_id, battle_type, rating)
                VALUES ($1, $2, $3)
                ON CONFLICT (player_id, battle_type) DO UPDATE
                SET rating = battle_ratings.rating + $4,
                    uncertainty = GREATEST(50, battle_ratings.uncertainty * 0.95),
                    last_update = CURRENT_TIMESTAMP
                """,
                [
                    (winner_id, battle_type.value, 1000, rating_change),
                    (loser_id, battle_type.value, 1000, -rating_change),
                ],
            )

    async def check_achievements(
        self, player_id: int, battle_type: BattleType
    ) -> List[Dict[str, Any]]:
        """Check and award any newly completed achievements."""
        stats = await self.get_player_stats(player_id, battle_type)
        if not stats:
            return []

        achievements = []
        async with self.pool.acquire() as conn:
            # Get unearned achievements
            rows = await conn.fetch(
                """
                SELECT * FROM battle_achievements a
                WHERE battle_type = $1
                AND NOT EXISTS (
                    SELECT 1 FROM player_achievements pa
                    WHERE pa.achievement_id = a.achievement_id
                    AND pa.player_id = $2
                )
                """,
                battle_type.value,
                player_id,
            )

            for achievement in rows:
                # Check if requirement is met
                if stats[achievement["requirement_type"]] >= achievement["requirement_value"]:
                    # Award achievement
                    await conn.execute(
                        """
                        INSERT INTO player_achievements (player_id, achievement_id)
                        VALUES ($1, $2)
                        """,
                        player_id,
                        achievement["achievement_id"],
                    )
                    achievements.append(achievement)

        return achievements

    async def _update_player_stats(
        self,
        conn: asyncpg.Connection,
        player_id: int,
        battle_type: BattleType,
        won: bool,
    ) -> None:
        """Update player's battle statistics."""
        await conn.execute(
            """
            INSERT INTO battle_stats (
                player_id, battle_type, total_battles,
                wins, losses, win_streak, last_battle_time
            ) VALUES ($1, $2, 1, $3, $4, $5, CURRENT_TIMESTAMP)
            ON CONFLICT (player_id, battle_type) DO UPDATE
            SET total_battles = battle_stats.total_battles + 1,
                wins = battle_stats.wins + $3,
                losses = battle_stats.losses + $4,
                win_streak = CASE
                    WHEN $5 = 1 THEN battle_stats.win_streak + 1
                    ELSE 0
                END,
                highest_streak = GREATEST(
                    battle_stats.highest_streak,
                    CASE
                        WHEN $5 = 1 THEN battle_stats.win_streak + 1
                        ELSE battle_stats.win_streak
                    END
                ),
                last_battle_time = CURRENT_TIMESTAMP
            """,
            player_id,
            battle_type.value,
            1 if won else 0,
            0 if won else 1,
            1 if won else 0,
        )
