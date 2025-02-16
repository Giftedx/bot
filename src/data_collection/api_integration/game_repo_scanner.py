"""
Specialized repository scanner for game-specific data extraction.
Handles ROM data, game mechanics, assets, and other game-specific information.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import json
import re
import struct
from pathlib import Path

from ..base_collector import BaseCollector
from ..config import GAME_DATA_SOURCES

logger = logging.getLogger(__name__)

class GameRepoScanner(BaseCollector):
    """Scanner for game-specific repositories."""
    
    def __init__(self, base_path: str = 'repos/games'):
        super().__init__("game_repo_scanner")
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
        # Initialize game-specific scanners
        self.scanners = {
            'pokemon': self._scan_pokemon_repo,
            'osrs': self._scan_osrs_repo,
            'fortnite': self._scan_fortnite_repo,
            'cookie_clicker': self._scan_cookie_clicker_repo
        }
    
    async def collect(self) -> Dict[str, Any]:
        """Collect game data from repositories."""
        game_data = {}
        
        for game_type, sources in GAME_DATA_SOURCES.items():
            if game_type in self.scanners:
                logger.info(f"Scanning {game_type} repositories...")
                game_data[game_type] = await self.scanners[game_type](sources)
        
        return game_data
    
    async def _scan_pokemon_repo(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Scan Pokemon repositories for game data."""
        data = {
            'games': {},
            'tools': {},
            'assets': {},
            'mechanics': {}
        }
        
        # Scan game repositories
        for game in sources['games']:
            repo_path = os.path.join(self.base_path, 'pokemon', game['repo'].replace('/', '_'))
            if os.path.exists(repo_path):
                data['games'][game['name']] = await self._extract_pokemon_game_data(
                    repo_path, game['platform']
                )
        
        # Scan data sources
        for source in sources.get('data_sources', []):
            if 'repo' in source:
                repo_path = os.path.join(self.base_path, 'pokemon', source['repo'].replace('/', '_'))
                if os.path.exists(repo_path):
                    data_type = source['type']
                    if data_type == 'data':
                        data['mechanics'][source['name']] = await self._extract_pokemon_mechanics(repo_path)
                    elif data_type == 'assets':
                        data['assets'][source['name']] = await self._extract_pokemon_assets(repo_path)
        
        # Scan tools
        for tool in sources.get('tools', []):
            repo_path = os.path.join(self.base_path, 'pokemon', tool['repo'].replace('/', '_'))
            if os.path.exists(repo_path):
                data['tools'][tool['name']] = await self._analyze_tool_repo(repo_path)
        
        return data
    
    async def _extract_pokemon_game_data(self, repo_path: str, platform: str) -> Dict[str, Any]:
        """Extract data from Pokemon game repositories."""
        game_data = {
            'rom_data': {},
            'maps': [],
            'scripts': [],
            'constants': {},
            'assets': {}
        }
        
        # Extract ROM data structures
        rom_structs_path = os.path.join(repo_path, 'src', 'data')
        if os.path.exists(rom_structs_path):
            for file in os.listdir(rom_structs_path):
                if file.endswith('.h') or file.endswith('.inc'):
                    structs = await self._parse_data_structures(os.path.join(rom_structs_path, file))
                    game_data['rom_data'].update(structs)
        
        # Extract map data
        maps_path = os.path.join(repo_path, 'data', 'maps')
        if os.path.exists(maps_path):
            game_data['maps'] = await self._extract_pokemon_maps(maps_path, platform)
        
        # Extract scripts
        scripts_path = os.path.join(repo_path, 'data', 'scripts')
        if os.path.exists(scripts_path):
            game_data['scripts'] = await self._extract_pokemon_scripts(scripts_path)
        
        # Extract constants
        constants_path = os.path.join(repo_path, 'constants')
        if os.path.exists(constants_path):
            game_data['constants'] = await self._extract_pokemon_constants(constants_path)
        
        # Extract assets
        assets_path = os.path.join(repo_path, 'graphics')
        if os.path.exists(assets_path):
            game_data['assets'] = await self._extract_pokemon_assets(assets_path)
        
        return game_data
    
    async def _parse_data_structures(self, file_path: str) -> Dict[str, Any]:
        """Parse C/ASM data structure definitions."""
        structs = {}
        current_struct = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Look for struct definitions
                    struct_match = re.match(r'struct\s+(\w+)\s*{', line)
                    if struct_match:
                        current_struct = struct_match.group(1)
                        structs[current_struct] = {'fields': [], 'size': 0}
                        continue
                    
                    # Look for field definitions
                    if current_struct and line and not line.startswith(('/*', '*/', '//')):
                        field_match = re.match(r'\s*(\w+)\s+(\w+)(\[\d+\])?;', line)
                        if field_match:
                            type_name, field_name, array_size = field_match.groups()
                            structs[current_struct]['fields'].append({
                                'name': field_name,
                                'type': type_name,
                                'array_size': array_size
                            })
                    
                    # End of struct
                    if line.startswith('}'):
                        current_struct = None
        
        except Exception as e:
            logger.error(f"Error parsing data structures in {file_path}: {str(e)}")
        
        return structs
    
    async def _extract_pokemon_maps(self, maps_path: str, platform: str) -> List[Dict[str, Any]]:
        """Extract map data from Pokemon game repositories."""
        maps = []
        
        for root, _, files in os.walk(maps_path):
            for file in files:
                if file.endswith(('.json', '.map', '.blk')):
                    try:
                        map_path = os.path.join(root, file)
                        map_data = await self._parse_map_file(map_path, platform)
                        if map_data:
                            maps.append(map_data)
                    except Exception as e:
                        logger.error(f"Error parsing map file {file}: {str(e)}")
        
        return maps
    
    async def _parse_map_file(self, file_path: str, platform: str) -> Optional[Dict[str, Any]]:
        """Parse a Pokemon map file."""
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                return json.load(f)
        
        # Parse binary map files
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                
                if platform in ['gb', 'gbc']:
                    return self._parse_gb_map(data)
                elif platform == 'gba':
                    return self._parse_gba_map(data)
        except Exception as e:
            logger.error(f"Error parsing binary map {file_path}: {str(e)}")
        
        return None
    
    async def _extract_pokemon_scripts(self, scripts_path: str) -> List[Dict[str, Any]]:
        """Extract script data from Pokemon game repositories."""
        scripts = []
        
        for root, _, files in os.walk(scripts_path):
            for file in files:
                if file.endswith(('.inc', '.s', '.asm')):
                    try:
                        script_path = os.path.join(root, file)
                        with open(script_path, 'r', encoding='utf-8') as f:
                            scripts.append({
                                'name': os.path.splitext(file)[0],
                                'path': os.path.relpath(script_path, scripts_path),
                                'content': f.read()
                            })
                    except Exception as e:
                        logger.error(f"Error reading script file {file}: {str(e)}")
        
        return scripts
    
    async def _extract_pokemon_constants(self, constants_path: str) -> Dict[str, Any]:
        """Extract constant definitions from Pokemon game repositories."""
        constants = {}
        
        for root, _, files in os.walk(constants_path):
            for file in files:
                if file.endswith(('.h', '.inc', '.s', '.asm')):
                    try:
                        const_path = os.path.join(root, file)
                        category = os.path.splitext(file)[0].lower()
                        
                        constants[category] = await self._parse_constants_file(const_path)
                    except Exception as e:
                        logger.error(f"Error parsing constants file {file}: {str(e)}")
        
        return constants
    
    async def _parse_constants_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a constants definition file."""
        constants = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Look for constant definitions
                    if line and not line.startswith(('/*', '*/', '//')):
                        # C-style defines
                        define_match = re.match(r'#define\s+(\w+)\s+(.+)', line)
                        if define_match:
                            name, value = define_match.groups()
                            constants[name] = value.strip()
                            continue
                        
                        # Assembly-style equates
                        equate_match = re.match(r'(\w+)\s+EQU\s+(.+)', line)
                        if equate_match:
                            name, value = equate_match.groups()
                            constants[name] = value.strip()
        
        except Exception as e:
            logger.error(f"Error parsing constants in {file_path}: {str(e)}")
        
        return constants
    
    async def _extract_pokemon_assets(self, assets_path: str) -> Dict[str, List[str]]:
        """Extract asset information from Pokemon game repositories."""
        assets = {
            'sprites': [],
            'tilesets': [],
            'backgrounds': [],
            'music': [],
            'sound_effects': []
        }
        
        for root, _, files in os.walk(assets_path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), assets_path)
                
                if file.endswith(('.png', '.bmp', '.4bpp', '.8bpp')):
                    if 'sprites' in rel_path.lower():
                        assets['sprites'].append(rel_path)
                    elif 'tilesets' in rel_path.lower():
                        assets['tilesets'].append(rel_path)
                    elif 'backgrounds' in rel_path.lower():
                        assets['backgrounds'].append(rel_path)
                elif file.endswith(('.mid', '.s', '.bin')) and 'sound' in rel_path.lower():
                    if 'music' in rel_path.lower():
                        assets['music'].append(rel_path)
                    else:
                        assets['sound_effects'].append(rel_path)
        
        return assets
    
    async def _extract_pokemon_mechanics(self, repo_path: str) -> Dict[str, Any]:
        """Extract game mechanics data from Pokemon repositories."""
        mechanics = {
            'battle': {},
            'evolution': {},
            'items': {},
            'moves': {},
            'abilities': {}
        }
        
        # Look for JSON data files
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.json'):
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            category = os.path.splitext(file)[0].lower()
                            if category in mechanics:
                                mechanics[category] = json.load(f)
                    except Exception as e:
                        logger.error(f"Error parsing mechanics file {file}: {str(e)}")
        
        return mechanics
    
    async def _scan_osrs_repo(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Scan OSRS repositories for game data."""
        data = {
            'game_data': {},
            'tools': {}
        }
        
        for tool in sources.get('tools', []):
            repo_path = os.path.join(self.base_path, 'osrs', tool['repo'].replace('/', '_'))
            if os.path.exists(repo_path):
                data['tools'][tool['name']] = await self._analyze_tool_repo(repo_path)
        
        return data
    
    async def _scan_fortnite_repo(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Scan Fortnite repositories for game data."""
        data = {
            'research': {},
            'tools': {}
        }
        
        for source in sources.get('sources', []):
            repo_path = os.path.join(self.base_path, 'fortnite', source['repo'].replace('/', '_'))
            if os.path.exists(repo_path):
                data['research'][source['name']] = await self._analyze_tool_repo(repo_path)
        
        return data
    
    async def _scan_cookie_clicker_repo(self, sources: Dict[str, Any]) -> Dict[str, Any]:
        """Scan Cookie Clicker repositories for game data."""
        data = {
            'game': {},
            'mods': {}
        }
        
        for source in sources.get('sources', []):
            repo_path = os.path.join(self.base_path, 'cookie_clicker', source['repo'].replace('/', '_'))
            if os.path.exists(repo_path):
                data['mods'][source['name']] = await self._analyze_tool_repo(repo_path)
        
        return data
    
    async def _analyze_tool_repo(self, repo_path: str) -> Dict[str, Any]:
        """Analyze a tool repository for useful information."""
        analysis = {
            'features': [],
            'apis': [],
            'dependencies': {},
            'docs': []
        }
        
        # Analyze repository contents
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Skip .git directory
                if '.git' in file_path:
                    continue
                
                # Look for API endpoints
                if file.endswith(('.py', '.js', '.java')):
                    endpoints = await self._find_api_endpoints(file_path)
                    analysis['apis'].extend(endpoints)
                
                # Parse dependencies
                if file in ['requirements.txt', 'package.json', 'build.gradle', 'pom.xml']:
                    deps = await self._parse_dependencies(file_path)
                    analysis['dependencies'].update(deps)
                
                # Collect documentation
                if file.endswith(('.md', '.rst', '.txt')):
                    rel_path = os.path.relpath(file_path, repo_path)
                    analysis['docs'].append(rel_path)
        
        return analysis
    
    def _parse_gb_map(self, data: bytes) -> Dict[str, Any]:
        """Parse Game Boy map format."""
        return {
            'width': data[0],
            'height': data[1],
            'tileset': data[2],
            'blocks': list(data[3:])
        }
    
    def _parse_gba_map(self, data: bytes) -> Dict[str, Any]:
        """Parse Game Boy Advance map format."""
        return {
            'width': struct.unpack('<H', data[0:2])[0],
            'height': struct.unpack('<H', data[2:4])[0],
            'border_width': data[4],
            'border_height': data[5],
            'blocks': list(struct.unpack(f'<{len(data[6:])//2}H', data[6:]))
        }
    
    async def process_item(self, item: Any) -> Any:
        """Process a single item (implemented for BaseCollector compatibility)."""
        return item 