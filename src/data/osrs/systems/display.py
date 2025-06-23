from typing import List, Dict, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import math
import asyncio
from pathlib import Path
import discord
from PIL import Image, ImageDraw, ImageFont
import io

from .movement import Tile, TileType, Area, MovementSystem
from .agility import AgilityObstacle, AgilityCourse, AgilitySystem


class DisplayMode(Enum):
    TEXT = "text"
    VISUAL = "visual"
    BOTH = "both"


class MapSymbol(Enum):
    PLAYER = "@"
    WALL = "█"
    GROUND = "·"
    WATER = "≈"
    AGILITY = "A"
    DOOR = "+"
    GATE = "="
    LADDER = "H"
    STAIRS = "S"
    NPC = "N"
    ITEM = "i"
    COMBAT = "!"


@dataclass
class ViewPort:
    """Represents the visible area around the player."""

    width: int
    height: int
    center_x: int
    center_y: int
    zoom: float = 1.0

    def get_bounds(self) -> Tuple[int, int, int, int]:
        """Get viewport boundaries."""
        half_width = int(self.width * self.zoom / 2)
        half_height = int(self.height * self.zoom / 2)
        return (
            self.center_x - half_width,
            self.center_y - half_height,
            self.center_x + half_width,
            self.center_y + half_height,
        )

    def is_in_view(self, x: int, y: int) -> bool:
        """Check if a point is within the viewport."""
        min_x, min_y, max_x, max_y = self.get_bounds()
        return min_x <= x <= max_x and min_y <= y <= max_y


@dataclass
class DisplayConfig:
    mode: DisplayMode = DisplayMode.TEXT
    use_emojis: bool = True
    compact_mode: bool = False
    show_details: bool = True
    color_scheme: Dict[str, str] = None


