# OSRS Code Integration Plan

## Phase 1: Core Systems
1. Game Mechanics and Models
   - Convert `MUser.ts` → `src/osrs/models/user.py`
   - Convert `Task.ts` → `src/osrs/core/task.py`
   - Convert `constants.ts` → `src/osrs/core/constants.py`

2. Combat and Skills
   - Convert combat_achievements/ → `src/osrs/core/combat/`
   - Convert skilling/ → `src/osrs/core/skills/`
   - Convert `addXP.ts` → `src/osrs/core/skills/xp.py`

3. Items and Economy
   - Convert `bankImage.ts` → `src/osrs/core/bank/image.py`
   - Convert `grandExchange.ts` → `src/osrs/core/economy/grand_exchange.py`
   - Convert `marketPrices.ts` → `src/osrs/core/economy/prices.py`

## Phase 2: Game Features
1. Minigames and Activities
   - Convert minions/ → `src/osrs/activities/`
   - Convert `colosseum.ts` → `src/osrs/activities/colosseum.py`
   - Convert `giantsFoundry.ts` → `src/osrs/activities/giants_foundry.py`

2. Player Housing
   - Convert poh/ → `src/osrs/features/poh/`
   - Convert `pohImage.ts` → `src/osrs/features/poh/image.py`

3. Collection and Achievements
   - Convert `collectionLogTask.ts` → `src/osrs/features/collection_log.py`
   - Convert `diaries.ts` → `src/osrs/features/achievement_diaries.py`
   - Convert `finishables.ts` → `src/osrs/features/completionist.py`

## Phase 3: Support Systems
1. Data Management
   - Convert data/ → `src/osrs/data/`
   - Convert `cache.ts` → `src/osrs/core/cache.py`
   - Convert resources/ → `src/osrs/resources/`

2. Analytics and Metrics
   - Convert `analytics.ts` → `src/osrs/core/analytics.py`
   - Convert `metrics.ts` → `src/osrs/core/metrics.py`
   - Convert `lootTrack.ts` → `src/osrs/core/loot_tracking.py`

3. Utility Functions
   - Convert util/ → `src/osrs/utils/`
   - Convert `DynamicButtons.ts` → `src/osrs/utils/ui.py`
   - Convert `PaginatedMessage.ts` → `src/osrs/utils/pagination.py`

## Implementation Notes

### Type Conversion Guide
- TypeScript interfaces → Python dataclasses or Pydantic models
- Enums → Python Enum classes
- async/await → Python asyncio
- Optional<T> → Optional[T]
- Array<T> → List[T]
- Record<K,V> → Dict[K,V]

### Key Considerations
1. Database Integration
   - Convert TypeScript DB queries to SQLAlchemy
   - Maintain transaction safety
   - Add proper indexing

2. Discord Integration
   - Use discord.py instead of discord.js
   - Convert event handlers
   - Adapt command structures

3. Image Generation
   - Port canvas operations to Pillow/PIL
   - Maintain image quality and performance
   - Consider caching strategies

### Testing Strategy
1. Create unit tests for each converted module
2. Implement integration tests for core features
3. Add end-to-end tests for critical paths

## Directory Structure
```
src/osrs/
├── activities/     # Minigames and activities
├── core/          # Core game systems
│   ├── bank/      # Banking system
│   ├── combat/    # Combat system
│   ├── economy/   # GE and trading
│   └── skills/    # Skill implementations
├── data/          # Game data and configs
├── features/      # Major game features
│   ├── poh/       # Player housing
│   └── pets/      # Pet system
├── models/        # Data models
├── resources/     # Static resources
└── utils/         # Utility functions
```

## Implementation Order
1. Core models and utilities
2. Basic game mechanics
3. Economy and items
4. Skills and activities
5. Advanced features
6. Support systems

## Next Steps
1. Create directory structure
2. Start with core models
3. Implement basic utilities
4. Begin feature conversion in order of dependency 