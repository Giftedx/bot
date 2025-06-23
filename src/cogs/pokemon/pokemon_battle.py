import discord
from discord.ext import commands
import asyncio
import random
import json
from typing import Dict, Optional, List, Tuple
import aiohttp


class PokemonBattle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battles: Dict[int, Dict] = {}  # channel_id: battle_data
        self.battle_locks: Dict[int, bool] = {}  # user_id: is_battling
        self.move_cache: Dict[str, Dict] = {}  # move_name: move_data
        self.type_cache: Dict[str, Dict] = {}  # type_name: type_data

        # Type effectiveness chart (will be populated from PokeAPI)
        self.type_chart: Dict[str, Dict[str, float]] = {}

        # Status effects and their chances
        self.status_effects = {
            "burn": {"damage": 0.0625, "attack_modifier": 0.5},
            "poison": {"damage": 0.125},
            "badly_poison": {"damage": 0.125, "stack": True},
            "paralyze": {"speed_modifier": 0.5, "skip_chance": 0.25},
            "sleep": {"skip_chance": 1.0, "max_turns": 3},
            "freeze": {"skip_chance": 1.0, "thaw_chance": 0.2},
        }

    async def cog_load(self):
        """Load type effectiveness data when cog starts"""
        await self.load_type_chart()

    async def load_type_chart(self):
        """Load type effectiveness data from PokeAPI"""
        types = [
            "normal",
            "fire",
            "water",
            "electric",
            "grass",
            "ice",
            "fighting",
            "poison",
            "ground",
            "flying",
            "psychic",
            "bug",
            "rock",
            "ghost",
            "dragon",
            "dark",
            "steel",
            "fairy",
        ]

        for type_name in types:
            if type_name not in self.type_chart:
                self.type_chart[type_name] = {}

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://pokeapi.co/api/v2/type/{type_name}") as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # No damage to
                        for t in data["damage_relations"]["no_damage_to"]:
                            self.type_chart[type_name][t["name"]] = 0.0

                        # Half damage to
                        for t in data["damage_relations"]["half_damage_to"]:
                            self.type_chart[type_name][t["name"]] = 0.5

                        # Double damage to
                        for t in data["damage_relations"]["double_damage_to"]:
                            self.type_chart[type_name][t["name"]] = 2.0

                        # Normal damage to (not specified in API)
                        for t in types:
                            if t not in self.type_chart[type_name]:
                                self.type_chart[type_name][t] = 1.0

    async def get_pokemon_types(self, pokemon_id: int) -> List[str]:
        """Get Pokemon types from PokeAPI"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [t["type"]["name"] for t in data["types"]]
                return ["normal"]  # Fallback type

    def calculate_type_effectiveness(self, move_type: str, defender_types: List[str]) -> float:
        """Calculate type effectiveness multiplier"""
        multiplier = 1.0
        for def_type in defender_types:
            multiplier *= self.type_chart.get(move_type, {}).get(def_type, 1.0)
        return multiplier

    def apply_status_effects(self, pokemon_data: Dict) -> Tuple[int, str]:
        """Apply status effects and return damage and message"""
        if "status" not in pokemon_data:
            return 0, ""

        status = pokemon_data["status"]
        damage = 0
        message = ""

        if status["condition"] == "burn":
            max_hp = self.calculate_hp(pokemon_data["pokemon"])
            damage = int(max_hp * self.status_effects["burn"]["damage"])
            message = f"{pokemon_data['pokemon']['name'].title()} is hurt by its burn!"

        elif status["condition"] == "poison":
            max_hp = self.calculate_hp(pokemon_data["pokemon"])
            if status.get("toxic_counter", 0) > 0:  # Toxic
                damage = int(
                    max_hp * self.status_effects["badly_poison"]["damage"] * status["toxic_counter"]
                )
                status["toxic_counter"] += 1
            else:  # Regular poison
                damage = int(max_hp * self.status_effects["poison"]["damage"])
            message = f"{pokemon_data['pokemon']['name'].title()} is hurt by poison!"

        elif status["condition"] == "sleep":
            status["turns_left"] = status.get("turns_left", 0) - 1
            if status["turns_left"] <= 0:
                del pokemon_data["status"]
                message = f"{pokemon_data['pokemon']['name'].title()} woke up!"
            else:
                message = f"{pokemon_data['pokemon']['name'].title()} is fast asleep!"

        elif status["condition"] == "freeze":
            if random.random() < self.status_effects["freeze"]["thaw_chance"]:
                del pokemon_data["status"]
                message = f"{pokemon_data['pokemon']['name'].title()} thawed out!"

        return damage, message

    async def get_move_data(self, move_name: str) -> Optional[Dict]:
        """Fetch move data from PokeAPI"""
        if move_name in self.move_cache:
            return self.move_cache[move_name]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/move/{move_name.lower()}") as resp:
                if resp.status == 200:
                    move_data = await resp.json()
                    self.move_cache[move_name] = move_data
                    return move_data
                return None

    @commands.group(invoke_without_command=True)
    async def battle(self, ctx):
        """Pokemon battle commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @battle.command(name="challenge")
    async def challenge_trainer(self, ctx, user: discord.Member, pokemon_name: str):
        """Challenge another trainer to a battle"""
        if ctx.author.id in self.battle_locks:
            return await ctx.send("You're already in a battle!")
        if user.id in self.battle_locks:
            return await ctx.send("That trainer is already in a battle!")
        if user.bot:
            return await ctx.send("You can't battle with bots!")
        if user == ctx.author:
            return await ctx.send("You can't battle yourself!")

        try:
            # Get challenger's Pokemon
            challenger_pokemon = await self.bot.db.fetchrow(
                "SELECT * FROM pokemon WHERE user_id = $1 AND LOWER(name) = LOWER($2)",
                ctx.author.id,
                pokemon_name,
            )
            if not challenger_pokemon:
                return await ctx.send("You don't have that Pokemon!")

            # Create battle session
            battle_data = {
                "trainers": {
                    ctx.author.id: {
                        "pokemon": challenger_pokemon,
                        "current_hp": self.calculate_hp(challenger_pokemon),
                        "moves": await self.get_pokemon_moves(challenger_pokemon["pokemon_id"]),
                    },
                    user.id: None,  # Will be filled when opponent accepts
                },
                "current_turn": None,
                "message": None,
            }
            self.active_battles[ctx.channel.id] = battle_data
            self.battle_locks[ctx.author.id] = True

            # Send challenge
            embed = discord.Embed(
                title="Pokemon Battle Challenge!",
                description=f"{ctx.author.mention} challenges {user.mention} to a battle!\n"
                f"Their Pokemon: Level {challenger_pokemon['level']} {challenger_pokemon['name'].title()}\n"
                f"{user.mention}, use `!battle accept <pokemon>` to accept!",
                color=discord.Color.red(),
            )
            battle_data["message"] = await ctx.send(embed=embed)

            # Wait for acceptance or timeout
            try:
                await asyncio.sleep(60)  # 1 minute timeout
                if ctx.channel.id in self.active_battles:
                    await ctx.send("Challenge timed out!")
                    await self.end_battle(ctx)
            except Exception:
                pass

        except Exception as e:
            await ctx.send(f"Error starting battle: {e}")
            await self.end_battle(ctx)

    @battle.command(name="accept")
    async def accept_challenge(self, ctx, pokemon_name: str):
        """Accept a battle challenge"""
        if ctx.channel.id not in self.active_battles:
            return await ctx.send("No active challenge in this channel!")

        battle = self.active_battles[ctx.channel.id]
        if ctx.author.id not in battle["trainers"]:
            return await ctx.send("This challenge isn't for you!")
        if battle["trainers"][ctx.author.id] is not None:
            return await ctx.send("You've already accepted!")

        try:
            # Get opponent's Pokemon
            opponent_pokemon = await self.bot.db.fetchrow(
                "SELECT * FROM pokemon WHERE user_id = $1 AND LOWER(name) = LOWER($2)",
                ctx.author.id,
                pokemon_name,
            )
            if not opponent_pokemon:
                return await ctx.send("You don't have that Pokemon!")

            # Set up opponent's Pokemon
            battle["trainers"][ctx.author.id] = {
                "pokemon": opponent_pokemon,
                "current_hp": self.calculate_hp(opponent_pokemon),
                "moves": await self.get_pokemon_moves(opponent_pokemon["pokemon_id"]),
            }
            self.battle_locks[ctx.author.id] = True

            # Start battle
            battle["current_turn"] = random.choice(list(battle["trainers"].keys()))
            await self.update_battle_embed(ctx)

            trainer = ctx.guild.get_member(battle["current_turn"])
            await ctx.send(f"Battle started! {trainer.mention}'s turn!")

        except Exception as e:
            await ctx.send(f"Error accepting battle: {e}")
            await self.end_battle(ctx)

    @battle.command(name="move")
    async def use_move(self, ctx, move_name: str):
        """Use a move in battle"""
        if ctx.channel.id not in self.active_battles:
            return await ctx.send("No active battle in this channel!")

        battle = self.active_battles[ctx.channel.id]
        if ctx.author.id != battle["current_turn"]:
            return await ctx.send("It's not your turn!")

        try:
            attacker = battle["trainers"][ctx.author.id]
            defender = battle["trainers"][
                next(uid for uid in battle["trainers"] if uid != ctx.author.id)
            ]

            # Check status effects that prevent moves
            if "status" in attacker:
                status = attacker["status"]
                if status["condition"] in ["sleep", "freeze"]:
                    damage, message = self.apply_status_effects(attacker)
                    await ctx.send(message)
                    if "status" in attacker:  # Still has status effect
                        # Switch turns
                        battle["current_turn"] = next(
                            uid for uid in battle["trainers"] if uid != ctx.author.id
                        )
                        trainer = ctx.guild.get_member(battle["current_turn"])
                        await ctx.send(f"{trainer.mention}'s turn!")
                        return
                elif status["condition"] == "paralyze":
                    if random.random() < self.status_effects["paralyze"]["skip_chance"]:
                        await ctx.send(
                            f"{attacker['pokemon']['name'].title()} is paralyzed and can't move!"
                        )
                        # Switch turns
                        battle["current_turn"] = next(
                            uid for uid in battle["trainers"] if uid != ctx.author.id
                        )
                        trainer = ctx.guild.get_member(battle["current_turn"])
                        await ctx.send(f"{trainer.mention}'s turn!")
                        return

            # Check if move exists
            move_name = move_name.lower()
            if move_name not in attacker["moves"]:
                return await ctx.send(
                    f"Your Pokemon doesn't know that move! Available moves: {', '.join(attacker['moves'])}"
                )

            # Get move data
            move_data = await self.get_move_data(move_name)
            if not move_data:
                return await ctx.send("Error getting move data!")

            # Get Pokemon types
            attacker_types = await self.get_pokemon_types(attacker["pokemon"]["pokemon_id"])
            defender_types = await self.get_pokemon_types(defender["pokemon"]["pokemon_id"])

            # Calculate STAB (Same Type Attack Bonus)
            stab = 1.5 if move_data["type"]["name"] in attacker_types else 1.0

            # Calculate type effectiveness
            type_effectiveness = self.calculate_type_effectiveness(
                move_data["type"]["name"], defender_types
            )

            # Calculate damage
            power = move_data.get("power", 0)
            if power:
                # Get stats with status modifications
                attack = json.loads(attacker["pokemon"]["stats"])["attack"]
                if "status" in attacker and attacker["status"]["condition"] == "burn":
                    attack *= self.status_effects["burn"]["attack_modifier"]

                defense = json.loads(defender["pokemon"]["stats"])["defense"]
                level = attacker["pokemon"]["level"]

                # Enhanced damage formula with STAB and type effectiveness
                damage = int(
                    ((2 * level / 5 + 2) * power * attack / defense / 50 + 2)
                    * stab
                    * type_effectiveness
                    * random.uniform(0.85, 1.0)
                )
            else:
                damage = 0

            # Apply damage
            defender["current_hp"] = max(0, defender["current_hp"] - damage)

            # Create move result message
            message_parts = [f"{attacker['pokemon']['name'].title()} used {move_name.title()}!"]

            if damage > 0:
                message_parts.append(f"Dealt {damage} damage!")
                if type_effectiveness > 1:
                    message_parts.append("It's super effective!")
                elif type_effectiveness < 1 and type_effectiveness > 0:
                    message_parts.append("It's not very effective...")
                elif type_effectiveness == 0:
                    message_parts.append("It had no effect...")

            # Apply status effects from move
            if "status" in move_data and random.random() < move_data["status_chance"]:
                defender["status"] = {
                    "condition": move_data["status"],
                    "turns_left": random.randint(
                        1, self.status_effects.get(move_data["status"], {}).get("max_turns", 1)
                    ),
                }
                message_parts.append(
                    f"{defender['pokemon']['name'].title()} was {move_data['status']}ed!"
                )

            await ctx.send("\n".join(message_parts))
            await self.update_battle_embed(ctx)

            # Apply end-of-turn status effects
            for trainer_data in battle["trainers"].values():
                if trainer_data:
                    damage, message = self.apply_status_effects(trainer_data)
                    if damage > 0:
                        trainer_data["current_hp"] = max(0, trainer_data["current_hp"] - damage)
                        await ctx.send(message)
                        await self.update_battle_embed(ctx)

            # Check for faint
            if defender["current_hp"] == 0:
                await self.handle_victory(ctx, ctx.author.id)
                return

            # Switch turns
            battle["current_turn"] = next(uid for uid in battle["trainers"] if uid != ctx.author.id)
            trainer = ctx.guild.get_member(battle["current_turn"])
            await ctx.send(f"{trainer.mention}'s turn!")

        except Exception as e:
            await ctx.send(f"Error using move: {e}")

    async def handle_victory(self, ctx, winner_id):
        """Handle battle victory"""
        battle = self.active_battles[ctx.channel.id]
        winner = ctx.guild.get_member(winner_id)
        loser = ctx.guild.get_member(next(uid for uid in battle["trainers"] if uid != winner_id))

        winner_pokemon = battle["trainers"][winner_id]["pokemon"]
        loser_pokemon = battle["trainers"][
            next(uid for uid in battle["trainers"] if uid != winner_id)
        ]["pokemon"]

        # Calculate XP gain
        xp_gain = int(loser_pokemon["level"] * 50 * random.uniform(0.8, 1.2))

        # Update winner's Pokemon
        old_level = winner_pokemon["level"]
        new_xp = winner_pokemon.get("xp", 0) + xp_gain
        new_level = self.calculate_level(new_xp)

        await self.bot.db.execute(
            "UPDATE pokemon SET xp = $1, level = $2 WHERE id = $3",
            new_xp,
            new_level,
            winner_pokemon["id"],
        )

        # Create victory embed
        embed = discord.Embed(
            title="Battle Victory!",
            description=f"{winner.mention}'s {winner_pokemon['name'].title()} wins!",
            color=discord.Color.green(),
        )
        embed.add_field(name="XP Gained", value=str(xp_gain))

        if new_level > old_level:
            embed.add_field(
                name="Level Up!",
                value=f"{winner_pokemon['name'].title()} grew to level {new_level}!",
            )

            # Check for evolution
            evolution = await self.check_evolution(winner_pokemon["pokemon_id"], new_level)
            if evolution:
                await self.evolve_pokemon(ctx, winner_pokemon["id"], evolution)
                embed.add_field(
                    name="Evolution!",
                    value=f"Your {winner_pokemon['name'].title()} evolved into {evolution['name'].title()}!",
                )

        await ctx.send(embed=embed)
        await self.end_battle(ctx)

    def calculate_hp(self, pokemon: Dict) -> int:
        """Calculate max HP for a Pokemon"""
        base_hp = json.loads(pokemon["stats"])["hp"]
        return int((2 * base_hp * pokemon["level"]) / 100 + pokemon["level"] + 10)

    def calculate_level(self, xp: int) -> int:
        """Calculate level from XP"""
        return min(100, int((xp / 1000) ** 0.5) + 1)

    async def get_pokemon_moves(self, pokemon_id: int) -> list:
        """Get available moves for a Pokemon"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Get up to 4 random moves
                    moves = [m["move"]["name"] for m in data["moves"]]
                    return random.sample(moves, min(4, len(moves)))
                return ["tackle"]  # Fallback move

    async def check_evolution(self, pokemon_id: int, level: int) -> Optional[Dict]:
        """Check if Pokemon can evolve"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for evolution in data.get("evolution_chain", {}).get("evolves_to", []):
                        if (
                            evolution.get("evolution_details", [{}])[0].get("min_level", 101)
                            <= level
                        ):
                            return evolution
                return None

    async def evolve_pokemon(self, ctx, pokemon_id: int, evolution: Dict):
        """Evolve a Pokemon"""
        # Get evolution data
        async with aiohttp.ClientSession() as session:
            async with session.get(evolution["species"]["url"]) as resp:
                if resp.status == 200:
                    evolution_data = await resp.json()

                    # Update Pokemon
                    await self.bot.db.execute(
                        "UPDATE pokemon SET name = $1, pokemon_id = $2 WHERE id = $3",
                        evolution_data["name"],
                        evolution_data["id"],
                        pokemon_id,
                    )

    async def update_battle_embed(self, ctx):
        """Update the battle status embed"""
        battle = self.active_battles[ctx.channel.id]

        embed = discord.Embed(title="Pokemon Battle", color=discord.Color.blue())

        for trainer_id, data in battle["trainers"].items():
            if data:  # Skip if trainer hasn't chosen Pokemon yet
                trainer = ctx.guild.get_member(trainer_id)
                pokemon = data["pokemon"]

                hp_percent = int(data["current_hp"] / self.calculate_hp(pokemon) * 100)
                hp_bar = "█" * (hp_percent // 10) + "░" * (10 - hp_percent // 10)

                # Get status condition if any
                status_text = ""
                if "status" in data:
                    status_text = f"\nStatus: {data['status']['condition'].upper()}"

                embed.add_field(
                    name=f"{trainer.display_name}'s {pokemon['name'].title()}",
                    value=f"Level: {pokemon['level']}\n"
                    f"HP: {data['current_hp']}/{self.calculate_hp(pokemon)} [{hp_bar}]{status_text}\n"
                    f"Moves: {', '.join(data['moves'])}",
                    inline=False,
                )

        await battle["message"].edit(embed=embed)

    async def end_battle(self, ctx):
        """End the battle and clean up"""
        if ctx.channel.id in self.active_battles:
            battle = self.active_battles[ctx.channel.id]
            for trainer_id in battle["trainers"]:
                if trainer_id in self.battle_locks:
                    del self.battle_locks[trainer_id]
            del self.active_battles[ctx.channel.id]


async def setup(bot):
    await bot.add_cog(PokemonBattle(bot))