class DisplayFormatter:
    """Formats OSRS game information for Discord display"""

    SKILL_EMOJIS = {
        "attack": "⚔️",
        "strength": "💪",
        "defence": "🛡️",
        "ranged": "🏹",
        "prayer": "✨",
        "magic": "🔮",
        "runecrafting": "🌀",
        "construction": "🏠",
        "hitpoints": "❤️",
        "agility": "🏃",
        "herblore": "🌿",
        "thieving": "💰",
        "crafting": "🔨",
        "fletching": "🏃",
        "slayer": "💀",
        "hunter": "🦊",
        "mining": "⛏️",
        "smithing": "🔥",
        "fishing": "🎣",
        "cooking": "🍳",
        "firemaking": "🔥",
        "woodcutting": "🪓",
        "farming": "🌱",
    }

    def __init__(self, config: DisplayConfig = None):
        self.config = config or DisplayConfig()

    def format_stats(
        self, stats: Dict[str, int], include_xp: bool = True
    ) -> Union[str, discord.Embed]:
        """Format player stats for Discord display"""
        if self.config.mode == DisplayMode.TEXT:
            lines = []
            for skill, level in stats.items():
                emoji = self.SKILL_EMOJIS.get(skill, "") if self.config.use_emojis else ""
                xp_str = f" ({stats.get(f'{skill}_xp', 0):,} xp)" if include_xp else ""
                lines.append(f"{emoji} {skill.title()}: {level}{xp_str}")
            return "```\n" + "\n".join(lines) + "\n```"
        else:
            # Create visual stats display
            embed = discord.Embed(title="Player Stats")
            for skill, level in stats.items():
                emoji = self.SKILL_EMOJIS.get(skill, "")
                xp_str = f" ({stats.get(f'{skill}_xp', 0):,} xp)" if include_xp else ""
                embed.add_field(name=f"{emoji} {skill.title()}", value=f"Level {level}{xp_str}")
            return embed

    def format_combat(
        self,
        attacker_stats: Dict[str, int],
        defender_stats: Dict[str, int],
        hit_chance: float,
        max_hit: int,
    ) -> Union[str, discord.Embed]:
        """Format combat information for Discord display"""
        if self.config.mode == DisplayMode.TEXT:
            return (
                f"```\nAccuracy: {hit_chance*100:.1f}%\n"
                f"Max Hit: {max_hit}\n"
                f"Potential DPS: {(hit_chance * max_hit/2):.1f}\n```"
            )
        else:
            embed = discord.Embed(title="Combat Stats")
            embed.add_field(name="Accuracy", value=f"{hit_chance*100:.1f}%")
            embed.add_field(name="Max Hit", value=str(max_hit))
            embed.add_field(name="Potential DPS", value=f"{(hit_chance * max_hit/2):.1f}")
            return embed

    def format_drop_table(self, drops: List[Dict[str, any]]) -> Union[str, discord.Embed]:
        """Format drop table information for Discord display"""
        if self.config.mode == DisplayMode.TEXT:
            lines = []
            for drop in drops:
                chance = (
                    f"1/{int(1/drop['chance'])}" if drop["chance"] < 1 else f"{drop['chance']*100}%"
                )
                lines.append(f"{drop['item']}: {chance}")
            return "```\n" + "\n".join(lines) + "\n```"
        else:
            embed = discord.Embed(title="Drop Table")
            for drop in drops:
                chance = (
                    f"1/{int(1/drop['chance'])}" if drop["chance"] < 1 else f"{drop['chance']*100}%"
                )
                embed.add_field(name=drop["item"], value=chance)
            return embed

    def format_location(self, area_data: Dict[str, any]) -> Union[str, discord.Embed]:
        """Format location information for Discord display"""
        if self.config.mode == DisplayMode.TEXT:
            lines = [f"Location: {area_data['name']}"]
            if area_data.get("wilderness_level"):
                lines.append(f"Wilderness Level: {area_data['wilderness_level']}")
            if area_data.get("requirements"):
                lines.append("Requirements:")
                for req, value in area_data["requirements"].items():
                    lines.append(f"- {req}: {value}")
            return "```\n" + "\n".join(lines) + "\n```"
        else:
            embed = discord.Embed(title=area_data["name"])
            if area_data.get("wilderness_level"):
                embed.add_field(name="Wilderness Level", value=str(area_data["wilderness_level"]))
            if area_data.get("requirements"):
                reqs = "\n".join(
                    f"{req}: {value}" for req, value in area_data["requirements"].items()
                )
                embed.add_field(name="Requirements", value=reqs)
            return embed

    def format_inventory(self, items: List[Dict[str, any]]) -> Union[str, discord.Embed]:
        """Format inventory information for Discord display"""
        if self.config.mode == DisplayMode.TEXT:
            lines = []
            for item in items:
                qty_str = f" x{item['quantity']}" if item["quantity"] > 1 else ""
                lines.append(f"{item['name']}{qty_str}")
            return "```\n" + "\n".join(lines) + "\n```"
        else:
            embed = discord.Embed(title="Inventory")
            for item in items:
                qty_str = f" x{item['quantity']}" if item["quantity"] > 1 else ""
                embed.add_field(name=item["name"], value=qty_str if qty_str else "1")
            return embed

    def format_skill_progress(
        self, skill: str, level: int, xp: int, next_level_xp: int
    ) -> Union[str, discord.Embed]:
        """Format skill progress information for Discord display"""
        progress = (xp - self._level_to_xp(level)) / (next_level_xp - self._level_to_xp(level))
        bar_length = 20
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)

        if self.config.mode == DisplayMode.TEXT:
            emoji = self.SKILL_EMOJIS.get(skill, "") if self.config.use_emojis else ""
            return (
                f"```\n{emoji} {skill.title()} Level {level}\n"
                f"XP: {xp:,}/{next_level_xp:,}\n"
                f"Progress: [{bar}] {progress*100:.1f}%\n```"
            )
        else:
            embed = discord.Embed(title=f"{skill.title()} Progress")
            embed.add_field(name="Level", value=str(level), inline=True)
            embed.add_field(name="XP", value=f"{xp:,}/{next_level_xp:,}", inline=True)
            embed.add_field(name="Progress", value=f"[{bar}] {progress*100:.1f}%", inline=False)
            return embed

    def _level_to_xp(self, level: int) -> int:
        """Convert level to XP using OSRS formula"""
        xp = 0
        for i in range(1, level):
            xp += math.floor(i + 300 * 2 ** (i / 7))
        return math.floor(xp / 4)


class VisualMapGenerator:
    """Generates visual maps for areas and locations"""

    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size

    def generate_area_map(self, area_data: Dict[str, any]) -> discord.File:
        """Generate a visual map of an area"""
        width = len(area_data["tiles"][0]) * self.tile_size
        height = len(area_data["tiles"]) * self.tile_size

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw tiles
        for y, row in enumerate(area_data["tiles"]):
            for x, tile in enumerate(row):
                color = self._get_tile_color(tile["type"])
                x1, y1 = x * self.tile_size, y * self.tile_size
                x2, y2 = x1 + self.tile_size, y1 + self.tile_size
                draw.rectangle([x1, y1, x2, y2], fill=color)

                # Draw special markers for interactive tiles
                if tile.get("interaction_text"):
                    draw.text((x1 + 2, y1 + 2), "?", fill=(255, 255, 255))

        # Convert to bytes for Discord
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(buffer, filename="map.png")

    def _get_tile_color(self, tile_type: str) -> tuple:
        """Get color for different tile types"""
        colors = {
            "walkable": (100, 100, 100),
            "blocked": (50, 50, 50),
            "water": (0, 0, 255),
            "agility_obstacle": (255, 165, 0),
            "door": (139, 69, 19),
            "gate": (139, 69, 19),
            "ladder": (210, 180, 140),
            "stairs": (210, 180, 140),
        }
        return colors.get(tile_type, (0, 0, 0))


