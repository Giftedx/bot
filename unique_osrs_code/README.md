# Unique OSRS Code

This directory contains unique code preserved from the temp_osrs directory:

## Directory Structure
- `src/` - Contains the source code
  - `lib/` - Core library implementations
  - `tasks/` - Task implementations for various game activities
- `toolkit/` - Utility package for OSRS bot development
- `data/` - Game data and configuration files

## Components

### Toolkit Package
A utility package containing various tools and helpers for OSRS bot development.
Original location: temp_osrs/packages/toolkit

### Lib Directory
Contains unique implementations and modifications, including:
- Custom bank image generation (bankImage.ts)
- Grand Exchange implementation (grandExchange.ts)
- Collection log system (collectionLogTask.ts)
- Custom minigames and activities
- Analytics and metrics tracking
- And more...

### Tasks Directory
Contains unique task implementations for various game activities.

### Data Directory
Contains important game data and configuration files:
- Combat achievements data
- Item data
- Command configurations
- And more...

Note: While some of this code may be based on oldschoolbot, it contains unique modifications and implementations that were worth preserving.

## Integration Instructions
To integrate this code with the main OSRS codebase:

1. The toolkit package should be kept as a separate package
2. Lib implementations should be merged with src/osrs/core/
3. Tasks should be integrated into appropriate locations in src/osrs/
4. Data files should be moved to src/osrs/data/
