"""
Pokemon data collector that handles ROM parsing and PokeAPI data collection.
Implements ROM parsing for different Pokemon games and integrates with PokeAPI.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import struct
import json
import asyncio

from ..base_collector import BaseCollector
from ..config import API_CONFIG, GAME_DATA_SOURCES

logger = logging.getLogger(__name__)

class PokemonDataCollector(BaseCollector):
    """Collector for Pokemon game data from ROMs and PokeAPI."""
    
    def __init__(self):
        super().__init__("pokemon_collector")
        self.config = API_CONFIG['pokemon']
        self.game_config = GAME_DATA_SOURCES['pokemon']
        
        # ROM format specifications
        self.rom_specs = {
            'gb': {
                'header_size': 0x150,
                'bank_size': 0x4000,
                'map_header_size': 0x0C,
                'pokemon_base_stats_size': 0x1C
            },
            'gbc': {
                'header_size': 0x150,
                'bank_size': 0x4000,
                'map_header_size': 0x10,
                'pokemon_base_stats_size': 0x20
            },
            'gba': {
                'header_size': 0x200,
                'bank_size': 0x8000,
                'map_header_size': 0x14,
                'pokemon_base_stats_size': 0x28
            }
        }
    
    async def collect(self) -> Dict[str, Any]:
        """Collect Pokemon data from all configured sources."""
        data = {
            'api_data': await self._collect_api_data(),
            'rom_data': {}
        }
        
        # Check if any ROMs exist before attempting to parse them
        rom_paths = [
            self.config['rom_paths'].get('gb', ''),
            self.config['rom_paths'].get('gbc', ''),
            self.config['rom_paths'].get('gba', '')
        ]
        
        has_roms = any(
            os.path.exists(path) and any(os.listdir(path))
            for path in rom_paths if path
        )
        
        if has_roms:
            try:
                data['rom_data'] = await self._collect_rom_data()
            except Exception as e:
                logger.warning(f"Failed to collect ROM data: {e}")
                data['rom_data'] = {}
        else:
            logger.info("No ROM files found, skipping ROM data collection")
        
        return data
    
    async def _collect_api_data(self) -> Dict[str, Any]:
        """Collect data from PokeAPI."""
        api_data = {
            'pokemon': [],
            'moves': [],
            'items': [],
            'locations': []
        }
        
        # Use smaller batches and add delays to respect rate limits
        async def fetch_batch(urls: List[str], batch_size: int = 5) -> List[Dict]:
            results = []
            for i in range(0, len(urls), batch_size):
                batch = urls[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *[self.fetch_data(url) for url in batch],
                    return_exceptions=True
                )
                results.extend([r for r in batch_results if not isinstance(r, Exception)])
                await asyncio.sleep(1)  # Rate limiting delay
            return results
        
        # Prepare URLs for batch fetching
        pokemon_urls = [
            f"{self.config['pokeapi_url']}/pokemon/{i}"
            for i in range(1, 152)  # Gen 1 Pokemon
        ]
        move_urls = [
            f"{self.config['pokeapi_url']}/move/{i}"
            for i in range(1, 166)  # Gen 1 moves
        ]
        
        # Fetch data in batches
        try:
            api_data['pokemon'] = await fetch_batch(pokemon_urls)
            api_data['moves'] = await fetch_batch(move_urls)
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
            # Return partial data if available
            return api_data
        
        return api_data
    
    async def _collect_rom_data(self) -> Dict[str, Dict]:
        """Collect data from Pokemon ROMs."""
        rom_data = {}
        
        for game in self.game_config['games']:
            rom_path = os.path.join(self.config['rom_paths'][game['platform']], f"{game['name']}.{game['platform']}")
            if not os.path.exists(rom_path):
                logger.warning(f"ROM not found: {rom_path}")
                continue
            
            try:
                with open(rom_path, 'rb') as f:
                    rom_bytes = f.read()
                
                parser = getattr(self, f"_parse_{game['platform']}_rom")
                rom_data[game['name']] = await parser(rom_bytes)
                
            except Exception as e:
                logger.error(f"Error parsing ROM {game['name']}: {str(e)}")
        
        return rom_data
    
    async def _parse_gb_rom(self, rom_data: bytes) -> Dict[str, Any]:
        """Parse Game Boy Pokemon ROM data."""
        specs = self.rom_specs['gb']
        data = {
            'pokemon': await self._parse_gb_pokemon(rom_data),
            'moves': await self._parse_gb_moves(rom_data),
            'maps': await self._parse_gb_maps(rom_data),
            'items': await self._parse_gb_items(rom_data)
        }
        return data
    
    async def _parse_gb_pokemon(self, rom_data: bytes) -> List[Dict]:
        """Parse Pokemon data from GB ROM."""
        pokemon_list = []
        base_stats_addr = self._find_pattern(rom_data, b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00')
        
        if base_stats_addr:
            for i in range(151):  # Original 151 Pokemon
                offset = base_stats_addr + (i * self.rom_specs['gb']['pokemon_base_stats_size'])
                stats = struct.unpack('BBBBBBBB', rom_data[offset:offset + 8])
                
                pokemon = {
                    'id': i + 1,
                    'base_stats': {
                        'hp': stats[0],
                        'attack': stats[1],
                        'defense': stats[2],
                        'speed': stats[3],
                        'special': stats[4]
                    },
                    'types': list(struct.unpack('BB', rom_data[offset + 8:offset + 10])),
                    'catch_rate': rom_data[offset + 10],
                    'base_exp': rom_data[offset + 11]
                }
                pokemon_list.append(pokemon)
        
        return pokemon_list
    
    async def _parse_gb_moves(self, rom_data: bytes) -> List[Dict]:
        """Parse move data from GB ROM."""
        moves_list = []
        moves_addr = self._find_pattern(rom_data, b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00')
        
        if moves_addr:
            for i in range(165):  # Original moves
                offset = moves_addr + (i * 6)  # Move data is 6 bytes
                move_data = struct.unpack('BBBBBB', rom_data[offset:offset + 6])
                
                move = {
                    'id': i + 1,
                    'effect': move_data[0],
                    'power': move_data[1],
                    'type': move_data[2],
                    'accuracy': move_data[3],
                    'pp': move_data[4]
                }
                moves_list.append(move)
        
        return moves_list
    
    async def _parse_gb_maps(self, rom_data: bytes) -> List[Dict]:
        """Parse map data from GB ROM."""
        maps_list = []
        maps_addr = self._find_pattern(rom_data, b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00')
        
        if maps_addr:
            current_addr = maps_addr
            while current_addr < len(rom_data) - self.rom_specs['gb']['map_header_size']:
                map_header = rom_data[current_addr:current_addr + self.rom_specs['gb']['map_header_size']]
                
                if not any(map_header):  # Check if all bytes are zero
                    break
                
                map_data = {
                    'width': map_header[0],
                    'height': map_header[1],
                    'tileset': map_header[2],
                    'connections': await self._parse_map_connections(rom_data, current_addr + 3)
                }
                maps_list.append(map_data)
                
                current_addr += self.rom_specs['gb']['map_header_size']
        
        return maps_list
    
    async def _parse_map_connections(self, rom_data: bytes, offset: int) -> Dict[str, int]:
        """Parse map connection data."""
        return {
            'north': int.from_bytes(rom_data[offset:offset + 4], byteorder='little'),
            'south': int.from_bytes(rom_data[offset + 4:offset + 8], byteorder='little'),
            'west': int.from_bytes(rom_data[offset + 8:offset + 12], byteorder='little'),
            'east': int.from_bytes(rom_data[offset + 12:offset + 16], byteorder='little')
        }
    
    async def _parse_gb_items(self, rom_data: bytes) -> List[Dict]:
        """Parse item data from GB ROM."""
        items_list = []
        items_addr = self._find_pattern(rom_data, b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00')
        
        if items_addr:
            for i in range(255):  # Max items
                offset = items_addr + (i * 4)  # Item data is 4 bytes
                item_data = struct.unpack('BBBB', rom_data[offset:offset + 4])
                
                if not any(item_data):  # Check if all bytes are zero
                    break
                
                item = {
                    'id': i + 1,
                    'price': item_data[0] | (item_data[1] << 8),
                    'effect': item_data[2],
                    'flags': item_data[3]
                }
                items_list.append(item)
        
        return items_list
    
    def _find_pattern(self, data: bytes, pattern: bytes) -> Optional[int]:
        """Find a pattern in the ROM data."""
        try:
            return data.index(pattern)
        except ValueError:
            return None
    
    async def process_item(self, item: Any) -> Any:
        """Process a single item (implemented for BaseCollector compatibility)."""
        return item 