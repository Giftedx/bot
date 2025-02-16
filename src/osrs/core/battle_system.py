"""OSRS battle system implementation."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import random
import logging
import asyncio

from ..models.user import User
from .constants import SkillType
from .game_math import (
    calculate_max_hit,
    calculate_hit_chance,
    calculate_combat_level
)

logger = logging.getLogger(__name__)

class BattleSystem:
    """Manages combat and battles."""
    
    def __init__(self, bot):
        """Initialize battle system."""
        self.bot = bot
        self.active_battles: Dict[int, Dict] = {}  # battle_id -> battle_data
        self.battle_counter = 0

    async def initialize(self):
        """Initialize battle system."""
        # Load any saved battle state from database
        async with self.bot.db.pool.acquire() as conn:
            active_battles = await conn.fetch(
                "SELECT * FROM battle_history WHERE end_time IS NULL"
            )
            for battle in active_battles:
                self.active_battles[battle['battle_id']] = {
                    'challenger_id': battle['challenger_id'],
                    'opponent_id': battle['opponent_id'],
                    'battle_type': battle['battle_type'],
                    'start_time': battle['start_time'],
                    'battle_data': battle['battle_data']
                }

    async def start_battle(
        self,
        challenger_id: int,
        opponent_id: int,
        battle_type: str = "pvp"
    ) -> Optional[int]:
        """Start a new battle."""
        try:
            # Generate battle ID
            self.battle_counter += 1
            battle_id = self.battle_counter

            # Initialize battle data
            battle_data = {
                'challenger_id': challenger_id,
                'opponent_id': opponent_id,
                'battle_type': battle_type,
                'start_time': datetime.utcnow(),
                'turns': [],
                'status': 'active'
            }

            # Save to database
            async with self.bot.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO battle_history (
                        battle_id, battle_type, challenger_id,
                        opponent_id, start_time, battle_data
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    battle_id, battle_type, challenger_id,
                    opponent_id, battle_data['start_time'],
                    battle_data
                )

            self.active_battles[battle_id] = battle_data
            return battle_id

        except Exception as e:
            logger.error(f"Error starting battle: {e}")
            return None

    async def process_turn(
        self,
        battle_id: int,
        attacker_id: int,
        defender_id: int,
        combat_style: str
    ) -> Dict:
        """Process a battle turn."""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {'error': 'Battle not found'}

        attacker = self.bot.get_player(attacker_id)
        defender = self.bot.get_player(defender_id)
        if not attacker or not defender:
            return {'error': 'Player not found'}

        # Calculate hit
        max_hit = calculate_max_hit(
            attacker.skills[SkillType.STRENGTH].level,
            attacker.equipment.get_strength_bonus()
        )

        accuracy = calculate_hit_chance(
            attacker.skills[SkillType.ATTACK].level,
            attacker.equipment.get_attack_bonus(),
            defender.skills[SkillType.DEFENCE].level,
            defender.equipment.get_defence_bonus()
        )

        # Roll for hit
        hit = random.random() < accuracy
        damage = random.randint(0, max_hit) if hit else 0

        # Record turn
        turn_data = {
            'attacker_id': attacker_id,
            'defender_id': defender_id,
            'combat_style': combat_style,
            'accuracy': accuracy,
            'max_hit': max_hit,
            'damage': damage,
            'timestamp': datetime.utcnow()
        }

        battle['turns'].append(turn_data)

        # Update battle data in database
        async with self.bot.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE battle_history
                SET battle_data = $1
                WHERE battle_id = $2
                """,
                battle, battle_id
            )

        return turn_data

    async def end_battle(
        self,
        battle_id: int,
        winner_id: Optional[int] = None
    ) -> Dict:
        """End a battle and calculate rewards."""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {'error': 'Battle not found'}

        battle['status'] = 'completed'
        battle['end_time'] = datetime.utcnow()
        battle['winner_id'] = winner_id

        # Calculate statistics
        challenger_damage = sum(
            turn['damage']
            for turn in battle['turns']
            if turn['attacker_id'] == battle['challenger_id']
        )
        opponent_damage = sum(
            turn['damage']
            for turn in battle['turns']
            if turn['attacker_id'] == battle['opponent_id']
        )

        # Update database
        async with self.bot.db.pool.acquire() as conn:
            # Update battle history
            await conn.execute(
                """
                UPDATE battle_history
                SET end_time = $1,
                    winner_id = $2,
                    battle_data = $3
                WHERE battle_id = $4
                """,
                battle['end_time'], winner_id, battle, battle_id
            )

            # Update player statistics
            await conn.execute(
                """
                INSERT INTO battle_stats (
                    player_id, battle_type,
                    total_battles, wins, losses,
                    total_damage_dealt, total_damage_taken
                ) VALUES ($1, $2, 1, $3, $4, $5, $6)
                ON CONFLICT (player_id, battle_type)
                DO UPDATE SET
                    total_battles = battle_stats.total_battles + 1,
                    wins = battle_stats.wins + $3,
                    losses = battle_stats.losses + $4,
                    total_damage_dealt = battle_stats.total_damage_dealt + $5,
                    total_damage_taken = battle_stats.total_damage_taken + $6,
                    last_battle_time = CURRENT_TIMESTAMP
                """,
                battle['challenger_id'],
                battle['battle_type'],
                1 if winner_id == battle['challenger_id'] else 0,
                1 if winner_id == battle['opponent_id'] else 0,
                challenger_damage,
                opponent_damage
            )

            # Same for opponent
            await conn.execute(
                """
                INSERT INTO battle_stats (
                    player_id, battle_type,
                    total_battles, wins, losses,
                    total_damage_dealt, total_damage_taken
                ) VALUES ($1, $2, 1, $3, $4, $5, $6)
                ON CONFLICT (player_id, battle_type)
                DO UPDATE SET
                    total_battles = battle_stats.total_battles + 1,
                    wins = battle_stats.wins + $3,
                    losses = battle_stats.losses + $4,
                    total_damage_dealt = battle_stats.total_damage_dealt + $5,
                    total_damage_taken = battle_stats.total_damage_taken + $6,
                    last_battle_time = CURRENT_TIMESTAMP
                """,
                battle['opponent_id'],
                battle['battle_type'],
                1 if winner_id == battle['opponent_id'] else 0,
                1 if winner_id == battle['challenger_id'] else 0,
                opponent_damage,
                challenger_damage
            )

        # Calculate rewards
        rewards = self._calculate_rewards(battle)

        # Clean up
        del self.active_battles[battle_id]

        return {
            'battle_id': battle_id,
            'winner_id': winner_id,
            'duration': (battle['end_time'] - battle['start_time']).total_seconds(),
            'turns': len(battle['turns']),
            'challenger_damage': challenger_damage,
            'opponent_damage': opponent_damage,
            'rewards': rewards
        }

    def _calculate_rewards(self, battle: Dict) -> Dict:
        """Calculate battle rewards."""
        base_xp = 40  # Base XP per turn
        turns = len(battle['turns'])
        
        # Calculate XP rewards
        combat_xp = base_xp * turns
        
        # Bonus XP for winner
        winner_bonus = 1.5 if battle.get('winner_id') else 1.0
        
        challenger_rewards = {
            'xp': {
                'attack': combat_xp,
                'strength': combat_xp,
                'defence': combat_xp,
                'hitpoints': combat_xp // 2
            },
            'coins': 100 * turns
        }
        
        opponent_rewards = {
            'xp': {
                'attack': combat_xp,
                'strength': combat_xp,
                'defence': combat_xp,
                'hitpoints': combat_xp // 2
            },
            'coins': 100 * turns
        }
        
        # Apply winner bonus
        if battle.get('winner_id') == battle['challenger_id']:
            for skill in challenger_rewards['xp']:
                challenger_rewards['xp'][skill] *= winner_bonus
            challenger_rewards['coins'] *= winner_bonus
        elif battle.get('winner_id') == battle['opponent_id']:
            for skill in opponent_rewards['xp']:
                opponent_rewards['xp'][skill] *= winner_bonus
            opponent_rewards['coins'] *= winner_bonus
            
        return {
            'challenger': challenger_rewards,
            'opponent': opponent_rewards
        }

    async def get_battle_stats(
        self,
        player_id: int,
        battle_type: Optional[str] = None
    ) -> Dict:
        """Get player's battle statistics."""
        async with self.bot.db.pool.acquire() as conn:
            if battle_type:
                stats = await conn.fetchrow(
                    """
                    SELECT *
                    FROM battle_stats
                    WHERE player_id = $1 AND battle_type = $2
                    """,
                    player_id, battle_type
                )
            else:
                stats = await conn.fetchrow(
                    """
                    SELECT 
                        SUM(total_battles) as total_battles,
                        SUM(wins) as wins,
                        SUM(losses) as losses,
                        SUM(total_damage_dealt) as total_damage_dealt,
                        SUM(total_damage_taken) as total_damage_taken
                    FROM battle_stats
                    WHERE player_id = $1
                    GROUP BY player_id
                    """,
                    player_id
                )

            return dict(stats) if stats else {
                'total_battles': 0,
                'wins': 0,
                'losses': 0,
                'total_damage_dealt': 0,
                'total_damage_taken': 0
            }

    async def get_battle_history(
        self,
        player_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """Get player's recent battles."""
        async with self.bot.db.pool.acquire() as conn:
            battles = await conn.fetch(
                """
                SELECT *
                FROM battle_history
                WHERE challenger_id = $1 OR opponent_id = $1
                ORDER BY start_time DESC
                LIMIT $2
                """,
                player_id, limit
            )
            return [dict(battle) for battle in battles]

    async def get_leaderboard(
        self,
        battle_type: Optional[str] = None,
        stat: str = "wins",
        limit: int = 10
    ) -> List[Dict]:
        """Get battle leaderboard."""
        async with self.bot.db.pool.acquire() as conn:
            query = """
                SELECT 
                    player_id,
                    SUM(wins) as wins,
                    SUM(total_battles) as total_battles,
                    SUM(total_damage_dealt) as total_damage_dealt
                FROM battle_stats
            """
            
            if battle_type:
                query += " WHERE battle_type = $1"
                params = [battle_type]
            else:
                params = []
                
            query += f"""
                GROUP BY player_id
                ORDER BY {stat} DESC
                LIMIT $%d
            """ % (len(params) + 1)
            
            params.append(limit)
            
            leaders = await conn.fetch(query, *params)
            return [dict(leader) for leader in leaders] 