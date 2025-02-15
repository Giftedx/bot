"""OSRS game commands and features."""
import asyncio
import random
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta

try:
    import discord
    from discord.ext import commands
except ImportError:
    print("discord.py is not installed. Please install it with: pip install discord.py<2.0.0")
    raise

from src.osrs.models import Player, SkillType, Skill, Item, Equipment
from src.osrs.battle_system import OSRSBattleSystem
from src.osrs.core.game_math import calculate_max_hit, calculate_combat_level
from src.osrs.core.world_manager import WorldManager
from src.osrs.core.minigames import MinigameManager, MinigameType

class OSRSCommands(commands.Cog):
    """OSRS game commands and features."""

    def __init__(self, bot):
        self.bot = bot
        self.battle_system = OSRSBattleSystem()
        self.world_manager = WorldManager()
        self.active_battles = {}
        self.training_sessions = {}
        self.update_worlds.start()
        self.minigame_manager = MinigameManager()

        # Initialize Collection Log tables
        self.bot.loop.create_task(self._init_collection_log_tables())

    async def _init_collection_log_tables(self):
        """Initialize Collection Log database tables."""
        await self.bot.db.execute("""
            CREATE TABLE IF NOT EXISTS collection_log_categories (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)

        await self.bot.db.execute("""
            CREATE TABLE IF NOT EXISTS collection_log_items (
                id SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES collection_log_categories(id),
                name TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                rarity TEXT,
                UNIQUE(category_id, item_id)
            )
        """)

        await self.bot.db.execute("""
            CREATE TABLE IF NOT EXISTS player_collection_log (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                item_id INTEGER NOT NULL,
                obtained_at TIMESTAMP DEFAULT NULL,
                UNIQUE(user_id, item_id)
            )
        """)

        # Insert default categories if they don't exist
        categories = [
            ("Bosses", "Items obtained from boss monsters"),
            ("Raids", "Items obtained from raids"),
            ("Clue Scrolls", "Items obtained from clue scrolls"),
            ("Minigames", "Items obtained from minigames"),
            ("Other", "Miscellaneous collection log items")
        ]

        for name, description in categories:
            await self.bot.db.execute(
                """INSERT INTO collection_log_categories (name, description)
                   VALUES ($1, $2)
                   ON CONFLICT (name) DO NOTHING""",
                name, description
            )

    def cog_unload(self):
        self.update_worlds.cancel()

    @tasks.loop(minutes=5)
    async def update_worlds(self):
        """Update world information periodically."""
        await self.world_manager.update_worlds()

    @commands.hybrid_group()
    async def osrs(self, ctx: commands.Context):
        """OSRS commands group."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @osrs.command()
    async def create(self, ctx: commands.Context, name: str):
        """Create a new OSRS character."""
        # Check if player exists
        existing = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_players WHERE user_id = $1",
            ctx.author.id
        )
        if existing:
            return await ctx.send("You already have a character!")

        # Create player
        async with self.bot.db.transaction():
            await self.bot.db.execute(
                """INSERT INTO osrs_players (user_id, name)
                   VALUES ($1, $2)""",
                ctx.author.id, name
            )

            # Initialize skills
            for skill in SkillType:
                level = 10 if skill == SkillType.HITPOINTS else 1
                xp = Player.xp_for_level(level)
                await self.bot.db.execute(
                    """INSERT INTO osrs_skills (user_id, skill_name, level, xp)
                       VALUES ($1, $2, $3, $4)""",
                    ctx.author.id, skill.value, level, xp
                )

        await ctx.send(f"Created new character: **{name}**")

    @osrs.command()
    async def train(self, ctx: commands.Context, skill: str, minutes: int = 60):
        """Train a specific skill."""
        # Validate skill
        try:
            skill_type = SkillType(skill.lower())
        except ValueError:
            return await ctx.send(f"Invalid skill: {skill}")

        # Get player data
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Calculate XP rates based on level and method
        base_xp = self._calculate_xp_rate(skill_type, player.skills[skill_type].level)
        total_xp = base_xp * minutes

        # Update skill
        async with self.bot.db.transaction():
            await self.bot.db.execute(
                """UPDATE osrs_skills 
                   SET xp = xp + $1
                   WHERE user_id = $2 AND skill_name = $3""",
                total_xp, ctx.author.id, skill_type.value
            )

        await ctx.send(f"Gained {total_xp:,} XP in {skill_type.value}!")

    @osrs.command()
    async def stats(self, ctx: commands.Context, member: discord.Member = None):
        """Show player stats."""
        target = member or ctx.author
        player = await self._get_player(target.id)
        if not player:
            return await ctx.send("Player not found!")

        embed = discord.Embed(title=f"{player.name}'s Stats")
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)

        # Add combat stats
        combat_stats = ["attack", "strength", "defence", "hitpoints", "prayer", "magic", "ranged"]
        combat_text = ""
        for stat in combat_stats:
            skill = player.skills[SkillType(stat)]
            combat_text += f"{stat.title()}: {skill.level}\n"
        embed.add_field(name="Combat", value=combat_text)

        # Add skilling stats
        skill_text = ""
        for skill in SkillType:
            if skill.value not in combat_stats:
                level = player.skills[skill].level
                skill_text += f"{skill.value.title()}: {level}\n"
        embed.add_field(name="Skills", value=skill_text)

        # Add total level and combat level
        total_level = sum(skill.level for skill in player.skills.values())
        combat_level = player.get_combat_level()
        embed.add_field(name="Levels", value=f"Total Level: {total_level}\nCombat Level: {combat_level}")

        await ctx.send(embed=embed)

    @osrs.command()
    async def inventory(self, ctx: commands.Context):
        """Show inventory contents."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        items = await self.bot.db.fetch(
            """SELECT i.name, inv.quantity
               FROM osrs_inventory inv
               JOIN osrs_items i ON inv.item_id = i.item_id
               WHERE inv.user_id = $1
               ORDER BY inv.slot""",
            ctx.author.id
        )

        if not items:
            return await ctx.send("Your inventory is empty!")

        embed = discord.Embed(title=f"{player.name}'s Inventory")
        
        # Format items into a grid (4x7)
        inventory_text = ""
        for i, item in enumerate(items):
            if i > 0 and i % 4 == 0:
                inventory_text += "\n"
            inventory_text += f"{item['name']}({item['quantity']}) "

        embed.description = f"```{inventory_text}```"
        await ctx.send(embed=embed)

    @osrs.command()
    async def equipment(self, ctx: commands.Context):
        """Show equipped items."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        equipment = await self.bot.db.fetch(
            """SELECT e.slot_name, i.name
               FROM osrs_equipment e
               JOIN osrs_items i ON e.item_id = i.item_id
               WHERE e.user_id = $1""",
            ctx.author.id
        )

        embed = discord.Embed(title=f"{player.name}'s Equipment")
        
        for slot in ["weapon", "shield", "helmet", "body", "legs", "boots", "gloves", "amulet", "ring", "cape"]:
            item = next((e for e in equipment if e['slot_name'] == slot), None)
            embed.add_field(
                name=slot.title(),
                value=item['name'] if item else "Empty",
                inline=True
            )

        await ctx.send(embed=embed)

    @osrs.command()
    async def bank(self, ctx: commands.Context, page: int = 1):
        """Show bank contents."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        items_per_page = 24
        offset = (page - 1) * items_per_page

        items = await self.bot.db.fetch(
            """SELECT i.name, b.quantity, b.tab
               FROM osrs_bank b
               JOIN osrs_items i ON b.item_id = i.item_id
               WHERE b.user_id = $1
               ORDER BY b.tab, i.name
               LIMIT $2 OFFSET $3""",
            ctx.author.id, items_per_page, offset
        )

        if not items:
            return await ctx.send("Your bank is empty!" if page == 1 else "No items on this page!")

        embed = discord.Embed(title=f"{player.name}'s Bank - Page {page}")
        
        current_tab = None
        tab_text = ""
        
        for item in items:
            if item['tab'] != current_tab:
                if tab_text:
                    embed.add_field(name=f"Tab {current_tab}", value=tab_text, inline=False)
                current_tab = item['tab']
                tab_text = ""
            tab_text += f"{item['name']}: {item['quantity']:,}\n"

        if tab_text:
            embed.add_field(name=f"Tab {current_tab}", value=tab_text, inline=False)

        await ctx.send(embed=embed)

    @osrs.command()
    async def quests(self, ctx: commands.Context):
        """Show quest list and status."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        quests = await self.bot.db.fetch(
            """SELECT quest_name, status, progress
               FROM osrs_quests
               WHERE user_id = $1
               ORDER BY quest_name""",
            ctx.author.id
        )

        embed = discord.Embed(title=f"{player.name}'s Quest Log")
        
        # Group quests by status
        not_started = []
        in_progress = []
        completed = []
        
        for quest in quests:
            if quest['status'] == 'completed':
                completed.append(quest['quest_name'])
            elif quest['status'] == 'in_progress':
                in_progress.append(f"{quest['quest_name']} ({quest['progress']}%)")
            else:
                not_started.append(quest['quest_name'])

        if completed:
            embed.add_field(
                name="✅ Completed",
                value="\n".join(completed),
                inline=False
            )
        
        if in_progress:
            embed.add_field(
                name="⏳ In Progress",
                value="\n".join(in_progress),
                inline=False
            )
            
        if not_started:
            embed.add_field(
                name="❌ Not Started",
                value="\n".join(not_started),
                inline=False
            )

        # Add completion stats
        total = len(quests)
        completed_count = len(completed)
        completion_percent = (completed_count / total * 100) if total > 0 else 0
        
        embed.set_footer(text=f"Quest Completion: {completed_count}/{total} ({completion_percent:.1f}%)")
        await ctx.send(embed=embed)

    @osrs.command()
    async def start_quest(self, ctx: commands.Context, *, quest_name: str):
        """Start a new quest."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Check if quest exists and requirements are met
        quest_data = await self._get_quest_data(quest_name)
        if not quest_data:
            return await ctx.send(f"Quest '{quest_name}' not found!")

        # Check if already started/completed
        existing = await self.bot.db.fetchrow(
            """SELECT status FROM osrs_quests
               WHERE user_id = $1 AND quest_name = $2""",
            ctx.author.id, quest_name
        )
        
        if existing:
            if existing['status'] == 'completed':
                return await ctx.send("You've already completed this quest!")
            elif existing['status'] == 'in_progress':
                return await ctx.send("You've already started this quest!")

        # Check requirements
        if not await self._check_quest_requirements(ctx.author.id, quest_data['requirements']):
            reqs = self._format_requirements(quest_data['requirements'])
            return await ctx.send(f"You don't meet the requirements for this quest:\n{reqs}")

        # Start the quest
        await self.bot.db.execute(
            """INSERT INTO osrs_quests (user_id, quest_name, status, progress)
               VALUES ($1, $2, 'in_progress', 0)""",
            ctx.author.id, quest_name
        )

        embed = discord.Embed(
            title=f"Started Quest: {quest_name}",
            description=quest_data['description'],
            color=discord.Color.blue()
        )
        embed.add_field(name="Difficulty", value=quest_data['difficulty'])
        embed.add_field(name="Length", value=quest_data['length'])
        
        if quest_data['rewards']:
            embed.add_field(
                name="Rewards",
                value="\n".join(f"• {reward}" for reward in quest_data['rewards']),
                inline=False
            )

        await ctx.send(embed=embed)

    @osrs.command()
    async def quest_guide(self, ctx: commands.Context, *, quest_name: str):
        """Show detailed information about a quest."""
        quest_data = await self._get_quest_data(quest_name)
        if not quest_data:
            return await ctx.send(f"Quest '{quest_name}' not found!")

        embed = discord.Embed(
            title=f"Quest Guide: {quest_name}",
            description=quest_data['description']
        )
        
        # Add quest details
        embed.add_field(name="Difficulty", value=quest_data['difficulty'])
        embed.add_field(name="Length", value=quest_data['length'])
        embed.add_field(name="Quest Points", value=str(quest_data['points']))
        
        # Requirements
        if quest_data['requirements']:
            reqs = self._format_requirements(quest_data['requirements'])
            embed.add_field(name="Requirements", value=reqs, inline=False)
            
        # Items needed
        if quest_data['items']:
            items = "\n".join(f"• {item}" for item in quest_data['items'])
            embed.add_field(name="Items Needed", value=items, inline=False)
            
        # Rewards
        if quest_data['rewards']:
            rewards = "\n".join(f"• {reward}" for reward in quest_data['rewards'])
            embed.add_field(name="Rewards", value=rewards, inline=False)

        await ctx.send(embed=embed)

    @osrs.group(name="minigame")
    async def minigame(self, ctx: commands.Context):
        """Minigame commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a minigame command.")

    @minigame.command(name="list")
    async def list_minigames(self, ctx: commands.Context):
        """List available minigames."""
        embed = discord.Embed(title="OSRS Minigames")
        
        for game_type in MinigameType:
            reqs = self.minigame_manager.requirements[game_type]
            desc = []
            
            if 'combat_level' in reqs:
                desc.append(f"Combat Level: {reqs['combat_level']}")
            if 'skills' in reqs:
                for skill, level in reqs['skills'].items():
                    desc.append(f"{skill.title()}: {level}")
                    
            rewards = self.minigame_manager.rewards.get(game_type, {})
            if rewards:
                if 'points' in rewards:
                    desc.append(f"Rewards: {rewards['points'][0]}-{rewards['points'][1]} points")
                if 'tokens' in rewards:
                    desc.append(f"Rewards: {rewards['tokens'][0]}-{rewards['tokens'][1]} tokens")
                    
            embed.add_field(
                name=game_type.value.replace('_', ' ').title(),
                value="\n".join(desc) or "No special requirements",
                inline=False
            )
            
        await ctx.send(embed=embed)

    @minigame.command(name="start")
    async def start_minigame(self, ctx: commands.Context, minigame: str):
        """Start a minigame."""
        try:
            game_type = MinigameType(minigame.lower())
        except ValueError:
            return await ctx.send(f"Invalid minigame: {minigame}")
            
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Convert player data to stats dict
        stats = {
            'combat_level': player.get_combat_level(),
            'skills': {
                skill.value: level.level 
                for skill, level in player.skills.items()
            }
        }
            
        # Try to start minigame
        if error := await self.minigame_manager.start_minigame(
            game_type, ctx.author.id, stats
        ):
            return await ctx.send(f"Cannot start minigame: {error}")
            
        embed = discord.Embed(
            title=f"Started {game_type.value.replace('_', ' ').title()}",
            description="Use `!osrs minigame action <action>` to play!"
        )
        await ctx.send(embed=embed)

    @minigame.command(name="action")
    async def minigame_action(self, ctx: commands.Context, action: str):
        """Perform an action in current minigame."""
        result = await self.minigame_manager.process_minigame_tick(
            ctx.author.id, action
        )
        
        if 'error' in result:
            return await ctx.send(result['error'])
            
        embed = discord.Embed(title="Minigame Progress")
        
        if 'message' in result:
            embed.description = result['message']
            
        if 'points' in result:
            embed.add_field(name="Points", value=str(result['points']))
            
        if 'progress' in result:
            embed.add_field(name="Progress", value=f"{result['progress']}%")
            
        if 'rewards' in result:
            rewards = result['rewards']
            reward_text = []
            
            if rewards.xp:
                for skill, amount in rewards.xp.items():
                    reward_text.append(f"{amount:,} {skill.title()} XP")
            if rewards.points:
                reward_text.append(f"{rewards.points} points")
            if rewards.tokens:
                reward_text.append(f"{rewards.tokens} tokens")
            if rewards.items:
                for item in rewards.items:
                    for item_id, qty in item.items():
                        reward_text.append(f"{qty}x {item_id.replace('_', ' ').title()}")
                        
            embed.add_field(
                name="Rewards Earned",
                value="\n".join(reward_text),
                inline=False
            )
            
        await ctx.send(embed=embed)

    @minigame.command(name="leave")
    async def leave_minigame(self, ctx: commands.Context):
        """Leave current minigame."""
        if ctx.author.id not in self.minigame_manager.active_sessions:
            return await ctx.send("You're not in a minigame!")
            
        session = self.minigame_manager.active_sessions[ctx.author.id]
        game_type = session['type'].value.replace('_', ' ').title()
        
        self.minigame_manager._end_session(ctx.author.id)
        await ctx.send(f"Left {game_type}.")

    @minigame.command(name="fight_caves")
    async def fight_caves(self, ctx: commands.Context):
        """Start the Fight Caves minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check requirements
        if player.get_combat_level() < 70:
            return await ctx.send("You need at least combat level 70 to attempt the Fight Caves!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.FIGHT_CAVES,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Fight Caves: {error}")
            
        embed = discord.Embed(
            title="Fight Caves",
            description=(
                "You've entered the Fight Caves!\n"
                "Use `!osrs minigame action attack` to fight\n"
                "Use `!osrs minigame action pray` to restore prayer points"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="inferno")
    async def inferno(self, ctx: commands.Context):
        """Start the Inferno minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check requirements
        if player.get_combat_level() < 100:
            return await ctx.send("You need at least combat level 100 to attempt the Inferno!")
            
        # Check for fire cape
        has_fire_cape = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_bank b
               JOIN osrs_items i ON b.item_id = i.item_id
               WHERE b.user_id = $1 AND i.name = 'Fire cape'""",
            ctx.author.id
        )
        if not has_fire_cape:
            return await ctx.send("You need a Fire cape to attempt the Inferno!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.INFERNO,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Inferno: {error}")
            
        embed = discord.Embed(
            title="The Inferno",
            description=(
                "You've entered the Inferno!\n"
                "Use `!osrs minigame action attack` to fight\n"
                "Use `!osrs minigame action pray` to restore prayer points\n"
                "Stay behind Zuk's shield during the final wave!"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="nightmare")
    async def nightmare_zone(self, ctx: commands.Context):
        """Start the Nightmare Zone minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check requirements
        if player.get_combat_level() < 40:
            return await ctx.send("You need at least combat level 40 to enter the Nightmare Zone!")
            
        # Check quest bosses
        quest_count = await self.bot.db.fetchval(
            """SELECT COUNT(*) FROM osrs_quests
               WHERE user_id = $1 AND status = 'completed'""",
            ctx.author.id
        )
        if quest_count < 5:
            return await ctx.send("You need to complete at least 5 quests to access the Nightmare Zone!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.NIGHTMARE_ZONE,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Nightmare Zone: {error}")
            
        embed = discord.Embed(
            title="Nightmare Zone",
            description=(
                "Welcome to the Nightmare Zone!\n"
                "Use `!osrs minigame action attack` to fight bosses\n"
                "Use `!osrs minigame action absorb` to drink absorption potions"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="tempoross")
    async def tempoross(self, ctx: commands.Context):
        """Start the Tempoross minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check fishing level
        fishing_level = player.skills[SkillType.FISHING].level
        if fishing_level < 35:
            return await ctx.send("You need at least level 35 Fishing to face the Tempoross!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.TEMPOROSS,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Tempoross: {error}")
            
        embed = discord.Embed(
            title="Tempoross",
            description=(
                "You've arrived at the Tempoross!\n"
                "Use `!osrs minigame action fish` to catch fish\n"
                "Use `!osrs minigame action cook` to cook fish\n"
                "Use `!osrs minigame action attack` to weaken the storm"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="gauntlet")
    async def gauntlet(self, ctx: commands.Context):
        """Start the Gauntlet minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check quest requirement
        has_sote = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_quests
               WHERE user_id = $1 AND quest_name = 'Song of the Elves'
               AND status = 'completed'""",
            ctx.author.id
        )
        if not has_sote:
            return await ctx.send("You need to complete Song of the Elves to access the Gauntlet!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.GAUNTLET,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Gauntlet: {error}")
            
        embed = discord.Embed(
            title="The Gauntlet",
            description=(
                "You've entered the Gauntlet!\n"
                "Use `!osrs minigame action gather` to collect resources\n"
                "Use `!osrs minigame action craft` to craft equipment\n"
                "Use `!osrs minigame action attack` to fight the Hunllef"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="zalcano")
    async def zalcano(self, ctx: commands.Context):
        """Start the Zalcano minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check skill requirements
        if player.skills[SkillType.MINING].level < 70:
            return await ctx.send("You need level 70 Mining to fight Zalcano!")
        if player.skills[SkillType.SMITHING].level < 70:
            return await ctx.send("You need level 70 Smithing to fight Zalcano!")
        if player.skills[SkillType.RUNECRAFT].level < 70:
            return await ctx.send("You need level 70 Runecraft to fight Zalcano!")
            
        # Check quest requirement
        has_sote = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_quests
               WHERE user_id = $1 AND quest_name = 'Song of the Elves'
               AND status = 'completed'""",
            ctx.author.id
        )
        if not has_sote:
            return await ctx.send("You need to complete Song of the Elves to fight Zalcano!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.ZALCANO,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Zalcano: {error}")
            
        embed = discord.Embed(
            title="Zalcano",
            description=(
                "You've entered Zalcano's domain!\n"
                "Use `!osrs minigame action mine` to mine tephra\n"
                "Use `!osrs minigame action heat` to heat ores\n"
                "Use `!osrs minigame action smith` to refine ores\n"
                "Use `!osrs minigame action throw` to attack Zalcano\n"
                "Use `!osrs minigame action dodge` to dodge attacks"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="soul_wars")
    async def soul_wars(self, ctx: commands.Context, team: str = None):
        """Start the Soul Wars minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check combat level
        if player.get_combat_level() < 40:
            return await ctx.send("You need at least combat level 40 to play Soul Wars!")
            
        # Validate team choice
        if team and team.lower() not in ['blue', 'red']:
            return await ctx.send("Please choose either 'blue' or 'red' team!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.SOUL_WARS,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                },
                'team': team.lower() if team else random.choice(['blue', 'red'])
            }
        ):
            return await ctx.send(f"Cannot start Soul Wars: {error}")
            
        embed = discord.Embed(
            title="Soul Wars",
            description=(
                "Welcome to Soul Wars!\n"
                "Use `!osrs minigame action attack_players` for PvP combat\n"
                "Use `!osrs minigame action attack_slayer` to kill creatures\n"
                "Use `!osrs minigame action capture_obelisk` to capture the obelisk\n"
                "Use `!osrs minigame action attack_avatar` to attack enemy avatar\n"
                "Use `!osrs minigame action bury_bones` to restore prayer\n"
                "Use `!osrs minigame action use_bandages` to heal"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="mahogany_homes")
    async def mahogany_homes(self, ctx: commands.Context):
        """Start the Mahogany Homes minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check construction level
        if player.skills[SkillType.CONSTRUCTION].level < 20:
            return await ctx.send("You need level 20 Construction to start Mahogany Homes!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.MAHOGANY_HOMES,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Mahogany Homes: {error}")
            
        embed = discord.Embed(
            title="Mahogany Homes",
            description=(
                "Welcome to Mahogany Homes!\n"
                "Use `!osrs minigame action get_contract` to get a new contract\n"
                "Use `!osrs minigame action check_materials` to check your materials\n"
                "Use `!osrs minigame action add_materials` to get more materials\n"
                "Use `!osrs minigame action repair` to repair homes"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="hallowed_sepulchre")
    async def hallowed_sepulchre(self, ctx: commands.Context):
        """Start the Hallowed Sepulchre minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check agility level
        if player.skills[SkillType.AGILITY].level < 52:
            return await ctx.send("You need level 52 Agility to enter the Hallowed Sepulchre!")
            
        # Check quest requirement
        has_sotf = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_quests
               WHERE user_id = $1 AND quest_name = 'Sins of the Father'
               AND status = 'completed'""",
            ctx.author.id
        )
        if not has_sotf:
            return await ctx.send("You need to complete Sins of the Father to access the Hallowed Sepulchre!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.HALLOWED_SEPULCHRE,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Hallowed Sepulchre: {error}")
            
        embed = discord.Embed(
            title="Hallowed Sepulchre",
            description=(
                "Welcome to the Hallowed Sepulchre!\n"
                "Use `!osrs minigame action run_floor` to attempt floor obstacles\n"
                "Use `!osrs minigame action start_next_floor` to proceed to next floor\n"
                "Use `!osrs minigame action loot_coffin` to loot grand coffins\n"
                "Use `!osrs minigame action check_time` to check remaining time"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="fishing_trawler")
    async def fishing_trawler(self, ctx: commands.Context):
        """Start the Fishing Trawler minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check fishing level
        if player.skills[SkillType.FISHING].level < 15:
            return await ctx.send("You need level 15 Fishing to join the Fishing Trawler!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.FISHING_TRAWLER,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Fishing Trawler: {error}")
            
        embed = discord.Embed(
            title="Fishing Trawler",
            description=(
                "Welcome aboard Murphy's Fishing Trawler!\n"
                "Use `!osrs minigame action bail` to bail water\n"
                "Use `!osrs minigame action patch` to patch leaks\n"
                "Use `!osrs minigame action net` to fix the net\n"
                "Use `!osrs minigame action check_status` to check ship status\n"
                "Use `!osrs minigame action abandon` to abandon ship"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="barbarian_assault")
    async def barbarian_assault(self, ctx: commands.Context):
        """Start the Barbarian Assault minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check combat level
        if player.get_combat_level() < 40:
            return await ctx.send("You need a combat level of 40 to play Barbarian Assault!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.BARBARIAN_ASSAULT,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Barbarian Assault: {error}")
            
        embed = discord.Embed(
            title="Barbarian Assault",
            description=(
                "Welcome to Barbarian Assault!\n"
                "Choose your role:\n"
                "Use `!osrs minigame role attacker` to be an Attacker\n"
                "Use `!osrs minigame role defender` to be a Defender\n"
                "Use `!osrs minigame role healer` to be a Healer\n"
                "Use `!osrs minigame role collector` to be a Collector\n\n"
                "Use `!osrs minigame action call` to call out commands\n"
                "Use `!osrs minigame action attack` to attack Penance\n"
                "Use `!osrs minigame action collect` to collect eggs\n"
                "Use `!osrs minigame action heal` to heal teammates\n"
                "Use `!osrs minigame action status` to check wave status"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="trouble_brewing")
    async def trouble_brewing(self, ctx: commands.Context, team: str = None):
        """Start the Trouble Brewing minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check cooking level
        if player.skills[SkillType.COOKING].level < 40:
            return await ctx.send("You need level 40 Cooking to play Trouble Brewing!")
            
        # Check quest requirement
        has_cabin_fever = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_quests
               WHERE user_id = $1 AND quest_name = 'Cabin Fever'
               AND status = 'completed'""",
            ctx.author.id
        )
        if not has_cabin_fever:
            return await ctx.send("You need to complete Cabin Fever to play Trouble Brewing!")
            
        # Validate team choice
        if team and team.lower() not in ['blue', 'red']:
            return await ctx.send("Please choose either 'blue' or 'red' team!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.TROUBLE_BREWING,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                },
                'team': team.lower() if team else random.choice(['blue', 'red'])
            }
        ):
            return await ctx.send(f"Cannot start Trouble Brewing: {error}")
            
        embed = discord.Embed(
            title="Trouble Brewing",
            description=(
                "Welcome to Trouble Brewing!\n"
                "Use `!osrs minigame action get_water` to collect water\n"
                "Use `!osrs minigame action get_sugar` to collect sugar\n"
                "Use `!osrs minigame action get_hops` to collect hops\n"
                "Use `!osrs minigame action brew` to brew rum\n"
                "Use `!osrs minigame action make_stuff` to create The Stuff\n"
                "Use `!osrs minigame action sabotage` to sabotage the enemy team\n"
                "Use `!osrs minigame action repair` to repair damaged equipment"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="pyramid_plunder")
    async def pyramid_plunder(self, ctx: commands.Context):
        """Start the Pyramid Plunder minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check thieving level
        if player.skills[SkillType.THIEVING].level < 21:
            return await ctx.send("You need level 21 Thieving to enter the Pyramid!")
            
        # Check quest requirement
        has_quest = await self.bot.db.fetchval(
            """SELECT 1 FROM osrs_quests
               WHERE user_id = $1 AND quest_name = 'Icthlarin\'s Little Helper'
               AND status = 'completed'""",
            ctx.author.id
        )
        if not has_quest:
            return await ctx.send("You need to complete Icthlarin's Little Helper to enter the Pyramid!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.PYRAMID_PLUNDER,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Pyramid Plunder: {error}")
            
        embed = discord.Embed(
            title="Pyramid Plunder",
            description=(
                "Welcome to the Pyramid!\n"
                "Use `!osrs minigame action search_urn` to search urns\n"
                "Use `!osrs minigame action search_chest` to search chests\n"
                "Use `!osrs minigame action search_sarcophagus` to search sarcophagi\n"
                "Use `!osrs minigame action next_room` to move to the next room\n"
                "Use `!osrs minigame action check_time` to check remaining time"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="volcanic_mine")
    async def volcanic_mine(self, ctx: commands.Context):
        """Start the Volcanic Mine minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check mining level
        if player.skills[SkillType.MINING].level < 50:
            return await ctx.send("You need level 50 Mining to enter the Volcanic Mine!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.VOLCANIC_MINE,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                }
            }
        ):
            return await ctx.send(f"Cannot start Volcanic Mine: {error}")
            
        embed = discord.Embed(
            title="Volcanic Mine",
            description=(
                "Welcome to the Volcanic Mine!\n"
                "Use `!osrs minigame action mine` to mine volcanic rocks\n"
                "Use `!osrs minigame action cool` to cool down lava\n"
                "Use `!osrs minigame action repair` to repair supports\n"
                "Use `!osrs minigame action check_stability` to check mine stability\n"
                "Use `!osrs minigame action escape` to escape when stability is low"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="castle_wars")
    async def castle_wars(self, ctx: commands.Context, team: str = None):
        """Start the Castle Wars minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check combat level
        if player.get_combat_level() < 40:
            return await ctx.send("You need a combat level of 40 to play Castle Wars!")
            
        # Validate team choice
        if team and team.lower() not in ['zamorak', 'saradomin']:
            return await ctx.send("Please choose either 'zamorak' or 'saradomin' team!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.CASTLE_WARS,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                },
                'team': team.lower() if team else random.choice(['zamorak', 'saradomin'])
            }
        ):
            return await ctx.send(f"Cannot start Castle Wars: {error}")
            
        embed = discord.Embed(
            title="Castle Wars",
            description=(
                "Welcome to Castle Wars!\n"
                "Use `!osrs minigame action attack` to attack enemies\n"
                "Use `!osrs minigame action defend` to defend your castle\n"
                "Use `!osrs minigame action get_flag` to capture the enemy flag\n"
                "Use `!osrs minigame action use_barricade` to place barricades\n"
                "Use `!osrs minigame action use_explosive` to destroy barricades\n"
                "Use `!osrs minigame action use_bandages` to heal teammates\n"
                "Use `!osrs minigame action check_score` to check the current score"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="pest_control")
    async def pest_control(self, ctx: commands.Context, boat: str = "novice"):
        """Start the Pest Control minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check combat level requirements
        combat_level = player.get_combat_level()
        min_levels = {
            "novice": 40,
            "intermediate": 70,
            "veteran": 100
        }
        
        if boat not in min_levels:
            return await ctx.send("Please choose 'novice', 'intermediate', or 'veteran' boat!")
            
        if combat_level < min_levels[boat]:
            return await ctx.send(f"You need combat level {min_levels[boat]} for the {boat} boat!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.PEST_CONTROL,
            ctx.author.id,
            {
                'combat_level': combat_level,
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                },
                'boat': boat
            }
        ):
            return await ctx.send(f"Cannot start Pest Control: {error}")
            
        embed = discord.Embed(
            title=f"Pest Control - {boat.title()} Boat",
            description=(
                "Welcome to Pest Control!\n"
                "Use `!osrs minigame action attack_portal` to attack portals\n"
                "Use `!osrs minigame action attack_pests` to attack pests\n"
                "Use `!osrs minigame action repair` to repair barricades\n"
                "Use `!osrs minigame action defend_knight` to defend the Void Knight\n"
                "Use `!osrs minigame action check_status` to check game status"
            )
        )
        await ctx.send(embed=embed)

    @minigame.command(name="last_man_standing")
    async def last_man_standing(self, ctx: commands.Context, mode: str = "competitive"):
        """Start the Last Man Standing minigame."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Validate game mode
        valid_modes = ["competitive", "casual", "high_stakes"]
        if mode.lower() not in valid_modes:
            return await ctx.send("Please choose 'competitive', 'casual', or 'high_stakes' mode!")
            
        # Start minigame
        if error := await self.minigame_manager.start_minigame(
            MinigameType.LAST_MAN_STANDING,
            ctx.author.id,
            {
                'combat_level': player.get_combat_level(),
                'skills': {
                    skill.value: level.level 
                    for skill, level in player.skills.items()
                },
                'mode': mode.lower()
            }
        ):
            return await ctx.send(f"Cannot start Last Man Standing: {error}")
            
        embed = discord.Embed(
            title=f"Last Man Standing - {mode.replace('_', ' ').title()} Mode",
            description=(
                "Welcome to Last Man Standing!\n"
                "Use `!osrs minigame action attack` to attack other players\n"
                "Use `!osrs minigame action loot` to search for equipment\n"
                "Use `!osrs minigame action switch_gear` to change equipment\n"
                "Use `!osrs minigame action use_prayer` to toggle prayers\n"
                "Use `!osrs minigame action check_players` to see remaining players\n"
                "Use `!osrs minigame action check_fog` to check fog status"
            )
        )
        await ctx.send(embed=embed)

    @osrs.group(name="achievements")
    async def achievements(self, ctx: commands.Context):
        """Achievement commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify an achievements command.")

    @achievements.command(name="list")
    async def list_achievements(self, ctx: commands.Context, category: str = None):
        """List achievements, optionally filtered by category."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get player's achievements
        achievements = await self.bot.db.fetch(
            """SELECT a.name, a.category, a.description, a.points, pa.completed_at
               FROM osrs_achievements a
               LEFT JOIN player_achievements pa ON 
                   pa.achievement_id = a.id AND pa.user_id = $1
               ORDER BY a.category, a.points DESC""",
            ctx.author.id
        )

        if not achievements:
            return await ctx.send("No achievements found!")

        # Filter by category if specified
        if category:
            achievements = [a for a in achievements if a['category'].lower() == category.lower()]
            if not achievements:
                return await ctx.send(f"No achievements found in category: {category}")

        embed = discord.Embed(title=f"{player.name}'s Achievements")
        
        # Group by category
        current_category = None
        category_text = ""
        total_points = 0
        completed_points = 0
        
        for achievement in achievements:
            if achievement['category'] != current_category:
                if category_text:
                    embed.add_field(
                        name=f"{current_category} Achievements",
                        value=category_text,
                        inline=False
                    )
                current_category = achievement['category']
                category_text = ""
                
            # Format achievement entry
            status = "✅" if achievement['completed_at'] else "❌"
            points = achievement['points']
            total_points += points
            if achievement['completed_at']:
                completed_points += points
                
            category_text += (
                f"{status} **{achievement['name']}** ({points} pts)\n"
                f"└ {achievement['description']}\n"
            )
            
        # Add last category
        if category_text:
            embed.add_field(
                name=f"{current_category} Achievements",
                value=category_text,
                inline=False
            )
            
        # Add summary
        embed.set_footer(text=f"Total Achievement Points: {completed_points}/{total_points}")
        await ctx.send(embed=embed)

    @achievements.command(name="progress")
    async def achievement_progress(self, ctx: commands.Context, *, achievement_name: str):
        """Check progress towards a specific achievement."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get achievement details
        achievement = await self.bot.db.fetchrow(
            """SELECT a.*, pa.progress, pa.completed_at
               FROM osrs_achievements a
               LEFT JOIN player_achievements pa ON 
                   pa.achievement_id = a.id AND pa.user_id = $1
               WHERE LOWER(a.name) = LOWER($2)""",
            ctx.author.id, achievement_name
        )

        if not achievement:
            return await ctx.send(f"Achievement not found: {achievement_name}")

        embed = discord.Embed(
            title=f"Achievement Progress: {achievement['name']}",
            description=achievement['description']
        )
        
        # Add requirements if any
        if achievement['requirements']:
            embed.add_field(
                name="Requirements",
                value="\n".join(f"• {req}" for req in achievement['requirements']),
                inline=False
            )
            
        # Add progress
        if achievement['completed_at']:
            completed_date = achievement['completed_at'].strftime("%Y-%m-%d %H:%M:%S")
            embed.add_field(
                name="Status",
                value=f"✅ Completed on {completed_date}",
                inline=False
            )
        elif achievement['progress']:
            embed.add_field(
                name="Progress",
                value=f"{achievement['progress']}% complete",
                inline=False
            )
        else:
            embed.add_field(
                name="Status",
                value="❌ Not started",
                inline=False
            )
            
        # Add rewards
        if achievement['rewards']:
            embed.add_field(
                name="Rewards",
                value="\n".join(f"• {reward}" for reward in achievement['rewards']),
                inline=False
            )
            
        embed.set_footer(text=f"Achievement Points: {achievement['points']}")
        await ctx.send(embed=embed)

    @osrs.group(name="hiscores")
    async def hiscores(self, ctx: commands.Context):
        """Hiscores commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a hiscores command.")

    @hiscores.command(name="skills")
    async def skill_hiscores(self, ctx: commands.Context, skill: str = None):
        """View skill hiscores, optionally filtered by specific skill."""
        try:
            skill_type = SkillType(skill.lower()) if skill else None
        except ValueError:
            return await ctx.send(f"Invalid skill: {skill}")

        # Get top players
        query = """
            SELECT p.name, s.level, s.xp, s.skill_name
            FROM osrs_players p
            JOIN osrs_skills s ON p.user_id = s.user_id
        """
        
        if skill_type:
            query += " WHERE s.skill_name = $1"
            params = [skill_type.value]
        else:
            query += """ 
                WHERE s.skill_name IN (
                    SELECT skill_name FROM osrs_skills
                    GROUP BY skill_name
                    ORDER BY AVG(level) DESC
                    LIMIT 5
                )
            """
            params = []
            
        query += " ORDER BY s.level DESC, s.xp DESC LIMIT 10"
        
        rankings = await self.bot.db.fetch(query, *params)
        if not rankings:
            return await ctx.send("No hiscores data found!")

        embed = discord.Embed(
            title=f"OSRS Hiscores - {skill.title() if skill else 'Top Skills'}"
        )
        
        if skill_type:
            # Single skill ranking
            ranking_text = ""
            for i, rank in enumerate(rankings, 1):
                ranking_text += f"{i}. {rank['name']} - Level {rank['level']} ({rank['xp']:,} XP)\n"
            embed.description = ranking_text
        else:
            # Top 5 skills rankings
            current_skill = None
            ranking_text = ""
            
            for rank in rankings:
                if rank['skill_name'] != current_skill:
                    if ranking_text:
                        embed.add_field(
                            name=f"{current_skill.title()}",
                            value=ranking_text,
                            inline=False
                        )
                    current_skill = rank['skill_name']
                    ranking_text = ""
                    
                ranking_text += f"{rank['name']} - Level {rank['level']} ({rank['xp']:,} XP)\n"
                
            if ranking_text:
                embed.add_field(
                    name=f"{current_skill.title()}",
                    value=ranking_text,
                    inline=False
                )
                
        await ctx.send(embed=embed)

    @hiscores.command(name="minigames")
    async def minigame_hiscores(self, ctx: commands.Context, minigame: str = None):
        """View minigame hiscores, optionally filtered by specific minigame."""
        # Get top players
        query = """
            SELECT p.name, m.minigame_name, m.score, m.wins, m.games_played
            FROM osrs_players p
            JOIN player_minigame_stats m ON p.user_id = m.user_id
        """
        
        if minigame:
            query += " WHERE LOWER(m.minigame_name) = LOWER($1)"
            params = [minigame]
        else:
            params = []
            
        query += " ORDER BY m.score DESC LIMIT 10"
        
        rankings = await self.bot.db.fetch(query, *params)
        if not rankings:
            return await ctx.send("No hiscores data found!")

        embed = discord.Embed(
            title=f"OSRS Minigame Hiscores - {minigame.title() if minigame else 'All Minigames'}"
        )
        
        if minigame:
            # Single minigame ranking
            ranking_text = ""
            for i, rank in enumerate(rankings, 1):
                win_rate = (rank['wins'] / rank['games_played'] * 100) if rank['games_played'] > 0 else 0
                ranking_text += (
                    f"{i}. {rank['name']}\n"
                    f"└ Score: {rank['score']:,} | "
                    f"W/L: {rank['wins']}/{rank['games_played']} "
                    f"({win_rate:.1f}%)\n"
                )
            embed.description = ranking_text
        else:
            # Top minigames rankings
            current_minigame = None
            ranking_text = ""
            
            for rank in rankings:
                if rank['minigame_name'] != current_minigame:
                    if ranking_text:
                        embed.add_field(
                            name=current_minigame.replace('_', ' ').title(),
                            value=ranking_text,
                            inline=False
                        )
                    current_minigame = rank['minigame_name']
                    ranking_text = ""
                    
                win_rate = (rank['wins'] / rank['games_played'] * 100) if rank['games_played'] > 0 else 0
                ranking_text += (
                    f"{rank['name']}\n"
                    f"└ Score: {rank['score']:,} | "
                    f"W/L: {rank['wins']}/{rank['games_played']} "
                    f"({win_rate:.1f}%)\n"
                )
                
            if ranking_text:
                embed.add_field(
                    name=current_minigame.replace('_', ' ').title(),
                    value=ranking_text,
                    inline=False
                )
                
        await ctx.send(embed=embed)

    @hiscores.command(name="quests")
    async def quest_hiscores(self, ctx: commands.Context):
        """View quest completion hiscores."""
        # Get top players by quest completion
        rankings = await self.bot.db.fetch(
            """SELECT p.name,
                      COUNT(*) FILTER (WHERE q.status = 'completed') as completed,
                      COUNT(*) as total,
                      MAX(q.completed_at) as last_completion
               FROM osrs_players p
               JOIN osrs_quests q ON p.user_id = q.user_id
               GROUP BY p.user_id, p.name
               ORDER BY completed DESC, last_completion ASC
               LIMIT 10""",
        )

        if not rankings:
            return await ctx.send("No hiscores data found!")

        embed = discord.Embed(title="OSRS Quest Completion Hiscores")
        
        ranking_text = ""
        for i, rank in enumerate(rankings, 1):
            completion = (rank['completed'] / rank['total'] * 100)
            last_quest = rank['last_completion'].strftime("%Y-%m-%d") if rank['last_completion'] else "N/A"
            
            ranking_text += (
                f"{i}. {rank['name']}\n"
                f"└ {rank['completed']}/{rank['total']} quests "
                f"({completion:.1f}%) | Last: {last_quest}\n"
            )
            
        embed.description = ranking_text
        await ctx.send(embed=embed)

    @osrs.group(name="clue")
    async def clue(self, ctx: commands.Context):
        """Clue scroll commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @clue.command(name="start")
    async def start_clue(self, ctx: commands.Context, tier: str):
        """Start solving a clue scroll."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check if already has active clue
        active_clue = await self.bot.db.fetchval(
            """SELECT clue_id FROM osrs_player_clues
               WHERE user_id = $1 AND status = 'active'""",
            ctx.author.id
        )
        if active_clue:
            return await ctx.send("You already have an active clue scroll!")
            
        # Get clue scroll from inventory
        clue = await self.bot.db.fetchrow(
            """SELECT c.* FROM osrs_clues c
               JOIN osrs_inventory i ON i.item_id = c.item_id
               WHERE i.user_id = $1 AND c.tier = $2
               LIMIT 1""",
            ctx.author.id, tier.lower()
        )
        
        if not clue:
            return await ctx.send(f"You don't have a {tier} clue scroll!")
            
        # Remove from inventory and start clue
        async with self.bot.db.transaction():
            await self.bot.db.execute(
                """DELETE FROM osrs_inventory
                   WHERE user_id = $1 AND item_id = $2
                   LIMIT 1""",
                ctx.author.id, clue['item_id']
            )
            
            await self.bot.db.execute(
                """INSERT INTO osrs_player_clues (
                       user_id, clue_id, current_step, status
                   ) VALUES ($1, $2, 1, 'active')""",
                ctx.author.id, clue['id']
            )
            
        # Show first step
        step = await self._get_clue_step(clue['id'])
        embed = discord.Embed(title=f"{tier.title()} Clue Scroll")
        embed.description = step['description']
        await ctx.send(embed=embed)

    @clue.command(name="solve")
    async def solve_clue_step(self, ctx: commands.Context, *, answer: str):
        """Submit answer for current clue step."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Get active clue
        clue = await self.bot.db.fetchrow(
            """SELECT c.*, pc.current_step, pc.clue_id
               FROM osrs_player_clues pc
               JOIN osrs_clues c ON pc.clue_id = c.id
               WHERE pc.user_id = $1 AND pc.status = 'active'""",
            ctx.author.id
        )
        
        if not clue:
            return await ctx.send("You don't have an active clue scroll!")
            
        # Get current step
        step = await self._get_clue_step(clue['clue_id'])
        
        # Check requirements
        meets_reqs, message = await self._check_clue_requirements(ctx.author.id, step)
        if not meets_reqs:
            return await ctx.send(message)
            
        # Check answer
        if answer.lower() != step['answer'].lower():
            return await ctx.send("That's not the correct answer. Try again!")
            
        # Get total steps
        total_steps = await self.bot.db.fetchval(
            "SELECT COUNT(*) FROM osrs_clue_steps WHERE clue_id = $1",
            clue['clue_id']
        )
        
        # Update progress
        if clue['current_step'] == total_steps:
            # Clue completed - give reward
            async with self.bot.db.transaction():
                # Mark as completed
                await self.bot.db.execute(
                    """UPDATE osrs_player_clues
                       SET status = 'completed'
                       WHERE user_id = $1 AND clue_id = $2""",
                    ctx.author.id, clue['clue_id']
                )
                
                # Generate and give rewards
                rewards = await self._generate_clue_rewards(clue['tier'])
                for item_id, quantity in rewards.items():
                    await self._add_to_bank(ctx.author.id, item_id, quantity)
                    
                # Format reward message
                reward_text = ""
                for item_id, quantity in rewards.items():
                    item_name = await self.bot.db.fetchval(
                        "SELECT name FROM osrs_items WHERE id = $1",
                        item_id
                    )
                    reward_text += f"{quantity}x {item_name}\n"
                    
                embed = discord.Embed(
                    title="Clue Scroll Completed!",
                    description=f"Rewards:\n{reward_text}"
                )
                await ctx.send(embed=embed)
        else:
            # Move to next step
            await self.bot.db.execute(
                """UPDATE osrs_player_clues
                   SET current_step = current_step + 1
                   WHERE user_id = $1 AND clue_id = $2""",
                ctx.author.id, clue['clue_id']
            )
            
            # Show next step
            next_step = await self._get_clue_step(clue['clue_id'])
            embed = discord.Embed(
                title=f"{clue['tier'].title()} Clue Scroll",
                description=next_step['description']
            )
            await ctx.send(embed=embed)

    async def _generate_clue_rewards(self, tier: str) -> Dict[int, int]:
        """Generate rewards for a completed clue scroll."""
        rewards = {}
        
        # Get reward table for tier
        reward_table = await self.bot.db.fetch(
            """SELECT item_id, weight, min_quantity, max_quantity
               FROM osrs_clue_rewards
               WHERE tier = $1""",
            tier
        )
        
        # Calculate total weight
        total_weight = sum(r['weight'] for r in reward_table)
        
        # Determine number of reward rolls
        rolls = {
            'easy': 2,
            'medium': 3,
            'hard': 4,
            'elite': 5,
            'master': 6
        }[tier]
        
        # Roll for rewards
        for _ in range(rolls):
            roll = random.uniform(0, total_weight)
            current_weight = 0
            
            for reward in reward_table:
                current_weight += reward['weight']
                if roll <= current_weight:
                    # Determine quantity
                    quantity = random.randint(
                        reward['min_quantity'],
                        reward['max_quantity']
                    )
                    
                    # Add to rewards
                    if reward['item_id'] in rewards:
                        rewards[reward['item_id']] += quantity
                    else:
                        rewards[reward['item_id']] = quantity
                    break
                    
        return rewards

    @clue.command(name="drop")
    async def drop_clue(self, ctx: commands.Context):
        """Drop your active clue scroll."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Get active clue
        clue = await self.bot.db.fetchrow(
            """SELECT c.*, pc.clue_id
               FROM osrs_player_clues pc
               JOIN osrs_clues c ON pc.clue_id = c.id
               WHERE pc.user_id = $1 AND pc.status = 'active'""",
            ctx.author.id
        )
        
        if not clue:
            return await ctx.send("You don't have an active clue scroll!")
            
        # Drop clue
        await self.bot.db.execute(
            """UPDATE osrs_player_clues
               SET status = 'dropped'
               WHERE user_id = $1 AND clue_id = $2""",
            ctx.author.id, clue['clue_id']
        )
        
        await ctx.send(f"Dropped {clue['tier']} clue scroll.")

    @osrs.group(name="daily")
    async def daily(self, ctx: commands.Context):
        """Daily task commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a daily task command.")

    @daily.command(name="tasks")
    async def view_daily_tasks(self, ctx: commands.Context):
        """View your daily tasks."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get daily tasks
        tasks = await self.bot.db.fetch(
            """SELECT task_type, requirement, reward_type, reward_amount, completed_at
               FROM player_daily_tasks
               WHERE user_id = $1 AND DATE(created_at) = CURRENT_DATE""",
            ctx.author.id
        )

        if not tasks:
            # Generate new daily tasks
            tasks = self._generate_daily_tasks(player)
            for task in tasks:
                await self.bot.db.execute(
                    """INSERT INTO player_daily_tasks 
                       (user_id, task_type, requirement, reward_type, reward_amount)
                       VALUES ($1, $2, $3, $4, $5)""",
                    ctx.author.id, task['type'], task['requirement'],
                    task['reward_type'], task['reward_amount']
                )

        embed = discord.Embed(title=f"{player.name}'s Daily Tasks")
        
        for task in tasks:
            status = "✅" if task['completed_at'] else "❌"
            description = self._format_daily_task(task)
            reward = self._format_daily_reward(task)
            
            embed.add_field(
                name=f"{status} {task['task_type'].replace('_', ' ').title()}",
                value=f"{description}\nReward: {reward}",
                inline=False
            )
            
        # Add daily streak if any
        streak = await self.bot.db.fetchval(
            """SELECT daily_streak FROM osrs_players WHERE user_id = $1""",
            ctx.author.id
        )
        if streak:
            embed.set_footer(text=f"Daily Streak: {streak} days")
            
        await ctx.send(embed=embed)

    @daily.command(name="complete")
    async def complete_daily_task(self, ctx: commands.Context, task_number: int):
        """Complete a daily task."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get specified task
        tasks = await self.bot.db.fetch(
            """SELECT id, task_type, requirement, reward_type, reward_amount, completed_at
               FROM player_daily_tasks
               WHERE user_id = $1 AND DATE(created_at) = CURRENT_DATE
               ORDER BY id""",
            ctx.author.id
        )

        if not tasks:
            return await ctx.send("You have no daily tasks! Use `!osrs daily tasks` to generate them.")

        if task_number < 1 or task_number > len(tasks):
            return await ctx.send(f"Invalid task number. Choose between 1 and {len(tasks)}.")

        task = tasks[task_number - 1]
        if task['completed_at']:
            return await ctx.send("This task is already completed!")

        # Check if task requirements are met
        if not await self._check_daily_task_requirements(ctx.author.id, task):
            description = self._format_daily_task(task)
            return await ctx.send(f"You haven't completed this task yet!\n{description}")

        # Complete task and give rewards
        await self.bot.db.execute(
            """UPDATE player_daily_tasks 
               SET completed_at = NOW()
               WHERE id = $1""",
            task['id']
        )

        # Apply rewards
        if task['reward_type'] == 'xp':
            skill = task['requirement'].split()[0]
            await self.bot.db.execute(
                """UPDATE osrs_skills 
                   SET xp = xp + $1
                   WHERE user_id = $2 AND skill_name = $3""",
                task['reward_amount'], ctx.author.id, skill
            )
        elif task['reward_type'] == 'points':
            await self.bot.db.execute(
                """UPDATE osrs_players 
                   SET points = points + $1
                   WHERE user_id = $2""",
                task['reward_amount'], ctx.author.id
            )
        elif task['reward_type'] == 'item':
            await self.bot.db.execute(
                """INSERT INTO osrs_bank (user_id, item_id, quantity)
                   VALUES ($1, $2, $3)
                   ON CONFLICT (user_id, item_id) 
                   DO UPDATE SET quantity = osrs_bank.quantity + $3""",
                ctx.author.id, task['reward_amount'], 1
            )

        # Check if all daily tasks are completed
        all_completed = all(t['completed_at'] for t in tasks)
        if all_completed:
            # Update daily streak
            await self.bot.db.execute(
                """UPDATE osrs_players 
                   SET daily_streak = daily_streak + 1
                   WHERE user_id = $1""",
                ctx.author.id
            )

        embed = discord.Embed(
            title="Daily Task Completed!",
            description=f"Completed task: {self._format_daily_task(task)}"
        )
        embed.add_field(
            name="Reward",
            value=self._format_daily_reward(task),
            inline=False
        )
        
        if all_completed:
            streak = await self.bot.db.fetchval(
                """SELECT daily_streak FROM osrs_players WHERE user_id = $1""",
                ctx.author.id
            )
            embed.set_footer(text=f"All daily tasks completed! Daily streak: {streak} days")
            
        await ctx.send(embed=embed)

    @osrs.group(name="collection")
    async def collection(self, ctx: commands.Context):
        """Collection log commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Please specify a collection log command.")

    @collection.command(name="view")
    async def view_collection(self, ctx: commands.Context, category: str = None):
        """View collection log, optionally filtered by category."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get collection log entries
        entries = await self._get_category_items(ctx.author.id, category)

        embed = discord.Embed(title=f"{player.name}'s Collection Log")
        
        if not entries:
            if category:
                embed.description = f"No items found in category: {category}"
            else:
                embed.description = "Your collection log is empty!"
            return await ctx.send(embed=embed)

        # Group by category
        current_category = None
        category_text = ""
        total_items = 0
        obtained_items = 0
        
        for entry in entries:
            if entry['category'] != current_category:
                if category_text:
                    embed.add_field(
                        name=f"{current_category}",
                        value=category_text,
                        inline=False
                    )
                current_category = entry['category']
                category_text = ""
                
            status = "✅" if entry['obtained_at'] else "❌"
            total_items += 1
            if entry['obtained_at']:
                obtained_items += 1
                date = entry['obtained_at'].strftime("%Y-%m-%d")
                category_text += f"{status} {entry['item_name']} - {date}\n"
            else:
                category_text += f"{status} {entry['item_name']}\n"
            
        # Add last category
        if category_text:
            embed.add_field(
                name=f"{current_category}",
                value=category_text,
                inline=False
            )
            
        # Add completion percentage
        completion = (obtained_items / total_items * 100) if total_items > 0 else 0
        embed.set_footer(text=f"Completion: {obtained_items}/{total_items} ({completion:.1f}%)")
        
        await ctx.send(embed=embed)

    @collection.command(name="stats")
    async def collection_stats(self, ctx: commands.Context):
        """View collection log statistics."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get collection stats by category
        stats = await self._get_collection_log_stats(ctx.author.id)

        if not stats:
            return await ctx.send("No collection log data found!")

        embed = discord.Embed(title=f"{player.name}'s Collection Log Stats")
        
        total_obtained = 0
        total_items = 0
        
        for category, data in stats.items():
            completion = (data['obtained'] / data['total'] * 100) if data['total'] > 0 else 0
            total_obtained += data['obtained']
            total_items += data['total']
            
            embed.add_field(
                name=category,
                value=f"{data['obtained']}/{data['total']} ({completion:.1f}%)",
                inline=True
            )
            
        # Add total completion
        total_completion = (total_obtained / total_items * 100) if total_items > 0 else 0
        embed.description = f"Total Completion: {total_obtained}/{total_items} ({total_completion:.1f}%)"
        
        await ctx.send(embed=embed)

    @collection.command(name="recent")
    async def recent_collections(self, ctx: commands.Context, limit: int = 10):
        """View recently obtained collection log entries."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Get recent entries
        entries = await self._get_recent_collections(ctx.author.id, limit)

        if not entries:
            return await ctx.send("No collection log entries found!")

        embed = discord.Embed(title=f"{player.name}'s Recent Collections")
        
        for entry in entries:
            date = entry['obtained_at'].strftime("%Y-%m-%d %H:%M")
            embed.add_field(
                name=f"{entry['category']} - {date}",
                value=entry['item_name'],
                inline=False
            )
            
        await ctx.send(embed=embed)

    @collection.command(name="search")
    async def search_collection(self, ctx: commands.Context, *, query: str):
        """Search for items in your collection log."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")

        # Search for entries
        entries = await self._search_collection_log(ctx.author.id, query)

        if not entries:
            return await ctx.send(f"No collection log entries found matching: {query}")

        embed = discord.Embed(title=f"Collection Log Search: {query}")
        
        # Group by category
        current_category = None
        category_text = ""
        
        for entry in entries:
            if entry['category'] != current_category:
                if category_text:
                    embed.add_field(
                        name=current_category,
                        value=category_text,
                        inline=False
                    )
                current_category = entry['category']
                category_text = ""
                
            status = "✅" if entry['obtained_at'] else "❌"
            if entry['obtained_at']:
                date = entry['obtained_at'].strftime("%Y-%m-%d")
                category_text += f"{status} {entry['item_name']} - {date}\n"
            else:
                category_text += f"{status} {entry['item_name']}\n"
                
        # Add last category
        if category_text:
            embed.add_field(
                name=current_category,
                value=category_text,
                inline=False
            )
            
        await ctx.send(embed=embed)

    async def _get_player(self, user_id: int) -> Optional[Player]:
        """Get player data from database."""
        player_data = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_players WHERE user_id = $1",
            user_id
        )
        if not player_data:
            return None

        # Get skills
        skills = {}
        skill_data = await self.bot.db.fetch(
            "SELECT * FROM osrs_skills WHERE user_id = $1",
            user_id
        )
        for skill in skill_data:
            skill_type = SkillType(skill['skill_name'])
            skills[skill_type] = Skill(
                type=skill_type,
                level=skill['level'],
                xp=skill['xp']
            )

        return Player(
            id=user_id,
            name=player_data['name'],
            skills=skills
        )

    def _calculate_xp_rate(self, skill: SkillType, level: int) -> int:
        """Calculate XP rate for a skill based on level."""
        base_rates = {
            SkillType.WOODCUTTING: 25,
            SkillType.MINING: 30,
            SkillType.FISHING: 35,
            SkillType.ATTACK: 40,
            SkillType.STRENGTH: 40,
            SkillType.DEFENCE: 40,
            SkillType.RANGED: 45,
            SkillType.MAGIC: 50,
            # Add more skills with their base rates
        }

        base_rate = base_rates.get(skill, 20)
        return int(base_rate * (1 + level / 50))  # Scale with level

    async def _get_quest_data(self, quest_name: str) -> Optional[Dict]:
        """Get quest information from database."""
        # This would normally fetch from a quest database
        # For now, return example data
        return {
            'name': quest_name,
            'description': 'Example quest description',
            'difficulty': 'Intermediate',
            'length': 'Medium',
            'points': 2,
            'requirements': {
                'skills': {
                    'attack': 20,
                    'strength': 25,
                },
                'quests': ['Cook\'s Assistant']
            },
            'items': ['Bronze sword', 'Food', 'Combat gear'],
            'rewards': [
                '3 Quest Points',
                '5,000 Attack XP',
                'Access to new area'
            ]
        }

    async def _check_quest_requirements(
        self, 
        user_id: int, 
        requirements: Dict
    ) -> bool:
        """Check if player meets quest requirements."""
        # Check skill requirements
        if 'skills' in requirements:
            player = await self._get_player(user_id)
            if not player:
                return False
                
            for skill_name, required_level in requirements['skills'].items():
                skill_type = SkillType(skill_name)
                if player.skills[skill_type].level < required_level:
                    return False

        # Check quest requirements
        if 'quests' in requirements:
            for quest in requirements['quests']:
                status = await self.bot.db.fetchval(
                    """SELECT status FROM osrs_quests
                       WHERE user_id = $1 AND quest_name = $2
                       AND status = 'completed'""",
                    user_id, quest
                )
                if not status:
                    return False

        return True

    def _format_requirements(self, requirements: Dict) -> str:
        """Format quest requirements for display."""
        lines = []
        
        if 'skills' in requirements:
            for skill, level in requirements['skills'].items():
                lines.append(f"• {skill.title()} level {level}")
                
        if 'quests' in requirements:
            for quest in requirements['quests']:
                lines.append(f"• Complete '{quest}'")
                
        return "\n".join(lines)

    def _generate_clue_requirements(self, tier: str) -> Dict:
        """Generate random requirements for a clue step."""
        requirements = {}
        
        if tier in ["hard", "elite", "master"]:
            # Add skill requirements
            skill_reqs = {
                "hard": (60, 70),
                "elite": (75, 85),
                "master": (85, 95)
            }
            min_level, max_level = skill_reqs[tier]
            
            skill = random.choice(list(SkillType))
            requirements['skills'] = {
                skill.value: random.randint(min_level, max_level)
            }
            
        if tier in ["elite", "master"]:
            # Add quest requirements
            requirements['quests'] = [
                random.choice([
                    "Dragon Slayer",
                    "Monkey Madness",
                    "Desert Treasure",
                    "Recipe for Disaster"
                ])
            ]
            
        return requirements

    def _generate_clue_rewards(self, tier: str) -> List[Dict]:
        """Generate rewards for completing a clue scroll."""
        rewards = []
        
        # Number of reward items based on tier
        num_rewards = {
            "easy": random.randint(2, 4),
            "medium": random.randint(3, 5),
            "hard": random.randint(4, 6),
            "elite": random.randint(5, 7),
            "master": random.randint(6, 8)
        }[tier]
        
        # Example rewards (would be expanded with actual item database)
        possible_rewards = {
            "easy": [
                {"item_id": 1, "name": "Bronze arrows", "min": 10, "max": 50},
                {"item_id": 2, "name": "Steel arrows", "min": 5, "max": 25},
                {"item_id": 3, "name": "Coins", "min": 1000, "max": 5000}
            ],
            "medium": [
                {"item_id": 4, "name": "Adamant arrows", "min": 10, "max": 50},
                {"item_id": 5, "name": "Rune arrows", "min": 5, "max": 25},
                {"item_id": 6, "name": "Coins", "min": 5000, "max": 20000}
            ],
            # Add more tiers and rewards
        }
        
        for _ in range(num_rewards):
            reward = random.choice(possible_rewards.get(tier, possible_rewards["easy"]))
            quantity = random.randint(reward["min"], reward["max"])
            rewards.append({
                "item_id": reward["item_id"],
                "name": reward["name"],
                "quantity": quantity
            })
            
        return rewards

    async def _check_clue_requirements(self, user_id: int, requirements: Dict) -> bool:
        """Check if player meets clue step requirements."""
        if not requirements:
            return True
            
        # Check skill requirements
        if 'skills' in requirements:
            player = await self._get_player(user_id)
            if not player:
                return False
                
            for skill_name, required_level in requirements['skills'].items():
                skill_type = SkillType(skill_name)
                if player.skills[skill_type].level < required_level:
                    return False
                    
        # Check quest requirements
        if 'quests' in requirements:
            for quest in requirements['quests']:
                completed = await self.bot.db.fetchval(
                    """SELECT 1 FROM osrs_quests
                       WHERE user_id = $1 AND quest_name = $2
                       AND status = 'completed'""",
                    user_id, quest
                )
                if not completed:
                    return False
                    
        return True

    def _format_clue_requirements(self, requirements: Dict) -> str:
        """Format clue requirements for display."""
        lines = []
        
        if 'skills' in requirements:
            for skill, level in requirements['skills'].items():
                lines.append(f"• {skill.title()} level {level}")
                
        if 'quests' in requirements:
            for quest in requirements['quests']:
                lines.append(f"• Complete quest: {quest}")
                
        if not lines:
            lines.append("No special requirements")
            
        return "\n".join(lines)

    def _generate_daily_tasks(self, player: Player) -> List[Dict]:
        """Generate daily tasks for a player."""
        tasks = []
        
        # Pool of possible task types
        task_types = [
            # Skilling tasks
            {
                "type": "skill_training",
                "requirements": [
                    {"skill": "woodcutting", "amount": 100},
                    {"skill": "fishing", "amount": 100},
                    {"skill": "mining", "amount": 100}
                ],
                "rewards": [
                    {"type": "xp", "amount": 5000},
                    {"type": "points", "amount": 100}
                ]
            },
            # Combat tasks
            {
                "type": "combat",
                "requirements": [
                    {"monster": "goblin", "amount": 50},
                    {"monster": "skeleton", "amount": 30},
                    {"monster": "zombie", "amount": 30}
                ],
                "rewards": [
                    {"type": "xp", "amount": 10000},
                    {"type": "points", "amount": 200}
                ]
            },
            # Minigame tasks
            {
                "type": "minigame",
                "requirements": [
                    {"game": "castle_wars", "amount": 3},
                    {"game": "fishing_trawler", "amount": 2},
                    {"game": "pest_control", "amount": 2}
                ],
                "rewards": [
                    {"type": "points", "amount": 300},
                    {"type": "item", "amount": 1}
                ]
            }
        ]
        
        # Generate 3 random tasks
        for _ in range(3):
            task_type = random.choice(task_types)
            requirement = random.choice(task_type["requirements"])
            reward = random.choice(task_type["rewards"])
            
            tasks.append({
                "type": task_type["type"],
                "requirement": requirement,
                "reward_type": reward["type"],
                "reward_amount": reward["amount"]
            })
            
        return tasks

    def _format_daily_task(self, task: Dict) -> str:
        """Format a daily task for display."""
        if task['task_type'] == 'skill_training':
            skill, amount = task['requirement'].split()
            return f"Gain {amount} {skill.title()} XP"
            
        elif task['task_type'] == 'combat':
            monster, amount = task['requirement'].split()
            return f"Kill {amount} {monster.title()}s"
            
        elif task['task_type'] == 'minigame':
            game, amount = task['requirement'].split()
            return f"Complete {amount} games of {game.replace('_', ' ').title()}"
            
        return "Unknown task type"

    def _format_daily_reward(self, task: Dict) -> str:
        """Format a daily task reward for display."""
        if task['reward_type'] == 'xp':
            return f"{task['reward_amount']:,} XP"
            
        elif task['reward_type'] == 'points':
            return f"{task['reward_amount']:,} points"
            
        elif task['reward_type'] == 'item':
            # Would look up item name from database
            return f"Mystery item"
            
        return "Unknown reward type"

    async def _check_daily_task_requirements(self, user_id: int, task: Dict) -> bool:
        """Check if player has completed a daily task."""
        if task['task_type'] == 'skill_training':
            skill, amount = task['requirement'].split()
            xp_gained = await self.bot.db.fetchval(
                """SELECT COALESCE(SUM(xp_gained), 0)
                   FROM player_xp_gains
                   WHERE user_id = $1 
                   AND skill_name = $2
                   AND gained_at >= CURRENT_DATE""",
                user_id, skill
            )
            return xp_gained >= int(amount)
            
        elif task['task_type'] == 'combat':
            monster, amount = task['requirement'].split()
            kills = await self.bot.db.fetchval(
                """SELECT COALESCE(COUNT(*), 0)
                   FROM player_kills
                   WHERE user_id = $1 
                   AND monster_name = $2
                   AND killed_at >= CURRENT_DATE""",
                user_id, monster
            )
            return kills >= int(amount)
            
        elif task['task_type'] == 'minigame':
            game, amount = task['requirement'].split()
            games = await self.bot.db.fetchval(
                """SELECT COALESCE(COUNT(*), 0)
                   FROM player_minigame_games
                   WHERE user_id = $1 
                   AND minigame_name = $2
                   AND played_at >= CURRENT_DATE""",
                user_id, game
            )
            return games >= int(amount)
            
        return False

    async def _add_to_collection_log(self, user_id: int, item_id: int) -> bool:
        """Add an item to a player's collection log if not already obtained."""
        # Check if item exists in collection log items
        item_exists = await self.bot.db.fetchval(
            """SELECT 1 FROM collection_log_items 
               WHERE item_id = $1""",
            item_id
        )
        if not item_exists:
            return False

        # Add to player's collection log if not already there
        await self.bot.db.execute(
            """INSERT INTO player_collection_log (user_id, item_id, obtained_at)
               VALUES ($1, $2, NOW())
               ON CONFLICT (user_id, item_id) 
               DO UPDATE SET obtained_at = NOW()
               WHERE player_collection_log.obtained_at IS NULL""",
            user_id, item_id
        )
        return True

    async def _get_collection_log_stats(self, user_id: int) -> Dict:
        """Get collection log statistics for a player."""
        stats = await self.bot.db.fetch(
            """SELECT 
                   c.name as category,
                   COUNT(cli.id) as total,
                   COUNT(pcl.obtained_at) as obtained
               FROM collection_log_categories c
               JOIN collection_log_items cli ON cli.category_id = c.id
               LEFT JOIN player_collection_log pcl ON 
                   pcl.item_id = cli.item_id AND pcl.user_id = $1
               GROUP BY c.name
               ORDER BY c.name""",
            user_id
        )
        
        return {
            row['category']: {
                'total': row['total'],
                'obtained': row['obtained']
            }
            for row in stats
        }

    async def _get_recent_collections(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> List[Dict]:
        """Get recently obtained collection log items."""
        return await self.bot.db.fetch(
            """SELECT 
                   c.name as category,
                   cli.name as item_name,
                   pcl.obtained_at
               FROM player_collection_log pcl
               JOIN collection_log_items cli ON cli.item_id = pcl.item_id
               JOIN collection_log_categories c ON c.id = cli.category_id
               WHERE pcl.user_id = $1 AND pcl.obtained_at IS NOT NULL
               ORDER BY pcl.obtained_at DESC
               LIMIT $2""",
            user_id, limit
        )

    async def _search_collection_log(
        self, 
        user_id: int, 
        query: str
    ) -> List[Dict]:
        """Search for items in collection log."""
        return await self.bot.db.fetch(
            """SELECT 
                   c.name as category,
                   cli.name as item_name,
                   cli.rarity,
                   pcl.obtained_at
               FROM collection_log_items cli
               JOIN collection_log_categories c ON c.id = cli.category_id
               LEFT JOIN player_collection_log pcl ON 
                   pcl.item_id = cli.item_id AND pcl.user_id = $1
               WHERE LOWER(cli.name) LIKE LOWER($2)
               ORDER BY c.name, cli.name""",
            user_id, f"%{query}%"
        )

    async def _get_category_items(
        self, 
        user_id: int, 
        category: str = None
    ) -> List[Dict]:
        """Get collection log items, optionally filtered by category."""
        query = """
            SELECT 
                c.name as category,
                cli.name as item_name,
                cli.rarity,
                pcl.obtained_at
            FROM collection_log_items cli
            JOIN collection_log_categories c ON c.id = cli.category_id
            LEFT JOIN player_collection_log pcl ON 
                pcl.item_id = cli.item_id AND pcl.user_id = $1
        """
        
        params = [user_id]
        if category:
            query += " WHERE LOWER(c.name) = LOWER($2)"
            params.append(category)
            
        query += " ORDER BY c.name, cli.name"
        
        return await self.bot.db.fetch(query, *params)

    async def _handle_item_obtained(self, user_id: int, item_id: int, quantity: int = 1):
        """Handle when a player obtains an item that might be in the collection log."""
        # Add to collection log if it's a collection log item
        await self._add_to_collection_log(user_id, item_id)

        # Check for collection log milestones
        stats = await self._get_collection_log_stats(user_id)
        total_obtained = sum(data['obtained'] for data in stats.values())
        total_items = sum(data['total'] for data in stats.values())
        
        # Check for category completion
        for category, data in stats.items():
            if data['obtained'] == data['total'] and data['total'] > 0:
                # Category completed
                await self.bot.db.execute(
                    """INSERT INTO player_achievements (user_id, achievement_id, completed_at)
                       SELECT $1, a.id, NOW()
                       FROM achievements a
                       WHERE a.name = $2
                       AND NOT EXISTS (
                           SELECT 1 FROM player_achievements pa
                           WHERE pa.user_id = $1 AND pa.achievement_id = a.id
                       )""",
                    user_id, f"Complete {category} Collection Log"
                )
        
        # Check for total completion milestones
        milestones = [25, 50, 75, 100, 200, 500, 1000]
        completion_percent = (total_obtained / total_items * 100) if total_items > 0 else 0
        
        for milestone in milestones:
            if completion_percent >= milestone:
                # Milestone reached
                await self.bot.db.execute(
                    """INSERT INTO player_achievements (user_id, achievement_id, completed_at)
                       SELECT $1, a.id, NOW()
                       FROM achievements a
                       WHERE a.name = $2
                       AND NOT EXISTS (
                           SELECT 1 FROM player_achievements pa
                           WHERE pa.user_id = $1 AND pa.achievement_id = a.id
                       )""",
                    user_id, f"Obtain {milestone}% of Collection Log"
                )

    async def _handle_loot_obtained(self, user_id: int, loot: Dict[int, int]):
        """Handle when a player obtains multiple items as loot."""
        for item_id, quantity in loot.items():
            await self._handle_item_obtained(user_id, item_id, quantity)

    async def _calculate_combat_bonuses(self, player_id: int) -> Dict[str, int]:
        """Calculate combat bonuses from equipped items."""
        bonuses = {
            'attack_stab': 0, 'attack_slash': 0, 'attack_crush': 0, 'attack_magic': 0, 'attack_range': 0,
            'defence_stab': 0, 'defence_slash': 0, 'defence_crush': 0, 'defence_magic': 0, 'defence_range': 0,
            'melee_strength': 0, 'ranged_strength': 0, 'magic_damage': 0,
            'prayer': 0
        }
        
        equipment = await self.bot.db.fetch(
            """SELECT i.bonuses
               FROM osrs_equipment e
               JOIN osrs_items i ON e.item_id = i.item_id
               WHERE e.user_id = $1""",
            player_id
        )
        
        for item in equipment:
            if item['bonuses']:
                for bonus_type, value in item['bonuses'].items():
                    bonuses[bonus_type] += value
                    
        return bonuses

    async def _calculate_max_hit(self, player_id: int, style: str) -> int:
        """Calculate max hit based on stats, equipment, and combat style."""
        player = await self._get_player(player_id)
        bonuses = await self._calculate_combat_bonuses(player_id)
        
        if style == 'melee':
            strength_level = player.skills[SkillType.STRENGTH].level
            return int((strength_level + 8) * (bonuses['melee_strength'] + 64) / 640)
        elif style == 'ranged':
            ranged_level = player.skills[SkillType.RANGED].level
            return int((ranged_level + 8) * (bonuses['ranged_strength'] + 64) / 640)
        elif style == 'magic':
            magic_level = player.skills[SkillType.MAGIC].level
            return int(magic_level * (bonuses['magic_damage'] + 64) / 640)
            
        return 0

    async def _calculate_accuracy(self, player_id: int, style: str, target_defence: int) -> float:
        """Calculate hit chance based on attack bonuses and target defence."""
        player = await self._get_player(player_id)
        bonuses = await self._calculate_combat_bonuses(player_id)
        
        if style == 'melee':
            attack_level = player.skills[SkillType.ATTACK].level
            attack_bonus = max(bonuses['attack_stab'], bonuses['attack_slash'], bonuses['attack_crush'])
            effective_attack = (attack_level + 8) * (attack_bonus + 64)
        elif style == 'ranged':
            ranged_level = player.skills[SkillType.RANGED].level
            attack_bonus = bonuses['attack_range']
            effective_attack = (ranged_level + 8) * (attack_bonus + 64)
        elif style == 'magic':
            magic_level = player.skills[SkillType.MAGIC].level
            attack_bonus = bonuses['attack_magic']
            effective_attack = (magic_level + 8) * (attack_bonus + 64)
        else:
            return 0.0
            
        effective_defence = (target_defence + 8) * 64
        
        if effective_attack > effective_defence:
            return 1 - (effective_defence + 2) / (2 * (effective_attack + 1))
        else:
            return effective_attack / (2 * (effective_defence + 1))

    @osrs.command()
    async def attack(self, ctx: commands.Context, target: discord.Member):
        """Attack another player in PvP."""
        attacker = await self._get_player(ctx.author.id)
        defender = await self._get_player(target.id)
        
        if not attacker or not defender:
            return await ctx.send("Both players need to have characters!")
            
        # Check if in PvP area
        if not await self.world_manager.is_pvp_area(attacker.location):
            return await ctx.send("You can only attack players in PvP areas!")
            
        # Calculate combat stats
        max_hit = await self._calculate_max_hit(ctx.author.id, 'melee')
        accuracy = await self._calculate_accuracy(
            ctx.author.id,
            'melee',
            defender.skills[SkillType.DEFENCE].level
        )
        
        # Determine if hit lands
        if random.random() > accuracy:
            await ctx.send(f"{ctx.author.name} missed their attack on {target.name}!")
            return
            
        # Calculate damage
        damage = random.randint(0, max_hit)
        
        # Apply damage
        await self.bot.db.execute(
            """UPDATE osrs_skills 
               SET current_hp = GREATEST(0, current_hp - $1)
               WHERE user_id = $2 AND skill_name = $3""",
            damage, target.id, SkillType.HITPOINTS.value
        )
        
        await ctx.send(f"{ctx.author.name} hit {target.name} for {damage} damage!")
        
        # Check if target died
        target_hp = await self.bot.db.fetchval(
            """SELECT current_hp FROM osrs_skills
               WHERE user_id = $1 AND skill_name = $2""",
            target.id, SkillType.HITPOINTS.value
        )
        
        if target_hp == 0:
            await ctx.send(f"{target.name} has been defeated!")
            # Handle death (drop items, teleport to respawn, etc.)
            await self._handle_player_death(target.id)

    async def _handle_player_death(self, player_id: int):
        """Handle what happens when a player dies."""
        # Restore HP to full
        player = await self._get_player(player_id)
        max_hp = player.skills[SkillType.HITPOINTS].level
        
        await self.bot.db.execute(
            """UPDATE osrs_skills 
               SET current_hp = $1
               WHERE user_id = $2 AND skill_name = $3""",
            max_hp, player_id, SkillType.HITPOINTS.value
        )
        
        # Teleport to respawn point (Lumbridge by default)
        await self.bot.db.execute(
            """UPDATE osrs_players
               SET location = 'lumbridge'
               WHERE user_id = $1""",
            player_id
        )
        
        # Drop items if not protected
        # TODO: Implement item dropping on death

    async def _check_achievement_task(self, player_id: int, task_id: int) -> Tuple[bool, str]:
        """Check if a player meets the requirements for an achievement task."""
        task = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_achievement_tasks WHERE id = $1",
            task_id
        )
        if not task:
            return False, "Task not found!"
            
        player = await self._get_player(player_id)
        
        # Check skill requirements
        if task['skill_requirement']:
            skill_type = SkillType(task['skill_requirement'])
            if player.skills[skill_type].level < task['level_requirement']:
                return False, f"You need level {task['level_requirement']} {skill_type.value}."
                
        # Check quest requirements
        if task['quest_requirement']:
            completed = await self.bot.db.fetchval(
                """SELECT EXISTS(
                       SELECT 1 FROM osrs_player_quests
                       WHERE user_id = $1 AND quest_id = $2 AND status = 'COMPLETED'
                   )""",
                player_id, task['quest_requirement']
            )
            if not completed:
                quest_name = await self.bot.db.fetchval(
                    "SELECT name FROM osrs_quests WHERE id = $1",
                    task['quest_requirement']
                )
                return False, f"You need to complete {quest_name} first."
                
        return True, "You meet all requirements!"

    @osrs.group()
    async def diary(self, ctx: commands.Context):
        """Achievement Diary commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @diary.command(name="list")
    async def diary_list(self, ctx: commands.Context):
        """Show list of Achievement Diaries."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Get all diaries and completed tasks
        diaries = await self.bot.db.fetch(
            "SELECT * FROM osrs_achievement_diaries ORDER BY area"
        )
        completed_tasks = await self.bot.db.fetch(
            """SELECT task_id FROM osrs_player_achievements
               WHERE user_id = $1""",
            ctx.author.id
        )
        completed_task_ids = [t['task_id'] for t in completed_tasks]
        
        embed = discord.Embed(title="Achievement Diaries")
        
        for diary in diaries:
            # Get tasks for this diary
            tasks = await self.bot.db.fetch(
                """SELECT * FROM osrs_achievement_tasks
                   WHERE diary_id = $1
                   ORDER BY difficulty, id""",
                diary['id']
            )
            
            # Group tasks by difficulty
            difficulties = ['Easy', 'Medium', 'Hard', 'Elite']
            diary_text = ""
            
            for diff in difficulties:
                diff_tasks = [t for t in tasks if t['difficulty'] == diff]
                if diff_tasks:
                    completed = len([t for t in diff_tasks if t['id'] in completed_task_ids])
                    total = len(diff_tasks)
                    diary_text += f"{diff}: {completed}/{total}\n"
                    
            embed.add_field(
                name=f"{diary['area']} Diary",
                value=diary_text,
                inline=True
            )
            
        await ctx.send(embed=embed)

    @diary.command(name="view")
    async def view_diary(self, ctx: commands.Context, *, area: str):
        """View tasks for a specific Achievement Diary."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Find diary
        diary = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_achievement_diaries WHERE LOWER(area) = LOWER($1)",
            area
        )
        if not diary:
            return await ctx.send("Diary not found!")
            
        # Get tasks and completion status
        tasks = await self.bot.db.fetch(
            """SELECT * FROM osrs_achievement_tasks
               WHERE diary_id = $1
               ORDER BY difficulty, id""",
            diary['id']
        )
        
        completed_tasks = await self.bot.db.fetch(
            """SELECT task_id FROM osrs_player_achievements
               WHERE user_id = $1""",
            ctx.author.id
        )
        completed_task_ids = [t['task_id'] for t in completed_tasks]
        
        embed = discord.Embed(title=f"{diary['area']} Achievement Diary")
        
        for difficulty in ['Easy', 'Medium', 'Hard', 'Elite']:
            diff_tasks = [t for t in tasks if t['difficulty'] == difficulty]
            if diff_tasks:
                task_text = ""
                for task in diff_tasks:
                    emoji = "✅" if task['id'] in completed_task_ids else "❌"
                    task_text += f"{emoji} {task['description']}\n"
                    
                embed.add_field(
                    name=f"{difficulty} Tasks",
                    value=task_text,
                    inline=False
                )
                
        # Add rewards section
        rewards = await self.bot.db.fetch(
            """SELECT * FROM osrs_achievement_rewards
               WHERE diary_id = $1
               ORDER BY difficulty""",
            diary['id']
        )
        
        if rewards:
            reward_text = ""
            for reward in rewards:
                reward_text += f"{reward['difficulty']}: {reward['description']}\n"
            embed.add_field(name="Rewards", value=reward_text, inline=False)
            
        await ctx.send(embed=embed)

    @diary.command(name="claim")
    async def claim_diary_reward(self, ctx: commands.Context, area: str, difficulty: str):
        """Claim rewards for completing a diary difficulty tier."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Validate difficulty
        difficulty = difficulty.title()
        if difficulty not in ['Easy', 'Medium', 'Hard', 'Elite']:
            return await ctx.send("Invalid difficulty! Must be Easy, Medium, Hard, or Elite.")
            
        # Find diary
        diary = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_achievement_diaries WHERE LOWER(area) = LOWER($1)",
            area
        )
        if not diary:
            return await ctx.send("Diary not found!")
            
        # Check if all tasks are completed
        tasks = await self.bot.db.fetch(
            """SELECT id FROM osrs_achievement_tasks
               WHERE diary_id = $1 AND difficulty = $2""",
            diary['id'], difficulty
        )
        
        completed_tasks = await self.bot.db.fetch(
            """SELECT task_id FROM osrs_player_achievements
               WHERE user_id = $1 AND task_id = ANY($2)""",
            ctx.author.id, [t['id'] for t in tasks]
        )
        
        if len(completed_tasks) < len(tasks):
            return await ctx.send(f"You haven't completed all {difficulty} tasks in the {diary['area']} diary!")
            
        # Check if already claimed
        already_claimed = await self.bot.db.fetchval(
            """SELECT EXISTS(
                   SELECT 1 FROM osrs_player_diary_rewards
                   WHERE user_id = $1 AND diary_id = $2 AND difficulty = $3
               )""",
            ctx.author.id, diary['id'], difficulty
        )
        
        if already_claimed:
            return await ctx.send(f"You have already claimed the {difficulty} rewards for the {diary['area']} diary!")
            
        # Get rewards
        rewards = await self.bot.db.fetchrow(
            """SELECT * FROM osrs_achievement_rewards
               WHERE diary_id = $1 AND difficulty = $2""",
            diary['id'], difficulty
        )
        
        # Grant rewards
        async with self.bot.db.transaction():
            # Mark as claimed
            await self.bot.db.execute(
                """INSERT INTO osrs_player_diary_rewards (user_id, diary_id, difficulty)
                   VALUES ($1, $2, $3)""",
                ctx.author.id, diary['id'], difficulty
            )
            
            # Add reward items to inventory
            if rewards['items']:
                for item_id, quantity in rewards['items'].items():
                    await self._add_to_inventory(ctx.author.id, item_id, quantity)
                    
            # Add experience rewards
            if rewards['experience']:
                for skill_id, xp in rewards['experience'].items():
                    await self.bot.db.execute(
                        """UPDATE osrs_skills
                           SET xp = xp + $1
                           WHERE user_id = $2 AND skill_name = $3""",
                        xp, ctx.author.id, SkillType(skill_id).value
                    )
                    
        await ctx.send(f"Claimed {difficulty} rewards for the {diary['area']} Achievement Diary!\n{rewards['description']}")

    async def _update_ge_prices(self):
        """Update Grand Exchange prices periodically."""
        # Get all tradeable items
        items = await self.bot.db.fetch(
            "SELECT * FROM osrs_items WHERE tradeable = true"
        )
        
        for item in items:
            # Calculate new price based on recent trades
            trades = await self.bot.db.fetch(
                """SELECT price FROM osrs_ge_history
                   WHERE item_id = $1
                   AND timestamp > NOW() - INTERVAL '24 hours'
                   ORDER BY timestamp DESC""",
                item['id']
            )
            
            if trades:
                avg_price = sum(t['price'] for t in trades) / len(trades)
                # Update guide price
                await self.bot.db.execute(
                    """UPDATE osrs_items
                       SET guide_price = $1,
                           last_price_update = NOW()
                       WHERE id = $2""",
                    int(avg_price), item['id']
                )

    @osrs.group()
    async def ge(self, ctx: commands.Context):
        """Grand Exchange commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ge.command(name="price")
    async def check_price(self, ctx: commands.Context, *, item_name: str):
        """Check the current Grand Exchange price of an item."""
        # Find item
        item = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_items WHERE LOWER(name) = LOWER($1) AND tradeable = true",
            item_name
        )
        if not item:
            return await ctx.send("Item not found or is not tradeable!")
            
        # Get price history
        history = await self.bot.db.fetch(
            """SELECT price, timestamp FROM osrs_ge_history
               WHERE item_id = $1
               AND timestamp > NOW() - INTERVAL '24 hours'
               ORDER BY timestamp DESC""",
            item['id']
        )
        
        embed = discord.Embed(title=f"{item['name']} - Grand Exchange Price")
        embed.add_field(name="Guide Price", value=f"{item['guide_price']:,} gp")
        
        if history:
            # Calculate price changes
            latest_price = history[0]['price']
            oldest_price = history[-1]['price']
            price_change = latest_price - oldest_price
            percent_change = (price_change / oldest_price) * 100
            
            embed.add_field(
                name="24h Change",
                value=f"{price_change:+,} gp ({percent_change:+.1f}%)"
            )
            
            # Add high/low prices
            high_price = max(h['price'] for h in history)
            low_price = min(h['price'] for h in history)
            embed.add_field(
                name="24h High/Low",
                value=f"High: {high_price:,} gp\nLow: {low_price:,} gp"
            )
            
        await ctx.send(embed=embed)

    @ge.command(name="buy")
    async def place_buy_order(self, ctx: commands.Context, item_name: str, quantity: int, price: int):
        """Place a buy order on the Grand Exchange."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Find item
        item = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_items WHERE LOWER(name) = LOWER($1) AND tradeable = true",
            item_name
        )
        if not item:
            return await ctx.send("Item not found or is not tradeable!")
            
        total_cost = quantity * price
        
        # Check if player has enough gold
        current_gold = await self.bot.db.fetchval(
            "SELECT coins FROM osrs_bank WHERE user_id = $1",
            ctx.author.id
        ) or 0
        
        if current_gold < total_cost:
            return await ctx.send(f"You need {total_cost:,} gp to place this order!")
            
        # Place order
        async with self.bot.db.transaction():
            # Remove gold
            await self.bot.db.execute(
                """UPDATE osrs_bank
                   SET coins = coins - $1
                   WHERE user_id = $2""",
                total_cost, ctx.author.id
            )
            
            # Create order
            await self.bot.db.execute(
                """INSERT INTO osrs_ge_orders (
                       user_id, item_id, quantity, price_each,
                       type, status, total_cost, quantity_filled
                   ) VALUES ($1, $2, $3, $4, 'buy', 'active', $5, 0)""",
                ctx.author.id, item['id'], quantity, price, total_cost
            )
            
        await ctx.send(
            f"Placed buy order for {quantity:,}x {item['name']} at {price:,} gp each "
            f"(Total: {total_cost:,} gp)"
        )
        
        # Try to match with existing sell orders
        await self._process_ge_orders(item['id'])

    @ge.command(name="sell")
    async def place_sell_order(self, ctx: commands.Context, item_name: str, quantity: int, price: int):
        """Place a sell order on the Grand Exchange."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Find item
        item = await self.bot.db.fetchrow(
            "SELECT * FROM osrs_items WHERE LOWER(name) = LOWER($1) AND tradeable = true",
            item_name
        )
        if not item:
            return await ctx.send("Item not found or is not tradeable!")
            
        # Check if player has the items
        item_count = await self.bot.db.fetchval(
            """SELECT quantity FROM osrs_bank
               WHERE user_id = $1 AND item_id = $2""",
            ctx.author.id, item['id']
        ) or 0
        
        if item_count < quantity:
            return await ctx.send(f"You don't have enough {item['name']}!")
            
        # Place order
        async with self.bot.db.transaction():
            # Remove items from bank
            await self.bot.db.execute(
                """UPDATE osrs_bank
                   SET quantity = quantity - $1
                   WHERE user_id = $2 AND item_id = $3""",
                quantity, ctx.author.id, item['id']
            )
            
            # Create order
            await self.bot.db.execute(
                """INSERT INTO osrs_ge_orders (
                       user_id, item_id, quantity, price_each,
                       type, status, quantity_filled
                   ) VALUES ($1, $2, $3, $4, 'sell', 'active', 0)""",
                ctx.author.id, item['id'], quantity, price
            )
            
        await ctx.send(
            f"Placed sell order for {quantity:,}x {item['name']} at {price:,} gp each "
            f"(Total: {quantity * price:,} gp)"
        )
        
        # Try to match with existing buy orders
        await self._process_ge_orders(item['id'])

    async def _process_ge_orders(self, item_id: int):
        """Process matching buy/sell orders for an item."""
        while True:
            # Find highest buy order and lowest sell order
            buy_order = await self.bot.db.fetchrow(
                """SELECT * FROM osrs_ge_orders
                   WHERE item_id = $1 AND type = 'buy' AND status = 'active'
                   ORDER BY price_each DESC, created_at ASC
                   LIMIT 1""",
                item_id
            )
            
            sell_order = await self.bot.db.fetchrow(
                """SELECT * FROM osrs_ge_orders
                   WHERE item_id = $1 AND type = 'sell' AND status = 'active'
                   ORDER BY price_each ASC, created_at ASC
                   LIMIT 1""",
                item_id
            )
            
            if not buy_order or not sell_order or buy_order['price_each'] < sell_order['price_each']:
                break
                
            # Calculate trade quantity
            quantity = min(
                buy_order['quantity'] - buy_order['quantity_filled'],
                sell_order['quantity'] - sell_order['quantity_filled']
            )
            
            # Execute trade
            async with self.bot.db.transaction():
                # Update orders
                for order in [buy_order, sell_order]:
                    await self.bot.db.execute(
                        """UPDATE osrs_ge_orders
                           SET quantity_filled = quantity_filled + $1,
                               status = CASE 
                                   WHEN quantity_filled + $1 = quantity THEN 'completed'
                                   ELSE status
                               END
                           WHERE id = $2""",
                        quantity, order['id']
                    )
                    
                # Transfer items to buyer
                await self._add_to_bank(buy_order['user_id'], item_id, quantity)
                
                # Transfer gold to seller
                trade_price = sell_order['price_each']
                trade_value = quantity * trade_price
                
                await self.bot.db.execute(
                    """UPDATE osrs_bank
                       SET coins = coins + $1
                       WHERE user_id = $2""",
                    trade_value, sell_order['user_id']
                )
                
                # Refund excess gold to buyer
                price_difference = buy_order['price_each'] - trade_price
                if price_difference > 0:
                    refund = quantity * price_difference
                    await self.bot.db.execute(
                        """UPDATE osrs_bank
                           SET coins = coins + $1
                           WHERE user_id = $2""",
                        refund, buy_order['user_id']
                    )
                    
                # Record trade in history
                await self.bot.db.execute(
                    """INSERT INTO osrs_ge_history (
                           item_id, quantity, price, buyer_id, seller_id
                       ) VALUES ($1, $2, $3, $4, $5)""",
                    item_id, quantity, trade_price,
                    buy_order['user_id'], sell_order['user_id']
                )
                
                # Notify users
                for user_id, order_type, amount in [
                    (buy_order['user_id'], 'bought', trade_value),
                    (sell_order['user_id'], 'sold', trade_value)
                ]:
                    user = self.bot.get_user(user_id)
                    if user:
                        item = await self.bot.db.fetchval(
                            "SELECT name FROM osrs_items WHERE id = $1",
                            item_id
                        )
                        await user.send(
                            f"GE Update: {order_type} {quantity:,}x {item} "
                            f"for {trade_price:,} gp each (Total: {amount:,} gp)"
                        )

    @ge.command(name="orders")
    async def view_orders(self, ctx: commands.Context):
        """View your active Grand Exchange orders."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        orders = await self.bot.db.fetch(
            """SELECT o.*, i.name as item_name
               FROM osrs_ge_orders o
               JOIN osrs_items i ON o.item_id = i.id
               WHERE o.user_id = $1 AND o.status = 'active'
               ORDER BY o.created_at DESC""",
            ctx.author.id
        )
        
        if not orders:
            return await ctx.send("You have no active orders!")
            
        embed = discord.Embed(title="Your Active GE Orders")
        
        for order in orders:
            remaining = order['quantity'] - order['quantity_filled']
            embed.add_field(
                name=f"{order['type'].title()} {order['item_name']}",
                value=(
                    f"Quantity: {remaining:,}/{order['quantity']:,}\n"
                    f"Price: {order['price_each']:,} gp each\n"
                    f"Total: {(remaining * order['price_each']):,} gp"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)

    @ge.command(name="cancel")
    async def cancel_order(self, ctx: commands.Context, order_id: int):
        """Cancel an active Grand Exchange order."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Find order
        order = await self.bot.db.fetchrow(
            """SELECT o.*, i.name as item_name
               FROM osrs_ge_orders o
               JOIN osrs_items i ON o.item_id = i.id
               WHERE o.id = $1 AND o.user_id = $2 AND o.status = 'active'""",
            order_id, ctx.author.id
        )
        
        if not order:
            return await ctx.send("Order not found or already completed!")
            
        # Cancel order
        async with self.bot.db.transaction():
            # Update order status
            await self.bot.db.execute(
                """UPDATE osrs_ge_orders
                   SET status = 'cancelled'
                   WHERE id = $1""",
                order_id
            )
            
            remaining = order['quantity'] - order['quantity_filled']
            
            if order['type'] == 'buy':
                # Refund remaining gold
                refund = remaining * order['price_each']
                await self.bot.db.execute(
                    """UPDATE osrs_bank
                       SET coins = coins + $1
                       WHERE user_id = $2""",
                    refund, ctx.author.id
                )
            else:  # sell order
                # Return remaining items
                await self._add_to_bank(ctx.author.id, order['item_id'], remaining)
                
        await ctx.send(
            f"Cancelled {order['type']} order for {remaining:,}x {order['item_name']} "
            f"at {order['price_each']:,} gp each"
        )

    async def _get_clue_step(self, clue_id: int) -> Dict:
        """Get the current step for a clue scroll."""
        return await self.bot.db.fetchrow(
            """SELECT cs.*, c.tier
               FROM osrs_clue_steps cs
               JOIN osrs_clues c ON cs.clue_id = c.id
               WHERE cs.clue_id = $1
               AND cs.step_number = (
                   SELECT current_step
                   FROM osrs_player_clues
                   WHERE clue_id = $1
               )""",
            clue_id
        )

    async def _check_clue_requirements(self, player_id: int, step: Dict) -> Tuple[bool, str]:
        """Check if a player meets the requirements for a clue step."""
        player = await self._get_player(player_id)
        
        # Check skill requirements
        if step['skill_requirement']:
            skill_type = SkillType(step['skill_requirement'])
            if player.skills[skill_type].level < step['level_requirement']:
                return False, f"You need level {step['level_requirement']} {skill_type.value}."
                
        # Check quest requirements
        if step['quest_requirement']:
            completed = await self.bot.db.fetchval(
                """SELECT EXISTS(
                       SELECT 1 FROM osrs_player_quests
                       WHERE user_id = $1 AND quest_id = $2 AND status = 'COMPLETED'
                   )""",
                player_id, step['quest_requirement']
            )
            if not completed:
                quest_name = await self.bot.db.fetchval(
                    "SELECT name FROM osrs_quests WHERE id = $1",
                    step['quest_requirement']
                )
                return False, f"You need to complete {quest_name} first."
                
        # Check item requirements
        if step['item_requirements']:
            for item_id, quantity in step['item_requirements'].items():
                item_count = await self.bot.db.fetchval(
                    """SELECT quantity FROM osrs_bank
                       WHERE user_id = $1 AND item_id = $2""",
                    player_id, item_id
                ) or 0
                
                if item_count < quantity:
                    item_name = await self.bot.db.fetchval(
                        "SELECT name FROM osrs_items WHERE id = $1",
                        item_id
                    )
                    return False, f"You need {quantity}x {item_name}."
                    
        return True, "You meet all requirements!"

    @osrs.group()
    async def clue(self, ctx: commands.Context):
        """Clue scroll commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @clue.command(name="start")
    async def start_clue(self, ctx: commands.Context, tier: str):
        """Start solving a clue scroll."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Check if already has active clue
        active_clue = await self.bot.db.fetchval(
            """SELECT clue_id FROM osrs_player_clues
               WHERE user_id = $1 AND status = 'active'""",
            ctx.author.id
        )
        if active_clue:
            return await ctx.send("You already have an active clue scroll!")
            
        # Get clue scroll from inventory
        clue = await self.bot.db.fetchrow(
            """SELECT c.* FROM osrs_clues c
               JOIN osrs_inventory i ON i.item_id = c.item_id
               WHERE i.user_id = $1 AND c.tier = $2
               LIMIT 1""",
            ctx.author.id, tier.lower()
        )
        
        if not clue:
            return await ctx.send(f"You don't have a {tier} clue scroll!")
            
        # Remove from inventory and start clue
        async with self.bot.db.transaction():
            await self.bot.db.execute(
                """DELETE FROM osrs_inventory
                   WHERE user_id = $1 AND item_id = $2
                   LIMIT 1""",
                ctx.author.id, clue['item_id']
            )
            
            await self.bot.db.execute(
                """INSERT INTO osrs_player_clues (
                       user_id, clue_id, current_step, status
                   ) VALUES ($1, $2, 1, 'active')""",
                ctx.author.id, clue['id']
            )
            
        # Show first step
        step = await self._get_clue_step(clue['id'])
        embed = discord.Embed(title=f"{tier.title()} Clue Scroll")
        embed.description = step['description']
        await ctx.send(embed=embed)

    @clue.command(name="solve")
    async def solve_clue_step(self, ctx: commands.Context, *, answer: str):
        """Submit answer for current clue step."""
        player = await self._get_player(ctx.author.id)
        if not player:
            return await ctx.send("You need to create a character first!")
            
        # Get active clue
        clue = await self.bot.db.fetchrow(
            """SELECT c.*, pc.current_step, pc.clue_id
               FROM osrs_player_clues pc
               JOIN osrs_clues c ON pc.clue_id = c.id
               WHERE pc.user_id = $1 AND pc.status = 'active'""",
            ctx.author.id
        )
        
        if not clue:
            return await ctx.send("You don't have an active clue scroll!")
            
        # Get current step
        step = await self._get_clue_step(clue['clue_id'])
        
        # Check requirements
        meets_reqs, message = await self._check_clue_requirements(ctx.author.id, step)
        if not meets_reqs:
            return await ctx.send(message)
            
        # Check answer
        if answer.lower() != step['answer'].lower():
            return await ctx.send("That's not the correct answer. Try again!")
            
        # Get total steps
        total_steps = await self.bot.db.fetchval(
            "SELECT COUNT(*) FROM osrs_clue_steps WHERE clue_id = $1",
            clue['clue_id']
        )
        
        # Update progress
        if clue['current_step'] == total_steps:
            # Clue completed - give reward
            async with self.bot.db.transaction():
                # Mark as completed
                await self.bot.db.execute(
                    """UPDATE osrs_player_clues
                       SET status = 'completed'
                       WHERE user_id = $1 AND clue_id = $2""",
                    ctx.author.id, clue['clue_id']
                )
                
                # Generate and give rewards
                rewards = await self._generate_clue_rewards(clue['tier'])
                for item_id, quantity in rewards.items():
                    await self._add_to_bank(ctx.author.id, item_id, quantity)
                    
                # Format reward message
                reward_text = ""
                for item_id, quantity in rewards.items():
                    item_name = await self.bot.db.fetchval(
                        "SELECT name FROM osrs_items WHERE id = $1",
                        item_id
                    )
                    reward_text += f"{quantity}x {item_name}\n"
                    
                embed = discord.Embed(
                    title="Clue Scroll Completed!",
                    description=f"Rewards:\n{reward_text}"
                )
                await ctx.send(embed=embed)
        else:
            # Move to next step
            await self.bot.db.execute(
                """UPDATE osrs_player_clues
                   SET current_step = current_step + 1
                   WHERE user_id = $1 AND clue_id = $2""",
                ctx.author.id, clue['clue_id']
            )
            
            # Show next step
            next_step = await self._get_clue_step(clue['clue_id'])
            embed = discord.Embed(
                title=f"{clue['tier'].title()} Clue Scroll",
                description=next_step['description']
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OSRSCommands(bot))
