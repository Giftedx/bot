# Project Directory Structure

```
bot-1/
├── config/
├── data/
├── database/
├── deploy/
├── discord_bot/
├── docker/
├── docs/
│   ├── deployment/
│   │   ├── deployment-guide.md
│   │   └── setup.md
│   ├── development/
│   │   ├── development-guide.md
│   │   └── setup.md
│   ├── project/
│   │   └── SLASH_MIGRATION.md
│   └── DEVELOPMENT.md
├── frontend/
├── grafana/
├── infrastructure/
├── logs/
├── migrations/
├── notes/
│   ├── overview.md
│   └── refactoring_progress.md
├── plex_api/
├── prometheus/
├── reference_repos/
├── repos/
│   ├── core_libraries/
│   ├── discord.js-selfbot-v13/
│   ├── discord.js/
│   └── plex_debrid/
├── scripts/
│   └── move_unique_code.py
├── security/
├── services/
├── setup/
├── src/
│   ├── bot/
│   ├── data_collection/
│   │   └── api_integration/
│   │       └── repo_scanner.py
│   ├── osrs/
│   │   └── mechanics.py
│   ├── tools/
│   │   └── code_analyzer.py
│   └── repo_manager.py
├── unique_osrs_code/
├── .env
├── package.json
├── README.md
├── requirements.txt
└── setup.py

bot-1/
├── src/                           # Main source code directory
│   ├── api/                       # API-related code
│   ├── app/                      
│   ├── bot/                      # Bot core functionality
│   ├── cache/                    # Caching mechanisms
│   ├── client/                   # Client-side code
│   ├── collectors/               # Data collection modules
│   ├── config/                   # Configuration files
│   ├── core/                     # Core application logic
│   ├── data/                     # Data storage and management
│   ├── database/                 # Database related code
│   ├── data_collection/          # Data collection utilities
│   ├── discord_bot/              # Discord bot specific code
│   ├── features/                 # Feature implementations
│   ├── integrations/             # Third-party integrations
│   ├── launcher/                 # Application launcher
│   ├── lib/                      # Library code
│   ├── media/                    # Media handling
│   ├── models/                   # Data models
│   ├── osrs/                     # Old School RuneScape specific code
│   ├── pets/                     # Pet-related features
│   ├── pokemon/                  # Pokemon-related features
│   ├── server/                   # Server-side code
│   ├── services/                 # Service implementations
│   ├── shared/                   # Shared utilities
│   ├── systems/                  # System components
│   ├── tools/                    # Development tools
│   ├── types/                    # Type definitions
│   ├── ui/                       # User interface components
│   ├── utils/                    # Utility functions
│   └── web_server/               # Web server implementation

├── services/                      # Microservices
│   ├── discord/                  # Discord service
│   ├── frontend/                 # Frontend service
│   ├── game/                     # Game service
│   ├── identity/                 # Identity/auth service
│   ├── media/                    # Media service
│   └── realtime/                 # Real-time communication service

├── config/                        # Configuration files
├── data/                         # Data storage
├── database/                     # Database files
├── deploy/                       # Deployment configurations
├── discord_bot/                  # Discord bot specific files
├── docker/                       # Docker configurations
├── docs/                         # Documentation
│   ├── deployment/               # Deployment guides
│   ├── development/              # Development guides
│   └── project/                  # Project documentation

├── frontend/                      # Frontend application
├── grafana/                      # Monitoring dashboards
├── infrastructure/               # Infrastructure code
├── logs/                         # Application logs
├── migrations/                   # Database migrations
├── notes/                        # Project notes
├── plex_api/                     # Plex API integration
├── prometheus/                   # Monitoring configuration
├── reference_repos/              # Reference repositories
├── scripts/                      # Utility scripts
├── security/                     # Security configurations
├── setup/                        # Setup scripts
├── tests/                        # Test files
├── unique_osrs_code/             # OSRS specific implementations
└── utils/                        # Utility functions

# Configuration Files
├── .env                          # Environment variables
├── .gitattributes               # Git attributes
├── .gitignore                   # Git ignore rules
├── package.json                 # Node.js dependencies
├── requirements.txt             # Python dependencies
├── setup.py                     # Python setup configuration
└── tsconfig.json                # TypeScript configuration