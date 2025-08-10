"""
Configuration for data collection and integration.
Defines data sources, APIs, and settings for various integrations.
"""

import os

# API Configuration
API_CONFIG = {
    "discord": {
        "client_id": os.getenv("DISCORD_CLIENT_ID"),
        "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
        "bot_token": os.getenv("DISCORD_BOT_TOKEN"),
        "required_scopes": [
            "identify",
            "guilds",
            "voice",
            "activities.write",
            "rpc",
            "rpc.activities.write",
        ],
    },
    "plex": {
        "server_url": os.getenv("PLEX_SERVER_URL"),
        "token": os.getenv("PLEX_TOKEN"),
        "client_identifier": "Discord-Plex-Integration",
    },
    "pokemon": {
        "pokeapi_url": "https://pokeapi.co/api/v2",
        "rom_paths": {
            "gb": os.getenv("POKEMON_GB_ROMS_PATH", "data/roms/gb"),
            "gbc": os.getenv("POKEMON_GBC_ROMS_PATH", "data/roms/gbc"),
            "gba": os.getenv("POKEMON_GBA_ROMS_PATH", "data/roms/gba"),
        },
    },
    "osrs": {
        "api_url": "https://api.osrsbox.com/v2",
        "ge_url": "https://secure.runescape.com/m=itemdb_oldschool/api",
        "runelite_url": "https://api.runelite.net/runelite-1.10.8",
        "cache_path": "data/osrs/cache",
    },
}

# Data Collection Settings
COLLECTION_CONFIG = {
    "fetch_interval": 300,  # 5 minutes
    "cache_duration": 3600,  # 1 hour
    "max_retries": 3,
    "timeout": 30,
    "batch_size": 100,
}

# Game Data Sources
GAME_DATA_SOURCES = {
    "pokemon": {
        "games": [
            {"name": "Red/Blue", "platform": "gb", "parser": "gb_parser", "repo": "pret/pokered"},
            {"name": "Yellow", "platform": "gb", "parser": "gb_parser", "repo": "pret/pokeyellow"},
            {
                "name": "Gold/Silver",
                "platform": "gbc",
                "parser": "gbc_parser",
                "repo": "pret/pokegold",
            },
            {
                "name": "Crystal",
                "platform": "gbc",
                "parser": "gbc_parser",
                "repo": "pret/pokecrystal",
            },
            {
                "name": "Ruby/Sapphire",
                "platform": "gba",
                "parser": "gba_parser",
                "repo": "pret/pokeruby",
            },
            {
                "name": "Emerald",
                "platform": "gba",
                "parser": "gba_parser",
                "repo": "pret/pokeemerald",
            },
            {
                "name": "FireRed/LeafGreen",
                "platform": "gba",
                "parser": "gba_parser",
                "repo": "pret/pokefirered",
            },
        ],
        "data_sources": [
            {"name": "PokeAPI", "type": "api", "url": "https://pokeapi.co/api/v2"},
            {"name": "Pokemon Showdown", "type": "api", "repo": "smogon/pokemon-showdown"},
            {"name": "Damage Calculator", "type": "tool", "repo": "smogon/damage-calc"},
            {"name": "TCG Data", "type": "data", "repo": "PokemonTCG/pokemon-tcg-data"},
            {"name": "Sprites", "type": "assets", "repo": "PokeAPI/sprites"},
            {"name": "Pokemon JSON", "type": "data", "repo": "fanzeyi/pokemon.json"},
            {"name": "Veekun Pokedex", "type": "data", "repo": "veekun/pokedex"},
        ],
        "tools": [
            {"name": "Universal Randomizer", "repo": "Dabomstew/universal-pokemon-randomizer"},
            {"name": "Pokemon Game Editor", "repo": "Gamer2020/PokemonGameEditor"},
            {"name": "pkNX", "repo": "kwsch/pkNX"},
            {"name": "PokeFinder", "repo": "Admiral-Fish/PokeFinder"},
            {"name": "RNG Guides", "repo": "zaksabeast/PokemonRNGGuides"},
        ],
    },
    "osrs": {
        "data_types": [
            "items",
            "monsters",
            "quests",
            "locations",
            "ge_prices",
            "hiscores",
            "player_stats",
            "clan_data",
        ],
        "sources": ["osrsbox-db", "runelite-data", "wiki-data", "ge-tracker"],
        "tools": [
            {"name": "RuneLite", "repo": "runelite/runelite"},
            {"name": "Map Editor", "repo": "tpetrychyn/osrs-map-editor"},
            {"name": "OSRSBox DB", "repo": "osrsbox/osrsbox-db"},
        ],
    },
    "fortnite": {
        "sources": [
            {"name": "Epic Research", "repo": "MixV2/EpicResearch"},
            {"name": "Neonite V2", "repo": "NeoniteDev/NeoniteV2"},
            {"name": "Offsets", "repo": "paysonism/Fortnite-Offsets"},
            {"name": "Emotes Extended", "repo": "Franc1sco/Fortnite-Emotes-Extended"},
        ]
    },
    "cookie_clicker": {
        "sources": [
            {"name": "Cookie Clicker", "repo": "ozh/cookieclicker"},
            {"name": "Cookie Monster", "repo": "CookieMonsterTeam/CookieMonster"},
            {"name": "Clicker Framework", "repo": "snotwadd20/ClickerFramework"},
            {"name": "Frozen Cookies", "repo": "Icehawk78/FrozenCookies"},
        ]
    },
}

