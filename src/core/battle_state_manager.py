"""Battle state persistence and management."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aioredis

from src.core.battle_manager import BattleState, BattleType


class BattleStateManager:
    """Manages battle state persistence and restoration."""

    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.BATTLE_KEY_PREFIX = "battle:"
        self.BATTLE_TIMEOUT = timedelta(minutes=30)

    async def save_battle_state(self, battle_state: BattleState) -> bool:
        """Save battle state to Redis."""
        try:
            key = f"{self.BATTLE_KEY_PREFIX}{battle_state.battle_id}"

            # Convert to serializable format
            state_data = {
                "battle_id": battle_state.battle_id,
                "battle_type": battle_state.battle_type.value,
                "challenger_id": battle_state.challenger_id,
                "opponent_id": battle_state.opponent_id,
                "current_turn": battle_state.current_turn,
                "start_time": battle_state.start_time.isoformat(),
                "is_finished": battle_state.is_finished,
                "winner_id": battle_state.winner_id,
                "battle_data": battle_state.battle_data,
            }

            # Save with expiration
            await self.redis.set(
                key, json.dumps(state_data), ex=int(self.BATTLE_TIMEOUT.total_seconds())
            )
            return True
        except Exception as e:
            print(f"Error saving battle state: {e}")
            return False

    async def load_battle_state(self, battle_id: str) -> Optional[BattleState]:
        """Load battle state from Redis."""
        try:
            key = f"{self.BATTLE_KEY_PREFIX}{battle_id}"
            if data := await self.redis.get(key):
                state_data = json.loads(data)

                # Convert back to BattleState
                return BattleState(
                    battle_id=state_data["battle_id"],
                    battle_type=BattleType(state_data["battle_type"]),
                    challenger_id=state_data["challenger_id"],
                    opponent_id=state_data["opponent_id"],
                    current_turn=state_data["current_turn"],
                    start_time=datetime.fromisoformat(state_data["start_time"]),
                    is_finished=state_data["is_finished"],
                    winner_id=state_data["winner_id"],
                    battle_data=state_data["battle_data"],
                )
        except Exception as e:
            print(f"Error loading battle state: {e}")
        return None

    async def delete_battle_state(self, battle_id: str) -> bool:
        """Delete battle state from Redis."""
        try:
            key = f"{self.BATTLE_KEY_PREFIX}{battle_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting battle state: {e}")
            return False

    async def get_active_battles(self) -> list[str]:
        """Get list of active battle IDs."""
        try:
            pattern = f"{self.BATTLE_KEY_PREFIX}*"
            keys = await self.redis.keys(pattern)
            return [k.decode().replace(self.BATTLE_KEY_PREFIX, "") for k in keys]
        except Exception as e:
            print(f"Error getting active battles: {e}")
            return []

    async def cleanup_expired_battles(self) -> int:
        """Clean up expired battle states."""
        try:
            pattern = f"{self.BATTLE_KEY_PREFIX}*"
            keys = await self.redis.keys(pattern)
            count = 0

            for key in keys:
                # Check if battle has timed out
                if data := await self.redis.get(key):
                    state_data = json.loads(data)
                    start_time = datetime.fromisoformat(state_data["start_time"])

                    if datetime.now() - start_time > self.BATTLE_TIMEOUT:
                        await self.redis.delete(key)
                        count += 1

            return count
        except Exception as e:
            print(f"Error cleaning up battles: {e}")
            return 0