class DisplaySystem:
    def __init__(
        self,
        movement_system: MovementSystem,
        agility_system: Optional[AgilitySystem] = None,
        mode: DisplayMode = DisplayMode.TEXT,
    ):
        self.movement = movement_system
        self.agility = agility_system
        self.mode = mode
        self.viewport = ViewPort(
            width=31, height=15, center_x=0, center_y=0  # Odd numbers work better for centering
        )
        self.tile_size = 32  # Pixel size for graphical mode
        self.colors = {
            "player": "\033[1;32m",  # Bright green
            "ground": "\033[0;37m",  # Light gray
            "wall": "\033[1;30m",  # Dark gray
            "water": "\033[1;34m",  # Blue
            "agility": "\033[1;33m",  # Yellow
            "door": "\033[0;33m",  # Brown
            "combat": "\033[1;31m",  # Red
            "reset": "\033[0m",
        }
        self.graphical_assets = self._load_assets()
        self.frame_buffer: List[List[str]] = []
        self.needs_update: bool = True

    def _load_assets(self) -> Dict[str, any]:
        """Load graphical assets."""
        assets_dir = Path("assets/osrs")
        assets = {}

        if assets_dir.exists():
            # Load tile textures
            for tile_type in TileType:
                texture_path = assets_dir / f"tiles/{tile_type.value}.png"
                if texture_path.exists():
                    assets[f"tile_{tile_type.value}"] = texture_path

            # Load UI elements
            ui_dir = assets_dir / "ui"
            if ui_dir.exists():
                for ui_file in ui_dir.glob("*.png"):
                    assets[f"ui_{ui_file.stem}"] = ui_file

        return assets

    def update_viewport(self):
        """Update viewport based on player position."""
        x, y, _ = self.movement.current_position
        self.viewport.center_x = x
        self.viewport.center_y = y
        self.needs_update = True

    def _get_tile_symbol(self, tile: Tile) -> str:
        """Get the display symbol for a tile."""
        if not tile:
            return MapSymbol.GROUND.value

        symbol_map = {
            TileType.BLOCKED: MapSymbol.WALL.value,
            TileType.WATER: MapSymbol.WATER.value,
            TileType.AGILITY_OBSTACLE: MapSymbol.AGILITY.value,
            TileType.DOOR: MapSymbol.DOOR.value,
            TileType.GATE: MapSymbol.GATE.value,
            TileType.LADDER: MapSymbol.LADDER.value,
            TileType.STAIRS: MapSymbol.STAIRS.value,
            TileType.WALKABLE: MapSymbol.GROUND.value,
        }
        return symbol_map.get(tile.type, MapSymbol.GROUND.value)

    def _get_tile_color(self, tile: Tile) -> str:
        """Get the color code for a tile."""
        if not tile:
            return self.colors["ground"]

        color_map = {
            TileType.BLOCKED: self.colors["wall"],
            TileType.WATER: self.colors["water"],
            TileType.AGILITY_OBSTACLE: self.colors["agility"],
            TileType.DOOR: self.colors["door"],
            TileType.GATE: self.colors["door"],
            TileType.WALKABLE: self.colors["ground"],
        }
        return color_map.get(tile.type, self.colors["ground"])

    def render_text_mode(self) -> str:
        """Render the game state in text mode."""
        if not self.movement.current_area:
            return "No area loaded"

        output = []
        min_x, min_y, max_x, max_y = self.viewport.get_bounds()
        player_x, player_y, _ = self.movement.current_position

        # Add top border
        output.append("+" + "-" * (self.viewport.width + 2) + "+")

        for y in range(min_y, max_y + 1):
            row = ["|"]  # Left border
            for x in range(min_x, max_x + 1):
                if x == player_x and y == player_y:
                    row.append(self.colors["player"] + MapSymbol.PLAYER.value)
                else:
                    tile = (
                        self.movement.current_area.tiles[y][x]
                        if 0 <= y < len(self.movement.current_area.tiles)
                        and 0 <= x < len(self.movement.current_area.tiles[0])
                        else None
                    )
                    symbol = self._get_tile_symbol(tile)
                    color = self._get_tile_color(tile)
                    row.append(color + symbol)
            row.append(self.colors["reset"] + "|")  # Right border
            output.append("".join(row))

        # Add bottom border
        output.append("+" + "-" * (self.viewport.width + 2) + "+")

        # Add status information
        if self.agility:
            output.append(f"Agility Level: {self.agility.level}")
            if self.agility.current_course:
                output.append(f"Course: {self.agility.current_course.name}")
                output.append(f"Lap Count: {self.agility.current_course.lap_count}")

        output.append(f"Run Energy: {self.movement.run_energy:.1f}%")
        output.append(f"Position: ({player_x}, {player_y})")

        return "\n".join(output)

    async def render_graphical_mode(self) -> Dict[str, any]:
        """Render the game state in graphical mode."""
        if not self.movement.current_area:
            return {"error": "No area loaded"}

        scene_data = {
            "viewport": {
                "width": self.viewport.width * self.tile_size,
                "height": self.viewport.height * self.tile_size,
                "zoom": self.viewport.zoom,
            },
            "player": {
                "x": self.movement.current_position[0],
                "y": self.movement.current_position[1],
                "plane": self.movement.current_position[2],
            },
            "tiles": [],
            "objects": [],
            "ui": {
                "stats": {
                    "run_energy": self.movement.run_energy,
                    "agility_level": self.agility.level if self.agility else 1,
                },
                "location": self.movement.current_area.name,
                "coordinates": f"({self.movement.current_position[0]}, {self.movement.current_position[1]})",
            },
        }

        # Add visible tiles
        min_x, min_y, max_x, max_y = self.viewport.get_bounds()
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= y < len(self.movement.current_area.tiles) and 0 <= x < len(
                    self.movement.current_area.tiles[0]
                ):
                    tile = self.movement.current_area.tiles[y][x]
                    if tile:
                        scene_data["tiles"].append(
                            {
                                "x": x,
                                "y": y,
                                "type": tile.type.value,
                                "texture": f"tile_{tile.type.value}",
                                "walkable": tile.type != TileType.BLOCKED,
                            }
                        )

        # Add agility obstacles if applicable
        if self.agility and self.agility.current_course:
            for obstacle in self.agility.current_course.obstacles:
                if self.viewport.is_in_view(obstacle.tile.x, obstacle.tile.y):
                    scene_data["objects"].append(
                        {
                            "type": "agility_obstacle",
                            "x": obstacle.tile.x,
                            "y": obstacle.tile.y,
                            "name": obstacle.name,
                            "level_required": obstacle.level_required,
                        }
                    )

        return scene_data

    async def render_frame(self) -> Union[str, Dict[str, any]]:
        """Render a frame in the current display mode."""
        if self.needs_update:
            self.update_viewport()
            self.needs_update = False

        if self.mode == DisplayMode.TEXT:
            return self.render_text_mode()
        elif self.mode == DisplayMode.VISUAL:
            return await self.render_graphical_mode()
        else:  # BOTH
            return {
                "text": self.render_text_mode(),
                "graphical": await self.render_graphical_mode(),
            }

    def set_mode(self, mode: DisplayMode):
        """Change the display mode."""
        self.mode = mode
        self.needs_update = True

    def zoom(self, factor: float):
        """Adjust viewport zoom."""
        self.viewport.zoom = max(0.5, min(2.0, self.viewport.zoom * factor))
        self.needs_update = True

    async def animate_movement(self, start: Tuple[int, int], end: Tuple[int, int], duration: float):
        """Animate movement between two points."""
        start_time = asyncio.get_event_loop().time()
        distance = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)

        while True:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - start_time

            if elapsed >= duration:
                self.movement.current_position = (end[0], end[1], self.movement.current_position[2])
                break

            # Calculate interpolated position
            progress = elapsed / duration
            x = start[0] + (end[0] - start[0]) * progress
            y = start[1] + (end[1] - start[1]) * progress
            self.movement.current_position = (int(x), int(y), self.movement.current_position[2])

            self.needs_update = True
            await asyncio.sleep(0.05)  # 20 FPS

    async def animate_agility_obstacle(self, obstacle: AgilityObstacle):
        """Animate traversing an agility obstacle."""
        if not self.agility:
            return

        start_pos = (obstacle.tile.x, obstacle.tile.y)
        end_pos = (obstacle.next_tile.x, obstacle.next_tile.y)

        # Start animation
        self.needs_update = True
        await asyncio.sleep(0.5)

        # Animate movement
        await self.animate_movement(start_pos, end_pos, obstacle.completion_delay)

        # End animation
        self.needs_update = True
