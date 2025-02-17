from discord.ext import commands
from discord import Embed
from typing import Optional
from .mechanics import (
    CombatStats, Equipment, CombatFormulas,
    PrayerMultipliers, ExperienceTable,
    DropRates, AGILITY_COURSES,
    PotionBoosts, SpecialAttacks,
    calculate_run_energy_drain,
    EquipmentStats, NightmareZone,
    SlayerSystem, SuperiorSlayer,
    BarrowsSystem, GodwarsDungeon,
    Zulrah, Vorkath,
    ChambersOfXeric, TheatreOfBlood,
    WildernessSystem, ConstructionSystem, FarmingSystem,
    InfernoSystem, AchievementDiarySystem, ClueScrollSystem,
    WoodcuttingSystem, MiningSystem
)
import math

class OSRSCommands(commands.Cog):
    """OSRS game mechanics commands for Discord"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="combat")
    async def calculate_combat(self, ctx, attack: int, strength: int, defence: int,
                             ranged: int, magic: int, hitpoints: int, prayer: int):
        """Calculate combat level using real OSRS formula"""
        stats = CombatStats(attack, strength, defence, ranged, magic, hitpoints, prayer)
        combat_level = stats.calculate_combat_level()
        
        embed = Embed(title="Combat Level Calculator", color=0x00ff00)
        embed.add_field(name="Combat Level", value=str(combat_level), inline=False)
        embed.add_field(name="Stats", value=
            f"Attack: {attack}\n"
            f"Strength: {strength}\n"
            f"Defence: {defence}\n"
            f"Ranged: {ranged}\n"
            f"Magic: {magic}\n"
            f"Hitpoints: {hitpoints}\n"
            f"Prayer: {prayer}"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="maxhit")
    async def calculate_max_hit(self, ctx, base_level: int, 
                              effective_level: int, strength_bonus: int,
                              void: bool = False):
        """Calculate max hit using real OSRS formula"""
        void_bonus = 1.1 if void else 1.0
        max_hit = CombatFormulas.calculate_max_hit(
            base_level, effective_level, strength_bonus, void_bonus
        )
        
        embed = Embed(title="Max Hit Calculator", color=0x00ff00)
        embed.add_field(name="Max Hit", value=str(max_hit), inline=False)
        embed.add_field(name="Parameters", value=
            f"Base Level: {base_level}\n"
            f"Effective Level: {effective_level}\n"
            f"Strength Bonus: {strength_bonus}\n"
            f"Void Bonus: {'Yes' if void else 'No'}"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="xp")
    async def calculate_xp(self, ctx, level: int):
        """Calculate XP required for level"""
        xp = ExperienceTable.level_to_xp(level)
        
        embed = Embed(title="Experience Calculator", color=0x00ff00)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="Total XP Required", value=f"{xp:,}", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="droprate")
    async def calculate_drop_rate(self, ctx, base_chance: int, 
                                ring_of_wealth: bool = False,
                                kill_count: Optional[int] = None):
        """Calculate drop rate with modifiers"""
        chance = DropRates.calculate_drop_chance(base_chance, ring_of_wealth)
        
        embed = Embed(title="Drop Rate Calculator", color=0x00ff00)
        embed.add_field(name="Base Chance", value=f"1/{base_chance:,}", inline=True)
        embed.add_field(name="Modified Chance", 
                       value=f"1/{chance:,.2f}", inline=True)
        
        if kill_count is not None:
            pet_chance = DropRates.calculate_pet_chance(base_chance, kill_count)
            embed.add_field(name="Pet Chance", 
                          value=f"1/{pet_chance:,.2f}", inline=True)
            embed.add_field(name="Kill Count", value=str(kill_count), inline=True)
        
        embed.add_field(name="Ring of Wealth", 
                       value="Yes" if ring_of_wealth else "No", inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="prayer")
    async def show_prayer_bonuses(self, ctx, prayer_type: str):
        """Show prayer bonuses for a specific type"""
        prayer_type = prayer_type.lower()
        if prayer_type == "attack":
            prayers = PrayerMultipliers.ATTACK_PRAYERS
            title = "Attack Prayer Bonuses"
        elif prayer_type == "strength":
            prayers = PrayerMultipliers.STRENGTH_PRAYERS
            title = "Strength Prayer Bonuses"
        elif prayer_type == "defence":
            prayers = PrayerMultipliers.DEFENCE_PRAYERS
            title = "Defence Prayer Bonuses"
        elif prayer_type == "ranged":
            prayers = PrayerMultipliers.RANGED_PRAYERS
            title = "Ranged Prayer Bonuses"
        elif prayer_type == "magic":
            prayers = PrayerMultipliers.MAGIC_PRAYERS
            title = "Magic Prayer Bonuses"
        else:
            await ctx.send("Invalid prayer type. Choose: attack, strength, defence, ranged, magic")
            return
            
        embed = Embed(title=title, color=0x00ff00)
        for prayer, multiplier in prayers.items():
            bonus_percent = (multiplier - 1) * 100
            embed.add_field(name=prayer, 
                          value=f"+{bonus_percent:.1f}%", 
                          inline=True)
        await ctx.send(embed=embed)
    
    @commands.command(name="agility")
    async def show_agility_course(self, ctx, course_name: str):
        """Show information about an agility course"""
        course_name = course_name.title()
        if course_name not in AGILITY_COURSES:
            courses = ", ".join(AGILITY_COURSES.keys())
            await ctx.send(f"Invalid course name. Available courses: {courses}")
            return
            
        course = AGILITY_COURSES[course_name]
        total_xp = course.calculate_lap_xp()
        
        embed = Embed(title=f"{course.name} Agility Course", color=0x00ff00)
        embed.add_field(name="Level Required", 
                       value=str(course.level_required), 
                       inline=True)
        embed.add_field(name="Total Lap XP", 
                       value=f"{total_xp:,.1f}", 
                       inline=True)
        
        obstacles = "\n".join(
            f"{name}: {xp:,.1f} xp" for name, xp in course.obstacles
        )
        embed.add_field(name="Obstacles", value=obstacles, inline=False)
        
        if course.mark_of_grace_chance > 0:
            mark_chance = course.mark_of_grace_chance * 100
            embed.add_field(name="Mark of Grace Chance", 
                          value=f"{mark_chance:.1f}%", 
                          inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="accuracy")
    async def calculate_accuracy(self, ctx, attack_level: int, 
                               equipment_bonus: int, defence_level: int, 
                               defence_bonus: int):
        """Calculate hit chance using real OSRS formula"""
        attack_roll = CombatFormulas.calculate_accuracy_roll(
            attack_level, equipment_bonus
        )
        defence_roll = CombatFormulas.calculate_defence_roll(
            defence_level, defence_bonus
        )
        hit_chance = CombatFormulas.calculate_hit_chance(
            attack_roll, defence_roll
        )
        
        embed = Embed(title="Accuracy Calculator", color=0x00ff00)
        embed.add_field(name="Hit Chance", 
                       value=f"{hit_chance*100:.2f}%", 
                       inline=False)
        embed.add_field(name="Attack", value=
            f"Level: {attack_level}\n"
            f"Equipment Bonus: {equipment_bonus}\n"
            f"Attack Roll: {attack_roll:,}"
        )
        embed.add_field(name="Defence", value=
            f"Level: {defence_level}\n"
            f"Equipment Bonus: {defence_bonus}\n"
            f"Defence Roll: {defence_roll:,}"
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="potion")
    async def calculate_potion_boost(self, ctx, potion_name: str, base_level: int):
        """Calculate potion boost effect"""
        potion_name = potion_name.title()
        
        # Find potion in all categories
        potion_categories = {
            "Combat": PotionBoosts.COMBAT_POTIONS,
            "Ranged": PotionBoosts.RANGED_POTIONS,
            "Magic": PotionBoosts.MAGIC_POTIONS,
            "Restore": PotionBoosts.RESTORE_POTIONS
        }
        
        found_potion = None
        category_name = None
        
        for cat_name, category in potion_categories.items():
            if potion_name in category:
                found_potion = category[potion_name]
                category_name = cat_name
                break
        
        if not found_potion:
            potions = []
            for category in potion_categories.values():
                potions.extend(category.keys())
            await ctx.send(f"Invalid potion name. Available potions: {', '.join(potions)}")
            return
        
        embed = Embed(title=f"{potion_name} Potion Boost", color=0x00ff00)
        for stat, boost_func in found_potion.items():
            boosted = boost_func(base_level)
            if stat == "all":
                embed.add_field(name="All Combat Stats", 
                              value=f"+{boosted} levels", 
                              inline=True)
            else:
                embed.add_field(name=stat.title(), 
                              value=f"{base_level} → {base_level + boosted} ({boosted:+})", 
                              inline=True)
        
        embed.add_field(name="Category", value=category_name, inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="spec")
    async def show_special_attack(self, ctx, weapon: str):
        """Show special attack information"""
        weapon = weapon.title()
        if weapon not in SpecialAttacks.SPECIAL_ATTACKS:
            weapons = ", ".join(SpecialAttacks.SPECIAL_ATTACKS.keys())
            await ctx.send(f"Invalid weapon. Available weapons: {weapons}")
            return
        
        spec = SpecialAttacks.SPECIAL_ATTACKS[weapon]
        
        embed = Embed(title=f"{weapon} Special Attack", color=0x00ff00)
        embed.add_field(name="Energy Drain", 
                       value=f"{spec['drain']}%", 
                       inline=True)
        embed.add_field(name="Number of Hits", 
                       value=str(spec['hits']), 
                       inline=True)
        
        # Format damage multiplier
        if isinstance(spec['damage_multiplier'], list):
            damage_mult = ", ".join(f"{m:.2f}x" for m in spec['damage_multiplier'])
        else:
            damage_mult = f"{spec['damage_multiplier']:.2f}x"
        
        embed.add_field(name="Damage Multiplier", 
                       value=damage_mult, 
                       inline=True)
        embed.add_field(name="Accuracy Multiplier", 
                       value=f"{spec['accuracy_multiplier']:.2f}x", 
                       inline=True)
        
        if spec['effect']:
            embed.add_field(name="Special Effect", 
                          value=spec['effect'].replace('_', ' ').title(), 
                          inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="runenergy")
    async def calculate_run_energy(self, ctx, weight: float, agility_level: int):
        """Calculate run energy drain and restore rates"""
        drain_rate = calculate_run_energy_drain(weight, agility_level)
        restore_rate = calculate_run_energy_restore(agility_level)
        
        # Calculate some useful metrics
        ticks_to_empty = math.floor(100 / drain_rate)
        seconds_to_empty = ticks_to_empty * 0.6  # 1 tick = 0.6 seconds
        ticks_to_full = math.floor(100 / restore_rate)
        seconds_to_full = ticks_to_full * 0.6
        
        embed = Embed(title="Run Energy Calculator", color=0x00ff00)
        embed.add_field(name="Drain per Tick", 
                       value=f"{drain_rate:.3f}%", 
                       inline=True)
        embed.add_field(name="Restore per Tick", 
                       value=f"{restore_rate:.3f}%", 
                       inline=True)
        embed.add_field(name="Time to Empty", 
                       value=f"{seconds_to_empty:.1f}s", 
                       inline=True)
        embed.add_field(name="Time to Full", 
                       value=f"{seconds_to_full:.1f}s", 
                       inline=True)
        
        # Add details about weight and agility effects
        weight_effect = max(0, weight - 64) * 0.35
        agility_effect = min(50, agility_level * 0.65)
        
        embed.add_field(name="Weight Penalty", 
                       value=f"+{weight_effect:.1f}%", 
                       inline=True)
        embed.add_field(name="Agility Bonus", 
                       value=f"-{agility_effect:.1f}%", 
                       inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="xprate")
    async def calculate_xp_rate(self, ctx, course_name: str):
        """Calculate XP rates for agility course"""
        course_name = course_name.title()
        if course_name not in AGILITY_COURSES:
            courses = ", ".join(AGILITY_COURSES.keys())
            await ctx.send(f"Invalid course name. Available courses: {courses}")
            return
        
        course = AGILITY_COURSES[course_name]
        lap_xp = course.calculate_lap_xp()
        
        # Calculate XP rates at different efficiencies
        perfect_laps_hour = 3600 / (len(course.obstacles) * 2.5)  # 2.5 ticks per obstacle
        good_laps_hour = perfect_laps_hour * 0.9
        average_laps_hour = perfect_laps_hour * 0.75
        
        perfect_xp = lap_xp * perfect_laps_hour
        good_xp = lap_xp * good_laps_hour
        average_xp = lap_xp * average_laps_hour
        
        # Calculate marks of grace per hour
        marks_perfect = perfect_laps_hour * course.mark_of_grace_chance
        marks_good = good_laps_hour * course.mark_of_grace_chance
        marks_average = average_laps_hour * course.mark_of_grace_chance
        
        embed = Embed(title=f"{course.name} XP Rates", color=0x00ff00)
        embed.add_field(name="XP per Lap", 
                       value=f"{lap_xp:,.1f}", 
                       inline=False)
        
        embed.add_field(name="Perfect Rate", 
                       value=f"{perfect_xp:,.0f} xp/hr\n{marks_perfect:.1f} marks/hr", 
                       inline=True)
        embed.add_field(name="Good Rate", 
                       value=f"{good_xp:,.0f} xp/hr\n{marks_good:.1f} marks/hr", 
                       inline=True)
        embed.add_field(name="Average Rate", 
                       value=f"{average_xp:,.0f} xp/hr\n{marks_average:.1f} marks/hr", 
                       inline=True)
        
        # Add time to next level if user is training agility
        if ctx.author.id in self.training_stats:
            current_xp = self.training_stats[ctx.author.id].get("agility", 0)
            current_level = ExperienceTable.xp_to_level(current_xp)
            next_level_xp = ExperienceTable.level_to_xp(current_level + 1)
            xp_needed = next_level_xp - current_xp
            
            hours_perfect = xp_needed / perfect_xp
            hours_good = xp_needed / good_xp
            hours_average = xp_needed / average_xp
            
            embed.add_field(name=f"Time to Level {current_level + 1}", 
                          value=f"Perfect: {hours_perfect:.1f}h\n"
                                f"Good: {hours_good:.1f}h\n"
                                f"Average: {hours_average:.1f}h", 
                          inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="equipment")
    async def show_equipment_stats(self, ctx, item_name: str):
        """Show equipment stats for an item"""
        item_name = item_name.title()
        
        # Check weapons first
        if item_name in EquipmentStats.WEAPONS:
            item = EquipmentStats.WEAPONS[item_name]
            embed = Embed(title=f"{item_name} Stats", color=0x00ff00)
            
            # Attack bonuses
            attack_bonuses = "\n".join(
                f"{style.title()}: {bonus:+d}" 
                for style, bonus in item["attack_bonus"].items()
            )
            embed.add_field(name="Attack Bonuses", value=attack_bonuses, inline=True)
            
            # Defence bonuses
            defence_bonuses = "\n".join(
                f"{style.title()}: {bonus:+d}" 
                for style, bonus in item["defence_bonus"].items()
            )
            embed.add_field(name="Defence Bonuses", value=defence_bonuses, inline=True)
            
            # Other stats
            other_stats = (
                f"Strength: {item['strength_bonus']:+d}\n"
                f"Prayer: {item['prayer_bonus']:+d}\n"
                f"Speed: {item['speed']} ticks\n"
                f"Style: {item['weapon_type'].title()}"
            )
            embed.add_field(name="Other Stats", value=other_stats, inline=True)
            
            # Requirements
            reqs = "\n".join(
                f"{skill.title()}: {level}" 
                for skill, level in item["requirements"].items()
            )
            embed.add_field(name="Requirements", value=reqs, inline=True)
            
        # Then check armor
        elif item_name in EquipmentStats.ARMOR:
            item = EquipmentStats.ARMOR[item_name]
            embed = Embed(title=f"{item_name} Stats", color=0x00ff00)
            
            # Attack bonuses
            attack_bonuses = "\n".join(
                f"{style.title()}: {bonus:+d}" 
                for style, bonus in item["attack_bonus"].items()
            )
            embed.add_field(name="Attack Bonuses", value=attack_bonuses, inline=True)
            
            # Defence bonuses
            defence_bonuses = "\n".join(
                f"{style.title()}: {bonus:+d}" 
                for style, bonus in item["defence_bonus"].items()
            )
            embed.add_field(name="Defence Bonuses", value=defence_bonuses, inline=True)
            
            # Other stats
            other_stats = (
                f"Strength: {item['strength_bonus']:+d}\n"
                f"Prayer: {item['prayer_bonus']:+d}\n"
                f"Slot: {item['slot'].title()}"
            )
            embed.add_field(name="Other Stats", value=other_stats, inline=True)
            
            # Requirements
            reqs = "\n".join(
                f"{skill.title()}: {level}" 
                for skill, level in item["requirements"].items()
            )
            embed.add_field(name="Requirements", value=reqs, inline=True)
            
        else:
            all_items = list(EquipmentStats.WEAPONS.keys()) + list(EquipmentStats.ARMOR.keys())
            await ctx.send(f"Item not found. Available items: {', '.join(all_items)}")
            return
            
        await ctx.send(embed=embed)
    
    @commands.command(name="nmz")
    async def show_nmz_info(self, ctx, boss_name: str = None, mode: str = "normal"):
        """Show NMZ boss information and points"""
        if boss_name:
            boss_name = boss_name.title()
            if boss_name not in NightmareZone.BOSSES:
                bosses = ", ".join(NightmareZone.BOSSES.keys())
                await ctx.send(f"Boss not found. Available bosses: {bosses}")
                return
                
            boss = NightmareZone.BOSSES[boss_name]
            points = NightmareZone.calculate_points(boss_name, mode)
            
            embed = Embed(title=f"NMZ Boss: {boss_name}", color=0x00ff00)
            embed.add_field(name="Combat Level", value=str(boss["combat_level"]), inline=True)
            embed.add_field(name="Hitpoints", value=str(boss["hitpoints"]), inline=True)
            embed.add_field(name="Points", value=f"{points:,} ({mode} mode)", inline=True)
            embed.add_field(name="Quest", value=boss["quest"], inline=True)
            
        else:
            embed = Embed(title="NMZ Power-ups", color=0x00ff00)
            for name, powerup in NightmareZone.POWERUPS.items():
                value = f"Duration: {powerup['duration']}s\nEffect: {powerup['effect']}"
                embed.add_field(name=name, value=value, inline=True)
                
        await ctx.send(embed=embed)
    
    @commands.command(name="slayer")
    async def show_slayer_info(self, ctx, master: str = None, task: str = None):
        """Show Slayer master task information"""
        if not master:
            # Show list of masters
            masters = []
            for name, info in SlayerSystem.MASTERS.items():
                masters.append(f"{name} (level {info['level_required']}+)")
            await ctx.send(f"Available Slayer masters: {', '.join(masters)}")
            return
            
        master = master.title()
        if master not in SlayerSystem.MASTERS:
            masters = ", ".join(SlayerSystem.MASTERS.keys())
            await ctx.send(f"Master not found. Available masters: {masters}")
            return
            
        master_info = SlayerSystem.MASTERS[master]
        
        if task:
            # Show specific task info
            task = task.title()
            if task not in master_info["tasks"]:
                tasks = ", ".join(master_info["tasks"].keys())
                await ctx.send(f"Task not found. Available tasks from {master}: {tasks}")
                return
                
            task_info = master_info["tasks"][task]
            weight = SlayerSystem.calculate_task_weight(master, task)
            
            embed = Embed(title=f"Slayer Task: {task}", color=0x00ff00)
            embed.add_field(name="Master", value=master, inline=True)
            embed.add_field(name="Amount", 
                          value=f"{task_info['min']}-{task_info['max']}", 
                          inline=True)
            embed.add_field(name="Weight", 
                          value=f"{task_info['weight']} ({weight*100:.1f}%)", 
                          inline=True)
            
            # Add superior info if applicable
            if task in SuperiorSlayer.SUPERIOR_MONSTERS:
                superior = SuperiorSlayer.SUPERIOR_MONSTERS[task]
                superior_info = (
                    f"Superior: {superior['superior']}\n"
                    f"Chance: 1/{1/superior['chance']:.0f}\n"
                    f"Combat Level: {superior['combat_level']}\n"
                    f"HP: {superior['base_hp']}\n"
                    f"Max Hit: {superior['max_hit']}\n"
                    f"XP Multiplier: {superior['xp_multiplier']}x"
                )
                embed.add_field(name="Superior Version", 
                              value=superior_info, 
                              inline=False)
                
        else:
            # Show master's task list
            embed = Embed(title=f"Slayer Master: {master}", color=0x00ff00)
            embed.add_field(name="Level Required", 
                          value=str(master_info["level_required"]), 
                          inline=False)
            
            # Group tasks by weight
            tasks_by_weight = {}
            for task_name, task_info in master_info["tasks"].items():
                weight = task_info["weight"]
                if weight not in tasks_by_weight:
                    tasks_by_weight[weight] = []
                tasks_by_weight[weight].append(task_name)
            
            # Add tasks grouped by weight
            for weight in sorted(tasks_by_weight.keys(), reverse=True):
                tasks = tasks_by_weight[weight]
                embed.add_field(name=f"Weight {weight}", 
                              value="\n".join(tasks), 
                              inline=True)
                
        await ctx.send(embed=embed)
    
    @commands.command(name="barrows")
    async def show_barrows_info(self, ctx, brother: str = None):
        """Show Barrows brother information and drop rates"""
        if brother:
            brother = brother.title()
            if brother not in BarrowsSystem.BROTHERS:
                brothers = ", ".join(BarrowsSystem.BROTHERS.keys())
                await ctx.send(f"Brother not found. Available brothers: {brothers}")
                return
                
            info = BarrowsSystem.BROTHERS[brother]
            embed = Embed(title=f"Barrows Brother: {brother}", color=0x00ff00)
            
            # Combat info
            combat_info = (
                f"Combat Level: {info['combat_level']}\n"
                f"Hitpoints: {info['hitpoints']}\n"
                f"Max Hit: {info['max_hit']}\n"
                f"Attack Style: {info['attack_style'].title()}\n"
                f"Weakness: {info['weakness'].title()}"
            )
            embed.add_field(name="Combat Info", value=combat_info, inline=False)
            
            # Special effect
            embed.add_field(name="Special Effect", value=info['special'], inline=False)
            
            # Equipment drops
            drops = []
            for item, data in BarrowsSystem.REWARDS.items():
                if data['set'] == brother:
                    drops.append(f"{item}: 1/{1/data['rarity']:.0f}")
            
            if drops:
                embed.add_field(name="Equipment Drops", 
                              value="\n".join(drops), 
                              inline=False)
                
        else:
            # Show reward potential info
            embed = Embed(title="Barrows Reward Mechanics", color=0x00ff00)
            
            # Reward potential explanation
            potential_info = (
                "Reward potential is calculated from:\n"
                "- Brothers killed: 2.5% each (max 15%)\n"
                "- Monsters killed: 0.1% each (max 1%)\n"
                "Maximum potential: 100%"
            )
            embed.add_field(name="Reward Potential", 
                          value=potential_info, 
                          inline=False)
            
            # Example calculations
            examples = (
                "6 brothers + 8 monsters = 15% + 0.8% = 15.8%\n"
                "5 brothers + 12 monsters = 12.5% + 1% = 13.5%\n"
                "6 brothers + 0 monsters = 15% + 0% = 15%"
            )
            embed.add_field(name="Examples", value=examples, inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="gwd")
    async def show_gwd_info(self, ctx, boss: str = None, kc: int = None):
        """Show GWD boss information and drop rates"""
        if boss:
            boss = boss.title()
            if boss not in GodwarsDungeon.BOSSES:
                bosses = ", ".join(GodwarsDungeon.BOSSES.keys())
                await ctx.send(f"Boss not found. Available bosses: {bosses}")
                return
                
            info = GodwarsDungeon.BOSSES[boss]
            embed = Embed(title=f"GWD Boss: {boss}", color=0x00ff00)
            
            # Combat info
            combat_info = (
                f"Combat Level: {info['combat_level']}\n"
                f"Hitpoints: {info['hitpoints']}\n"
                f"Max Hit: {info['max_hit']}\n"
                f"Attack Styles: {', '.join(s.title() for s in info['attack_styles'])}\n"
                f"Weakness: {info['weakness'].title()}"
            )
            embed.add_field(name="Combat Info", value=combat_info, inline=False)
            
            # Minions
            embed.add_field(name="Minions", 
                          value="\n".join(info['minions']), 
                          inline=True)
            
            # Requirements
            reqs = (
                f"Killcount: {info['killcount']}\n"
                f"Respawn Time: {info['respawn_time']}s"
            )
            embed.add_field(name="Requirements", value=reqs, inline=True)
            
            # Unique drops
            drops = []
            for item, rate in GodwarsDungeon.UNIQUE_DROPS[boss].items():
                if kc:
                    chance = GodwarsDungeon.calculate_killcount_chance(kc, rate)
                    drops.append(f"{item}: 1/{1/rate:.0f} ({chance*100:.1f}% by {kc} KC)")
                else:
                    drops.append(f"{item}: 1/{1/rate:.0f}")
            
            embed.add_field(name="Unique Drops", 
                          value="\n".join(drops), 
                          inline=False)
                
        else:
            # Show general GWD info
            embed = Embed(title="God Wars Dungeon Info", color=0x00ff00)
            
            # List all bosses with basic info
            for boss_name, boss_info in GodwarsDungeon.BOSSES.items():
                value = (
                    f"Combat Level: {boss_info['combat_level']}\n"
                    f"Killcount: {boss_info['killcount']}\n"
                    f"Weakness: {boss_info['weakness'].title()}"
                )
                embed.add_field(name=boss_name, value=value, inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="zulrah")
    async def show_zulrah_info(self, ctx, phase: str = None, dps: float = None):
        """Show Zulrah phase information and profit calculations"""
        if phase:
            phase = phase.title()
            if phase not in Zulrah.PHASES:
                phases = ", ".join(Zulrah.PHASES.keys())
                await ctx.send(f"Phase not found. Available phases: {phases}")
                return
                
            info = Zulrah.PHASES[phase]
            embed = Embed(title=f"Zulrah {phase} Phase", color=0x00ff00)
            
            # Combat info
            combat_info = (
                f"Combat Level: {info['combat_level']}\n"
                f"Hitpoints: {info['hitpoints']}\n"
                f"Max Hit: {info['max_hit']}\n"
                f"Attack Style: {info['attack_style'].title() if 'attack_style' in info else ', '.join(s.title() for s in info['attack_styles'])}\n"
                f"Weakness: {info['weakness'].title()}"
            )
            embed.add_field(name="Combat Info", value=combat_info, inline=False)
            
            # Protection and special
            if info['protection']:
                embed.add_field(name="Protection Prayer", 
                              value=info['protection'].title(), 
                              inline=True)
            embed.add_field(name="Special", value=info['special'], inline=True)
            
            # Show rotation info
            for rot_name, rotation in Zulrah.ROTATIONS.items():
                phase_positions = [i+1 for i, (p, _, _) in enumerate(rotation) if p == phase]
                if phase_positions:
                    positions = ", ".join(str(pos) for pos in phase_positions)
                    embed.add_field(name=f"{rot_name} Positions", 
                                  value=positions, 
                                  inline=True)
                
        else:
            # Show general Zulrah info
            embed = Embed(title="Zulrah Information", color=0x00ff00)
            
            # Unique drops
            drops = []
            for item, rate in Zulrah.UNIQUE_DROPS.items():
                drops.append(f"{item}: 1/{1/rate:.0f}")
            embed.add_field(name="Unique Drops", 
                          value="\n".join(drops), 
                          inline=False)
            
            # Profit calculation if DPS provided
            if dps:
                kill_time = Zulrah.calculate_kill_time(dps)
                profit = Zulrah.calculate_profit_per_hour(kill_time)
                
                profit_info = (
                    f"Kill Time: {kill_time:.1f}s\n"
                    f"Kills/hr: {3600/kill_time:.1f}\n"
                    f"Profit/hr: {profit:,} gp"
                )
                embed.add_field(name="Profit Calculator", 
                              value=profit_info, 
                              inline=False)
            
            # Add example rotation
            rot_info = []
            for i, (phase, pos, prayer) in enumerate(Zulrah.ROTATIONS["Rotation 1"]):
                prayer_text = f" ({prayer.title()})" if prayer else ""
                rot_info.append(f"{i+1}. {phase} - {pos}{prayer_text}")
            
            embed.add_field(name="Example Rotation", 
                          value="\n".join(rot_info), 
                          inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="vorkath")
    async def show_vorkath_info(self, ctx, dps: float = None, woox_walk: bool = False):
        """Show Vorkath information and profit calculations"""
        embed = Embed(title="Vorkath Information", color=0x00ff00)
        
        # Basic stats
        stats = Vorkath.STATS
        stats_info = (
            f"Combat Level: {stats['combat_level']}\n"
            f"Hitpoints: {stats['hitpoints']}\n"
            f"Max Hit: {stats['max_hit']}\n"
            f"Attack Styles: {', '.join(s.title() for s in stats['base_attack_styles'])}\n"
            f"Weakness: {', '.join(w.title() for w in stats['weakness'])}"
        )
        embed.add_field(name="Stats", value=stats_info, inline=False)
        
        # Special attacks
        for name, spec in Vorkath.SPECIAL_ATTACKS.items():
            spec_info = []
            for key, value in spec.items():
                if key == "frequency":
                    spec_info.append(f"Every {value} attacks" if value != "random" else "Random")
                elif key == "duration":
                    spec_info.append(f"Duration: {value} ticks")
                elif key == "damage":
                    spec_info.append(f"Damage: {value}")
                elif key == "max_hit":
                    spec_info.append(f"Max Hit: {value}")
                elif key == "spawn_hp":
                    spec_info.append(f"Spawn HP: {value}")
            embed.add_field(name=name, 
                          value="\n".join(spec_info), 
                          inline=True)
        
        # Unique drops
        drops = []
        for item, rate in Vorkath.UNIQUE_DROPS.items():
            if rate != 1:  # Skip guaranteed drops
                drops.append(f"{item}: 1/{1/rate:.0f}")
        embed.add_field(name="Unique Drops", 
                      value="\n".join(drops), 
                      inline=False)
        
        # Profit calculation if DPS provided
        if dps:
            kill_time = Vorkath.calculate_kill_time(dps, woox_walk)
            profit = Vorkath.calculate_profit_per_hour(kill_time)
            
            profit_info = (
                f"Kill Time: {kill_time:.1f}s\n"
                f"Kills/hr: {3600/kill_time:.1f}\n"
                f"Profit/hr: {profit:,} gp\n"
                f"Woox Walking: {'Yes' if woox_walk else 'No'}"
            )
            embed.add_field(name="Profit Calculator", 
                          value=profit_info, 
                          inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="cox")
    async def show_cox_info(self, ctx, boss: str = None, team_size: int = None, 
                           points: int = None, personal_points: int = None,
                           challenge_mode: bool = False):
        """Show Chambers of Xeric information"""
        if boss:
            boss = boss.title()
            if boss not in ChambersOfXeric.BOSSES:
                bosses = ", ".join(ChambersOfXeric.BOSSES.keys())
                await ctx.send(f"Boss not found. Available bosses: {bosses}")
                return
                
            info = ChambersOfXeric.BOSSES[boss]
            embed = Embed(title=f"CoX Boss: {boss}", color=0x00ff00)
            
            # Combat info
            if boss == "Great Olm":
                combat_info = (
                    f"Combat Level: {info['combat_level']}\n"
                    f"Head HP: {info['hitpoints']['head']}\n"
                    f"Left Hand HP: {info['hitpoints']['left_hand']}\n"
                    f"Right Hand HP: {info['hitpoints']['right_hand']}\n"
                    f"Max Auto Hit: {info['max_hit']['auto']}\n"
                    f"Max Crystal Hit: {info['max_hit']['crystal']}\n"
                    f"Max Lightning Hit: {info['max_hit']['lightning']}"
                )
                embed.add_field(name="Combat Info", value=combat_info, inline=False)
                
                # Phases
                embed.add_field(name="Phases", 
                              value="\n".join(info['phases']), 
                              inline=True)
                
                # Special attacks
                specials = "\n".join(f"{name}: {desc}" 
                                   for name, desc in info['special_attacks'].items())
                embed.add_field(name="Special Attacks", 
                              value=specials, 
                              inline=False)
            else:
                combat_info = (
                    f"Combat Level: {info['combat_level']}\n"
                    f"Hitpoints: {info['hitpoints']}\n"
                    f"Max Hit: {info['max_hit']}\n"
                    f"Attack Style: {info['attack_style'].title()}\n"
                    f"Weakness: {info['weakness'].title()}"
                )
                embed.add_field(name="Combat Info", value=combat_info, inline=False)
                
                if 'special' in info:
                    embed.add_field(name="Special Mechanic", 
                                  value=info['special'], 
                                  inline=True)
                
        else:
            # Show general CoX info
            embed = Embed(title="Chambers of Xeric Information", color=0x00ff00)
            
            # Unique drops
            drops = []
            for item, rate in ChambersOfXeric.UNIQUE_DROPS.items():
                drops.append(f"{item}: 1/{1/rate:.0f}")
            embed.add_field(name="Unique Drops", 
                          value="\n".join(drops), 
                          inline=False)
            
            # Points system
            points_info = (
                f"Death Reduction: {ChambersOfXeric.POINTS_SYSTEM['Death reduction']}%\n"
                f"Personal Cap: {ChambersOfXeric.POINTS_SYSTEM['Personal point cap']:,}\n"
                f"Team Cap: {ChambersOfXeric.POINTS_SYSTEM['Team point cap']:,}\n"
                f"CM Modifier: {ChambersOfXeric.POINTS_SYSTEM['Point modifiers']['Challenge mode']}x"
            )
            embed.add_field(name="Points System", 
                          value=points_info, 
                          inline=False)
            
            # Team size scaling
            scaling = []
            for size, modifier in ChambersOfXeric.POINTS_SYSTEM["Point modifiers"]["Team size"].items():
                if isinstance(size, int):
                    scaling.append(f"{size} player: {modifier:.1f}x")
            embed.add_field(name="Team Scaling", 
                          value="\n".join(scaling), 
                          inline=True)
            
            # Drop chance calculation if points provided
            if points and personal_points and team_size:
                chance = ChambersOfXeric.calculate_drop_chance(
                    points, personal_points, team_size
                )
                points_info = (
                    f"Team Points: {points:,}\n"
                    f"Personal Points: {personal_points:,}\n"
                    f"Team Size: {team_size}\n"
                    f"Drop Chance: {chance*100:.2f}%"
                )
                embed.add_field(name="Drop Chance", 
                              value=points_info, 
                              inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="tob")
    async def show_tob_info(self, ctx, boss: str = None, team_size: int = None,
                           deaths: int = None, completion_time: int = None):
        """Show Theatre of Blood information"""
        if boss:
            boss = boss.title()
            if boss not in TheatreOfBlood.BOSSES:
                bosses = ", ".join(TheatreOfBlood.BOSSES.keys())
                await ctx.send(f"Boss not found. Available bosses: {bosses}")
                return
                
            info = TheatreOfBlood.BOSSES[boss]
            embed = Embed(title=f"ToB Boss: {boss}", color=0x00ff00)
            
            # Combat info
            if boss == "Verzik Vitur":
                combat_info = (
                    f"Combat Level: {info['combat_level']}\n"
                    f"P1 HP: {info['phase_hp']['P1']}\n"
                    f"P2 HP: {info['phase_hp']['P2']}\n"
                    f"P3 HP: {info['phase_hp']['P3']}\n"
                    f"P1 Max Hit: {info['max_hit']['P1']}\n"
                    f"P2 Max Hit: {info['max_hit']['P2']}\n"
                    f"P3 Max Hit: {info['max_hit']['P3']}"
                )
                embed.add_field(name="Combat Info", value=combat_info, inline=False)
                
                # Special attacks
                specials = "\n".join(f"{name}: {desc}" 
                                   for name, desc in info['special_attacks'].items())
                embed.add_field(name="Special Attacks", 
                              value=specials, 
                              inline=False)
            else:
                combat_info = [f"Combat Level: {info['combat_level']}"]
                
                if 'hitpoints' in info:
                    combat_info.append(f"Hitpoints: {info['hitpoints']}")
                if 'max_hit' in info:
                    combat_info.append(f"Max Hit: {info['max_hit']}")
                if 'attack_styles' in info:
                    combat_info.append(f"Attack Styles: {', '.join(s.title() for s in info['attack_styles'])}")
                
                embed.add_field(name="Combat Info", 
                              value="\n".join(combat_info), 
                              inline=False)
                
                # Special mechanics for each boss
                if boss == "The Maiden of Sugadinti":
                    phases = f"Phase changes at: {', '.join(str(p)+'%' for p in info['phases'])}"
                    embed.add_field(name="Phases", value=phases, inline=True)
                    
                    specials = "\n".join(f"{name}: {desc}" 
                                       for name, desc in info['special_attacks'].items())
                    embed.add_field(name="Special Attacks", 
                                  value=specials, 
                                  inline=False)
                    
                elif boss == "Pestilent Bloat":
                    mechanics = "\n".join(f"{k}: {v} ticks" if 'duration' in k.lower() 
                                        else f"{k}: {v}" 
                                        for k, v in info['mechanics'].items())
                    embed.add_field(name="Mechanics", value=mechanics, inline=False)
                    
                elif boss == "Nylocas Vasilias":
                    phases = []
                    for style, data in info['phases'].items():
                        phases.append(f"{style}: {data['color'].title()} (weak to {data['weakness']})")
                    embed.add_field(name="Phases", 
                                  value="\n".join(phases), 
                                  inline=False)
                    
                elif boss == "Sotetseg":
                    specials = "\n".join(f"{name}: {desc}" 
                                       for name, desc in info['special_attacks'].items())
                    embed.add_field(name="Special Attacks", 
                                  value=specials, 
                                  inline=False)
                    
                elif boss == "Xarpus":
                    phases = "\n".join(f"Phase {phase}: {desc}" 
                                     for phase, desc in info['phases'].items())
                    embed.add_field(name="Phases", value=phases, inline=False)
                
        else:
            # Show general ToB info
            embed = Embed(title="Theatre of Blood Information", color=0x00ff00)
            
            # Unique drops
            drops = []
            for item, rate in TheatreOfBlood.UNIQUE_DROPS.items():
                drops.append(f"{item}: 1/{1/rate:.0f}")
            embed.add_field(name="Unique Drops", 
                          value="\n".join(drops), 
                          inline=False)
            
            # Death mechanics
            death_info = []
            for deaths, modifier in TheatreOfBlood.WIPE_MECHANICS["Death penalties"].items():
                penalty = (1 - modifier) * 100
                if deaths < TheatreOfBlood.WIPE_MECHANICS["Death cap"]:
                    death_info.append(f"{deaths} death: {penalty:.0f}% penalty")
                else:
                    death_info.append(f"{deaths}+ deaths: Raid failed")
            
            embed.add_field(name="Death Mechanics", 
                          value="\n".join(death_info), 
                          inline=True)
            
            # Drop chance calculation if parameters provided
            if team_size and deaths is not None and completion_time:
                chance = TheatreOfBlood.calculate_drop_chance(
                    team_size, deaths, completion_time
                )
                raid_info = (
                    f"Team Size: {team_size}\n"
                    f"Deaths: {deaths}\n"
                    f"Completion Time: {completion_time}s\n"
                    f"Drop Chance: {chance*100:.2f}%"
                )
                embed.add_field(name="Drop Chance", 
                              value=raid_info, 
                              inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="wild")
    async def show_wilderness_info(self, ctx, combat_level: int = None, 
                                 wilderness_level: int = None,
                                 skull_type: str = None):
        """Show Wilderness level ranges and PvP information"""
        embed = Embed(title="Wilderness Information", color=0x00ff00)
        
        if combat_level and wilderness_level:
            # Calculate combat range
            min_level, max_level = WildernessSystem.calculate_combat_range(
                combat_level, wilderness_level
            )
            
            combat_info = (
                f"Your Combat Level: {combat_level}\n"
                f"Wilderness Level: {wilderness_level}\n"
                f"Can be attacked by: {min_level}-{max_level}"
            )
            embed.add_field(name="Combat Range", value=combat_info, inline=False)
            
            # Add skull info if provided
            if skull_type:
                skull_type = skull_type.lower()
                if skull_type in WildernessSystem.SKULL_MECHANICS:
                    skull_info = WildernessSystem.SKULL_MECHANICS[skull_type]
                    items_kept = WildernessSystem.calculate_items_kept(
                        skull_type, protect_item=False
                    )
                    items_protected = WildernessSystem.calculate_items_kept(
                        skull_type, protect_item=True
                    )
                    
                    skull_details = (
                        f"Duration: {skull_info['duration']/100:.1f} minutes\n"
                        f"Items Kept: {items_kept}\n"
                        f"With Protect Item: {items_protected}\n"
                    )
                    if "prayer_drain" in skull_info:
                        skull_details += f"Prayer Drain: {skull_info['prayer_drain']*100:.0f}% of damage"
                        
                    embed.add_field(name=f"{skull_type.title()} Skull", 
                                  value=skull_details, 
                                  inline=False)
        else:
            # Show wilderness level ranges
            ranges = []
            for location, (min_level, max_level) in WildernessSystem.LEVEL_RANGES.items():
                ranges.append(f"{location.replace('_', ' ').title()}: {min_level}-{max_level}")
            
            embed.add_field(name="Wilderness Levels", 
                          value="\n".join(ranges), 
                          inline=False)
            
            # Show skull types
            skulls = []
            for skull_type, info in WildernessSystem.SKULL_MECHANICS.items():
                skulls.append(
                    f"{skull_type.title()}: {info['duration']/100:.1f}m, "
                    f"keeps {info['items_kept']} items"
                )
            
            embed.add_field(name="Skull Types", 
                          value="\n".join(skulls), 
                          inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="construction")
    async def show_construction_info(self, ctx, room_type: str = None, 
                                   portal_dest: str = None):
        """Show Construction room information and requirements"""
        if room_type:
            room_type = room_type.lower()
            if room_type not in ConstructionSystem.ROOM_TYPES:
                rooms = ", ".join(ConstructionSystem.ROOM_TYPES.keys())
                await ctx.send(f"Room not found. Available rooms: {rooms}")
                return
                
            room = ConstructionSystem.ROOM_TYPES[room_type]
            embed = Embed(title=f"Construction Room: {room_type.title()}", 
                        color=0x00ff00)
            
            # Room info
            room_info = (
                f"Level Required: {room['level']}\n"
                f"Cost: {room['cost']:,} gp\n"
                f"Door Hotspots: {room['doors']}"
            )
            embed.add_field(name="Requirements", value=room_info, inline=False)
            
            # Hotspots
            hotspots = "\n".join(spot.replace("_", " ").title() 
                               for spot in room["hotspots"])
            embed.add_field(name="Hotspots", value=hotspots, inline=True)
            
            # Portal info if applicable
            if room_type == "portal_chamber" and portal_dest:
                portal_dest = portal_dest.lower()
                if portal_dest in ConstructionSystem.PORTAL_DESTINATIONS:
                    portal = ConstructionSystem.PORTAL_DESTINATIONS[portal_dest]
                    runes = [f"{amount} {rune}" 
                            for rune, amount in portal["runes"].items()]
                    
                    portal_info = (
                        f"Magic Level: {portal['level']}\n"
                        f"Runes: {', '.join(runes)}"
                    )
                    embed.add_field(name=f"{portal_dest.title()} Portal", 
                                  value=portal_info, 
                                  inline=False)
                    
        else:
            # Show room categories
            embed = Embed(title="Construction Information", color=0x00ff00)
            
            # Group rooms by level
            rooms_by_level = {}
            for name, room in ConstructionSystem.ROOM_TYPES.items():
                level = room["level"]
                if level not in rooms_by_level:
                    rooms_by_level[level] = []
                rooms_by_level[level].append(
                    f"{name.replace('_', ' ').title()}: {room['cost']:,} gp"
                )
            
            # Add rooms grouped by level
            for level in sorted(rooms_by_level.keys()):
                embed.add_field(name=f"Level {level}", 
                              value="\n".join(rooms_by_level[level]), 
                              inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="farming")
    async def show_farming_info(self, ctx, patch_type: str = None, 
                              crop_type: str = None, stages: int = None):
        """Show Farming patch information and growth times"""
        if patch_type:
            patch_type = patch_type.lower()
            if patch_type not in FarmingSystem.PATCH_TYPES:
                patches = ", ".join(FarmingSystem.PATCH_TYPES.keys())
                await ctx.send(f"Patch type not found. Available types: {patches}")
                return
                
            patch = FarmingSystem.PATCH_TYPES[patch_type]
            embed = Embed(title=f"Farming: {patch_type.title()} Patches", 
                        color=0x00ff00)
            
            # Patch locations
            locations = "\n".join(loc.replace("_", " ").title() 
                                for loc in patch["locations"])
            embed.add_field(name="Locations", value=locations, inline=True)
            
            # Tools and protection
            tools = ", ".join(tool.replace("_", " ").title() 
                            for tool in patch["tools"])
            protection = patch["protection"].replace("_", " ").title() if patch["protection"] else "None"
            
            embed.add_field(name="Requirements", 
                          value=f"Tools: {tools}\nProtection: {protection}", 
                          inline=True)
            
            # Growth info if crop specified
            if crop_type and crop_type.lower() in FarmingSystem.GROWTH_STAGES:
                crop_type = crop_type.lower()
                growth = FarmingSystem.GROWTH_STAGES[crop_type]
                
                # Calculate growth time
                total_time = FarmingSystem.calculate_growth_time(crop_type, stages or 0)
                time_per_stage = growth["minutes_per_stage"]
                
                growth_info = (
                    f"Stage Count: {growth['stage_count']}\n"
                    f"Time per Stage: {time_per_stage}m\n"
                    f"Total Time: {total_time}m"
                )
                
                if "minimum_yield" in growth:
                    min_yield, max_yield = FarmingSystem.calculate_yield(
                        crop_type, "ultracompost", True
                    )
                    growth_info += f"\nYield: {min_yield}-{max_yield}"
                    
                if "produce_count" in growth:
                    growth_info += f"\nProduce: {growth['produce_count']} per harvest"
                    
                if "regrowth_time" in growth:
                    growth_info += f"\nRegrowth: {growth['regrowth_time']/60:.1f}h"
                    
                embed.add_field(name="Growth Info", 
                              value=growth_info, 
                              inline=False)
                
                # Disease chances
                disease_info = []
                for compost, chance in FarmingSystem.DISEASE_CHANCES.items():
                    actual_chance = FarmingSystem.calculate_disease_chance(
                        patch_type, compost, protection=bool(patch["protection"])
                    )
                    disease_info.append(
                        f"{compost.title()}: {actual_chance*100:.1f}%"
                    )
                    
                embed.add_field(name="Disease Chances", 
                              value="\n".join(disease_info), 
                              inline=True)
                
        else:
            # Show patch type overview
            embed = Embed(title="Farming Information", color=0x00ff00)
            
            for patch_name, patch_info in FarmingSystem.PATCH_TYPES.items():
                value = (
                    f"Locations: {len(patch_info['locations'])}\n"
                    f"Protection: {patch_info['protection'] or 'None'}\n"
                    f"Disease Reduction: {patch_info['compost_effect']*100:.0f}%"
                )
                embed.add_field(name=patch_name.replace("_", " ").title(), 
                              value=value, 
                              inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="inferno")
    async def show_inferno_info(self, ctx, wave: int = None):
        """Show Inferno wave information and supply calculations"""
        if wave:
            if wave not in InfernoSystem.WAVES:
                await ctx.send(f"Invalid wave number. Available waves: 1-68")
                return
                
            monsters = InfernoSystem.WAVES[wave]
            embed = Embed(title=f"Inferno Wave {wave}", color=0x00ff00)
            
            # Wave composition
            composition = []
            for monster in monsters:
                info = InfernoSystem.MONSTERS[monster]
                composition.append(
                    f"{monster}: Combat {info['combat_level']}, "
                    f"HP {info['hitpoints']}, "
                    f"Max hit {info['max_hit']}"
                )
            embed.add_field(name="Monsters", 
                          value="\n".join(composition), 
                          inline=False)
            
            # Wave difficulty
            difficulty = InfernoSystem.calculate_wave_difficulty(wave)
            embed.add_field(name="Relative Difficulty", 
                          value=f"{difficulty:.1f}", 
                          inline=True)
            
            # Supply calculation
            supplies = InfernoSystem.calculate_supply_usage(wave)
            supply_info = []
            for item, amount in supplies.items():
                supply_info.append(f"{item.replace('_', ' ').title()}: {amount}")
            
            embed.add_field(name="Expected Supplies", 
                          value="\n".join(supply_info), 
                          inline=True)
            
            # Special mechanics for Jad/Zuk waves
            if "Jad" in monsters:
                jad_info = InfernoSystem.MONSTERS["Jad"]
                healers = jad_info["healers"]
                embed.add_field(name="Jad Mechanics", 
                              value=f"Healers: {healers['count']}\n"
                                   f"Heal amount: {healers['heal_amount']}\n"
                                   f"Spawn at: {healers['trigger_hp']}%", 
                              inline=False)
            
            if "Zuk" in monsters:
                zuk_info = InfernoSystem.MONSTERS["Zuk"]
                shield = zuk_info["shield"]
                embed.add_field(name="Zuk Mechanics", 
                              value=f"Shield HP: {shield['hitpoints']}\n"
                                   f"Movement delay: {shield['movement_delay']} ticks\n"
                                   f"Safe range: {shield['safe_range']} tiles", 
                              inline=False)
                
                # Show spawn sets
                sets = []
                for i, set_info in enumerate(zuk_info["sets"], 1):
                    sets.append(
                        f"Set {i} ({set_info['hp']} HP): "
                        f"{', '.join(set_info['spawn'])}"
                    )
                embed.add_field(name="Spawn Sets", 
                              value="\n".join(sets), 
                              inline=False)
                
        else:
            # Show general Inferno info
            embed = Embed(title="Inferno Information", color=0x00ff00)
            
            # Monster overview
            for monster, info in InfernoSystem.MONSTERS.items():
                if monster in ["Jad", "Zuk"]:
                    continue  # Show these separately
                    
                value = (
                    f"Combat: {info['combat_level']}\n"
                    f"HP: {info['hitpoints']}\n"
                    f"Max hit: {info['max_hit']}\n"
                    f"Style: {info['attack_style'].title() if info['attack_style'] else 'None'}\n"
                    f"Weakness: {info['weakness'].replace('_', ' ').title()}"
                )
                embed.add_field(name=monster, value=value, inline=True)
            
            # Jad and Zuk info
            for boss in ["Jad", "Zuk"]:
                info = InfernoSystem.MONSTERS[boss]
                value = (
                    f"Combat: {info['combat_level']}\n"
                    f"HP: {info['hitpoints']}\n"
                    f"Max hit: {info['max_hit']}\n"
                    f"Style: {info['attack_style'].title() if 'attack_style' in info else ', '.join(s.title() for s in info['attack_styles'])}\n"
                    f"Weakness: {info['weakness'].replace('_', ' ').title()}"
                )
                embed.add_field(name=boss, value=value, inline=False)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="diary")
    async def show_achievement_diary(self, ctx, area: str = None, 
                                   difficulty: str = None):
        """Show Achievement Diary information and requirements"""
        if area:
            area = area.title()
            if area not in AchievementDiarySystem.AREAS:
                areas = ", ".join(AchievementDiarySystem.AREAS.keys())
                await ctx.send(f"Area not found. Available areas: {areas}")
                return
                
            if difficulty:
                difficulty = difficulty.lower()
                if difficulty not in AchievementDiarySystem.AREAS[area]:
                    difficulties = ", ".join(AchievementDiarySystem.AREAS[area].keys())
                    await ctx.send(f"Difficulty not found. Available difficulties: {difficulties}")
                    return
                    
                # Show specific diary tier
                diary = AchievementDiarySystem.AREAS[area][difficulty]
                embed = Embed(title=f"{area} {difficulty.title()} Diary", 
                            color=0x00ff00)
                
                # Requirements
                reqs = []
                for skill, level in diary["requirements"].items():
                    reqs.append(f"{skill.title()}: {level}")
                embed.add_field(name="Requirements", 
                              value="\n".join(reqs), 
                              inline=True)
                
                # Tasks
                tasks = []
                for i, task in enumerate(diary["tasks"], 1):
                    tasks.append(f"{i}. {task}")
                embed.add_field(name="Tasks", 
                              value="\n".join(tasks), 
                              inline=False)
                
                # Rewards
                for item, reward in diary["rewards"].items():
                    reward_info = []
                    if "stats" in reward:
                        for stat, bonus in reward["stats"].items():
                            reward_info.append(f"+{bonus} {stat.title()}")
                    if "effects" in reward:
                        reward_info.extend(reward["effects"])
                        
                    embed.add_field(name=item.replace("_", " ").title(), 
                                  value="\n".join(reward_info), 
                                  inline=True)
                
            else:
                # Show area overview
                embed = Embed(title=f"{area} Achievement Diary", color=0x00ff00)
                
                for diff, info in AchievementDiarySystem.AREAS[area].items():
                    # Show requirements and reward summary
                    value = []
                    value.append("Requirements:")
                    for skill, level in info["requirements"].items():
                        value.append(f"- {skill.title()}: {level}")
                    value.append("\nRewards:")
                    for item, reward in info["rewards"].items():
                        value.append(f"- {item.replace('_', ' ').title()}")
                        
                    embed.add_field(name=diff.title(), 
                                  value="\n".join(value), 
                                  inline=True)
                
        else:
            # Show all areas
            embed = Embed(title="Achievement Diaries", color=0x00ff00)
            
            for area, difficulties in AchievementDiarySystem.AREAS.items():
                value = []
                for diff in difficulties.keys():
                    value.append(f"- {diff.title()}")
                embed.add_field(name=area, value="\n".join(value), inline=True)
            
        await ctx.send(embed=embed)
    
    @commands.command(name="clue")
    async def show_clue_info(self, ctx, clue_type: str = None, 
                            step_type: str = None):
        """Show Clue Scroll information and rewards"""
        if clue_type:
            clue_type = clue_type.lower()
            if clue_type not in ClueScrollSystem.TYPES:
                types = ", ".join(ClueScrollSystem.TYPES.keys())
                await ctx.send(f"Clue type not found. Available types: {types}")
                return
                
            info = ClueScrollSystem.TYPES[clue_type]
            embed = Embed(title=f"{clue_type.title()} Clue Scroll", 
                        color=0x00ff00)
            
            # Basic info
            embed.add_field(name="Steps", 
                          value=str(info["steps"]), 
                          inline=True)
            
            # Completion chance
            chance_with_reqs = ClueScrollSystem.calculate_completion_chance(
                clue_type, True
            )
            chance_without_reqs = ClueScrollSystem.calculate_completion_chance(
                clue_type, False
            )
            completion_info = (
                f"With requirements: {chance_with_reqs*100:.1f}%\n"
                f"Without requirements: {chance_without_reqs*100:.1f}%"
            )
            embed.add_field(name="Completion Chance", 
                          value=completion_info, 
                          inline=True)
            
            # Average reward
            avg_reward = ClueScrollSystem.calculate_average_reward(clue_type)
            embed.add_field(name="Average Reward", 
                          value=f"{avg_reward:,} gp", 
                          inline=True)
            
            # Unique drops
            drops = []
            for item, rate in info["unique_drops"].items():
                drops.append(f"{item.replace('_', ' ').title()}: 1/{1/rate:.0f}")
            embed.add_field(name="Unique Drops", 
                          value="\n".join(drops), 
                          inline=False)
            
            # Step type info if specified
            if step_type:
                step_type = step_type.lower()
                if step_type not in ClueScrollSystem.STEP_TYPES:
                    steps = ", ".join(ClueScrollSystem.STEP_TYPES.keys())
                    await ctx.send(f"Step type not found. Available types: {steps}")
                    return
                    
                step_info = ClueScrollSystem.STEP_TYPES[step_type]
                value = [f"Difficulty: {step_info['difficulty']:.1f}"]
                
                if step_info["requirements"]:
                    value.append("\nRequirements:")
                    for req, needed in step_info["requirements"].items():
                        value.append(f"- {req.replace('_', ' ').title()}")
                        
                embed.add_field(name=f"{step_type.title()} Steps", 
                              value="\n".join(value), 
                              inline=False)
                
        else:
            # Show clue type overview
            embed = Embed(title="Clue Scroll Information", color=0x00ff00)
            
            for type_name, type_info in ClueScrollSystem.TYPES.items():
                value = [
                    f"Steps: {type_info['steps']}",
                    f"Avg. Value: {ClueScrollSystem.calculate_average_reward(type_name):,} gp",
                    "\nNotable drops:"
                ]
                
                # Show top 3 most valuable drops
                drops = []
                for item, rate in type_info["unique_drops"].items():
                    if "3rd_age" in item:
                        value = 1_000_000_000
                    elif "ranger" in item:
                        value = 40_000_000
                    elif "gilded" in item:
                        value = 1_000_000
                    else:
                        value = 100_000
                    drops.append((item, rate, value))
                
                drops.sort(key=lambda x: x[2], reverse=True)
                for item, rate, _ in drops[:3]:
                    value.append(f"- {item.replace('_', ' ').title()}: 1/{1/rate:.0f}")
                    
                embed.add_field(name=type_name.title(), 
                              value="\n".join(value), 
                              inline=True)
            
        await ctx.send(embed=embed)

    @commands.command(name='mining')
    async def show_mining_info(self, ctx, rock_type: str = None, 
                             level: int = None, pickaxe_type: str = None):
        """Show Mining information and calculations"""
        if rock_type:
            rock_type = rock_type.lower()
            if rock_type not in MiningSystem.ROCKS:
                rocks = ", ".join(MiningSystem.ROCKS.keys())
                await ctx.send(f"Rock type not found. Available rocks: {rocks}")
                return
                
            rock = MiningSystem.ROCKS[rock_type]
            embed = Embed(title=f"Mining: {rock_type.title()} Rock", 
                        color=0x00ff00)
            
            # Basic info
            rock_info = (
                f"Level Required: {rock['level']}\n"
                f"XP per Ore: {rock['xp']}\n"
                f"Respawn Time: {rock['respawn_time']}s\n"
                f"Ore Value: {rock['ore_value']} gp"
            )
            embed.add_field(name="Rock Info", value=rock_info, inline=False)
            
            # Best locations
            locations = MiningSystem.get_best_location(rock_type)
            embed.add_field(name="Best Locations", 
                          value="\n".join(loc.replace("_", " ").title() 
                                        for loc in locations), 
                          inline=True)
            
            # Calculations if level and pickaxe provided
            if level is not None and pickaxe_type:
                pickaxe_type = pickaxe_type.lower()
                if pickaxe_type not in MiningSystem.PICKAXES:
                    pickaxes = ", ".join(MiningSystem.PICKAXES.keys())
                    await ctx.send(f"Pickaxe type not found. Available pickaxes: {pickaxes}")
                    return
                
                xp_rate = MiningSystem.calculate_xp_rate(
                    rock_type, level, pickaxe_type
                )
                profit = MiningSystem.calculate_profit_per_hour(
                    rock_type, level, pickaxe_type
                )
                
                rates = (
                    f"XP/hr: {xp_rate:,.1f}\n"
                    f"Profit/hr: {profit:,} gp\n"
                    f"Time to next level: {((ExperienceTable.level_to_xp(level + 1) - ExperienceTable.level_to_xp(level)) / xp_rate):.1f}h"
                )
                embed.add_field(name="Rates", value=rates, inline=False)
                
                # Add gem chances
                gems = []
                for gem, chance in MiningSystem.GEM_CHANCES.items():
                    gems_per_hour = xp_rate * chance / rock["xp"]
                    gems.append(f"{gem.replace('_', ' ').title()}: {gems_per_hour:.1f}/hr")
                
                embed.add_field(name="Gem Rates", 
                              value="\n".join(gems), 
                              inline=True)
                
        else:
            # Show mining overview
            embed = Embed(title="Mining Information", color=0x00ff00)
            
            # Group rocks by level
            rocks_by_level = {}
            for name, rock in MiningSystem.ROCKS.items():
                level = rock["level"]
                if level not in rocks_by_level:
                    rocks_by_level[level] = []
                rocks_by_level[level].append(
                    f"{name.title()}: {rock['xp']} xp, {rock['ore_value']} gp"
                )
            
            # Add rocks grouped by level
            for level in sorted(rocks_by_level.keys()):
                embed.add_field(name=f"Level {level}", 
                              value="\n".join(rocks_by_level[level]), 
                              inline=True)
            
            # Add pickaxe information
            pickaxes_info = []
            for name, pickaxe in MiningSystem.PICKAXES.items():
                pickaxes_info.append(
                    f"{name.title()}: Level {pickaxe['level']}, +{pickaxe['bonus']} bonus"
                )
            embed.add_field(name="Pickaxes", 
                          value="\n".join(pickaxes_info), 
                          inline=False)
            
            # Add special mining locations
            special_locations = {
                "Motherlode Mine": "Level 30, AFK mining, Nuggets for prospector",
                "Blast Mine": "Level 40, High XP rates, Dynamite required",
                "Volcanic Mine": "Level 50, Team-based, High XP rates",
                "Mining Guild": "Level 60, Invisible +7 mining boost"
            }
            locations_info = []
            for name, desc in special_locations.items():
                locations_info.append(f"{name}: {desc}")
            embed.add_field(name="Special Locations", 
                          value="\n".join(locations_info), 
                          inline=False)
            
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(OSRSCommands(bot)) 