# Integration Settings
INTEGRATION_CONFIG = {
    "discord_activity": {
        "supported_platforms": ["desktop", "web"],
        "activity_types": {
            "plex_watch": {
                "name": "Plex Watch Together",
                "type": "ACTIVITY",
                "supported_media": ["movie", "show", "music"],
            },
            "pokemon_battle": {
                "name": "Pokemon Battle",
                "type": "ACTIVITY",
                "supported_games": ["gb", "gbc", "gba"],
            },
            "osrs_group": {
                "name": "OSRS Group Activity",
                "type": "ACTIVITY",
                "features": ["raids", "minigames", "group_ironman"],
            },
        },
    },
    "plex_integration": {
        "transcoding": {
            "video_quality": ["Original", "1080p", "720p", "480p"],
            "audio_quality": ["Original", "High", "Medium", "Low"],
            "max_bitrate": 20000,
        },
        "features": [
            "watch_together",
            "voice_chat_sync",
            "player_controls",
            "media_info",
            "user_presence",
        ],
    },
}

# Repository Sources
REPO_SOURCES = {
    "github": [
        # Discord Integration
        "discord/embedded-app-sdk",
        "discord/discord-api-spec",
        # Pokemon Game Data & Tools
        "pret/pokered",
        "pret/pokecrystal",
        "pret/pokeemerald",
        "pret/pokefirered",
        "pret/pokeyellow",
        "pret/pokeruby",
        "pret/pokegold",
        "pret/poketcg",
        "pret/pokeplatinum",
        "pret/pokeheartgold",
        "pret/pokediamond",
        "PokeAPI/pokeapi",
        "PokeAPI/sprites",
        "fanzeyi/pokemon.json",
        "smogon/pokemon-showdown",
        "smogon/damage-calc",
        "PokemonUnity/PokemonUnity",
        "kwsch/pkNX",
        "Kermalis/PokemonGameEngine",
        "Kermalis/PokemonBattleEngine",
        "Dabomstew/universal-pokemon-randomizer",
        "veekun/pokedex",
        "PokemonTCG/pokemon-tcg-data",
        "Gamer2020/PokemonGameEditor",
        "Admiral-Fish/PokeFinder",
        "zaksabeast/PokemonRNGGuides",
        "kinkofer/PokemonAPI",
        "berichan/SysBot.PokemonScarletViolet",
        # Pokemon GO Related
        "Grover-c13/PokeGOAPI-Java",
        "tejado/pgoapi",
        "jabbink/PokemonGoBot",
        "NecronomiconCoding/NecroBot",
        "AHAAAAAAA/PokemonGo-Map",
        "PokemonGoF/PokemonGo-Bot",
        "PokemonGoF/PokemonGo-Web",
        "RocketMap/RocketMap",
        "mchristopher/PokemonGo-DesktopMap",
        # OSRS & RuneScape
        "runelite/runelite",
        "osrsbox/osrsbox-db",
        "tpetrychyn/osrs-map-editor",
        # Plex Integration
        "plexinc/plex-media-player",
        "Xwaler/PlexConverter-headless",
        # Spotify Integration
        "zmb3/spotify",
        "Spotifyd/spotifyd",
        "Rigellute/spotify-tui",
        "spotDL/spotify-downloader",
        "x0uid/SpotifyAdBlock",
        # Game Development Resources
        "chriscourses/pokemon-style-game",
        "FullScreenShenanigans/FullScreenPokemon",
        "lxgr-linux/pokete",
        "pagefaultgames/pokerogue",
        # Fortnite Related
        "MixV2/EpicResearch",
        "NeoniteDev/NeoniteV2",
        "paysonism/Fortnite-Offsets",
        "Franc1sco/Fortnite-Emotes-Extended",
        # Cookie Clicker
        "ozh/cookieclicker",
        "CookieMonsterTeam/CookieMonster",
        "snotwadd20/ClickerFramework",
        "Icehawk78/FrozenCookies",
        # Media & Downloads
        "yt-dlp/yt-dlp",
    ],
    "gitlab": ["2009scape/2009scape"],
}

# Cache Settings
CACHE_CONFIG = {
    "redis": {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0)),
    },
    "file_cache": {"base_path": "data/cache", "max_size": 1024 * 1024 * 1024},  # 1GB
}
