"""OSRS combat system implementation."""

import random
from typing import Optional, Dict, List
import discord
from discord.ext import commands
from datetime import datetime, timedelta

from src.osrs.models import Player, SkillType
from src.osrs.core.game_mechanics import CombatStyle
from src.osrs.core.game_math import calculate_max_hit, calculate_hit_chance


class CombatCommands(commands.Cog):
    """Combat-related commands for OSRS."""
    
    def __init__(self, bot):
        self.bot = bot
        self.combat_cooldowns: Dict[int, datetime] = {}
        self.COOLDOWN = 30  # seconds between combat actions
        
        self.combat_styles = {
            "accurate": CombatStyle(
                name="Accurate",
                attack_bonus=3,
                accuracy_multiplier=1.1,
                xp_type=SkillType.ATTACK
            ),
            "aggressive": CombatStyle(
                name="Aggressive",
                strength_bonus=3,
                damage_multiplier=1.1,
                xp_type=SkillType.STRENGTH
            ),
            "defensive": CombatStyle(
                name="Defensive",
                defence_bonus=3,
                defence_multiplier=1.1,
                xp_type=SkillType.DEFENCE
            ),
            "controlled": CombatStyle(
                name="Controlled",
                attack_bonus=1,
                strength_bonus=1,
                defence_bonus=1,
                xp_type=SkillType.SHARED
            )
        }
    
    @commands.group(invoke_without_command=True)
    async def combat(self, ctx):
        """Combat commands"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="⚔️ Combat Commands",
                description="OSRS Combat System",
                color=discord.Color.red()
            )
            
            commands = """
            `!combat train <style>` - Train combat skills
            `!combat stats` - View combat stats
            `!combat styles` - View combat styles
            `!combat attack <player>` - Attack another player
            """
            embed.add_field(name="Commands", value=commands, inline=False)
            
            await ctx.send(embed=embed)
    
    @combat.command(name="styles")
    async def show_styles(self, ctx):
        """Show available combat styles"""
        embed = discord.Embed(
            title="Combat Styles",
            color=discord.Color.blue()
        )
        
        for style_name, style in self.combat_styles.items():
            value = f"XP Type: {style.xp_type.value}\n"
            if style.attack_bonus:
                value += f"Attack Bonus: +{style.attack_bonus}\n"
            if style.strength_bonus:
                value += f"Strength Bonus: +{style.strength_bonus}\n"
            if style.defence_bonus:
                value += f"Defence Bonus: +{style.defence_bonus}\n"
            if style.accuracy_multiplier != 1.0:
                value += f"Accuracy Multiplier: x{style.accuracy_multiplier}\n"
            if style.damage_multiplier != 1.0:
                value += f"Damage Multiplier: x{style.damage_multiplier}\n"
                
            embed.add_field(
                name=style.name,
                value=value,
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @combat.command(name="train")
    async def train_combat(self, ctx, style: str):
        """Train combat skills using a specific style"""
        player = self.bot.get_player(ctx.author.id)
        if not player:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Validate combat style
        style = style.lower()
        if style not in self.combat_styles:
            return await ctx.send(
                f"Invalid combat style! Use `!combat styles` to see available styles."
            )
        
        # Check cooldown
        now = datetime.now()
        if ctx.author.id in self.combat_cooldowns:
            remaining = (self.combat_cooldowns[ctx.author.id] - now).total_seconds()
            if remaining > 0:
                return await ctx.send(
                    f"You can train again in {int(remaining)} seconds."
                )
        
        combat_style = self.combat_styles[style]
        
        # Calculate hits and XP
        max_hit = calculate_max_hit(
            player.skills[SkillType.STRENGTH].level + combat_style.strength_bonus,
            player.equipment.get_strength_bonus(),
            damage_multiplier=combat_style.damage_multiplier
        )
        
        accuracy = calculate_hit_chance(
            player.skills[SkillType.ATTACK].level + combat_style.attack_bonus,
            player.equipment.get_attack_bonus(),
            50,  # Training dummy defence level
            0,   # Training dummy defence bonus
            accuracy_multiplier=combat_style.accuracy_multiplier
        )
        
        # Simulate hits
        hits = []
        total_damage = 0
        for _ in range(3):  # 3 hits per training session
            if random.random() < accuracy:
                damage = random.randint(0, max_hit)
                hits.append(damage)
                total_damage += damage
            else:
                hits.append(0)
        
        # Calculate XP
        base_xp = total_damage * 4  # 4 XP per damage point
        if combat_style.xp_type == SkillType.SHARED:
            # Distribute XP among Attack, Strength, and Defence
            for skill in [SkillType.ATTACK, SkillType.STRENGTH, SkillType.DEFENCE]:
                old_level = player.skills[skill].level
                player.skills[skill].add_xp(base_xp // 3)
                if player.skills[skill].level > old_level:
                    await ctx.send(
                        f"Level up! {skill.value.title()}: "
                        f"{old_level} → {player.skills[skill].level}"
                    )
        else:
            # Add XP to specific skill
            old_level = player.skills[combat_style.xp_type].level
            player.skills[combat_style.xp_type].add_xp(base_xp)
            if player.skills[combat_style.xp_type].level > old_level:
                await ctx.send(
                    f"Level up! {combat_style.xp_type.value.title()}: "
                    f"{old_level} → {player.skills[combat_style.xp_type].level}"
                )
        
        # Create response embed
        embed = discord.Embed(
            title=f"Combat Training - {combat_style.name}",
            color=discord.Color.green()
        )
        
        hits_str = " | ".join(str(h) for h in hits)
        embed.add_field(name="Hits", value=hits_str, inline=False)
        embed.add_field(name="Total Damage", value=str(total_damage))
        embed.add_field(name="XP Gained", value=f"{base_xp:,}")
        
        # Set cooldown
        self.combat_cooldowns[ctx.author.id] = now + timedelta(seconds=self.COOLDOWN)
        
        await ctx.send(embed=embed)
    
    @combat.command(name="attack")
    async def attack_player(self, ctx, target: discord.Member):
        """Attack another player"""
        # Get attacker
        attacker = self.bot.get_player(ctx.author.id)
        if not attacker:
            return await ctx.send(
                "You don't have a character! Use `!osrs create <name>` to make one."
            )
        
        # Get target
        defender = self.bot.get_player(target.id)
        if not defender:
            return await ctx.send(f"{target.name} doesn't have a character!")
        
        # Check if in same world
        if not self.bot.world_manager.are_players_in_same_world(attacker, defender):
            return await ctx.send(f"{target.name} is in a different world!")
        
        # Check if in PvP area
        if not self.bot.world_manager.is_pvp_enabled(attacker):
            return await ctx.send("You must be in a PvP area to attack other players!")
        
        # Calculate combat stats
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
        if random.random() < accuracy:
            damage = random.randint(0, max_hit)
            
            # Apply damage
            old_hp = defender.skills[SkillType.HITPOINTS].level
            new_hp = max(0, old_hp - damage)
            defender.skills[SkillType.HITPOINTS].level = new_hp
            
            # Create response embed
            embed = discord.Embed(
                title="⚔️ PvP Combat",
                description=f"{ctx.author.name} attacks {target.name}!",
                color=discord.Color.red()
            )
            
            embed.add_field(name="Damage", value=str(damage))
            embed.add_field(
                name=f"{target.name}'s HP",
                value=f"{new_hp}/{old_hp}"
            )
            
            if new_hp == 0:
                embed.add_field(
                    name="K.O!",
                    value=f"{target.name} has been defeated!",
                    inline=False
                )
                # TODO: Handle death mechanics (item drops, respawn, etc)
        else:
            embed = discord.Embed(
                title="⚔️ PvP Combat",
                description=f"{ctx.author.name} attacks {target.name}!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Result", value="Miss!")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Set up the combat commands cog."""
    await bot.add_cog(CombatCommands(bot)) 