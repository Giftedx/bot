# Achievement System

> **Note for contributors:** Please follow the [Documentation Standards](../../guides/documentation/standards.md) and use the [README template](../../templates/README-template.md) when updating or maintaining this document.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Draft
- **Authors**: [Contributors]
- **Related Documents**: [Entity System](../entity/README.md), [Inventory System](../inventory/README.md), [Combat System](../combat/README.md), [Optimized Implementation Strategy](../../../notes/optimized_implementation.md)

## Overview

The Achievement System provides a unified, extensible framework for tracking and rewarding player accomplishments across all game systems (e.g., OSRS, Pokemon, pets). It enables code reuse, consistent achievement logic, and shared reward mechanisms.

## Architecture

```
class BaseAchievement:
    """Base class for all achievements."""
    def __init__(self, id: int, name: str, description: str, points: int):
        self.id = id
        self.name = name
        self.description = description
        self.points = points

    def check_completion(self, player):
        # Shared completion logic
        pass

class OSRSAchievement(BaseAchievement):
    # OSRS-specific achievement logic
    pass

class PokemonAchievement(BaseAchievement):
    # Pokemon-specific achievement logic
    pass
```

## Key Classes & Interfaces
- `BaseAchievement`: Abstract base for all achievements
- `OSRSAchievement`, `PokemonAchievement`: Game-specific extensions
- Integration with entity, inventory, and combat systems

## Extending for Game-Specific Achievements
- Inherit from `BaseAchievement`
- Add/override methods for game-specific logic
- Use shared methods for common mechanics

## Integration Points
- **Entity System**: Achievements can be triggered by entity actions
- **Inventory System**: Inventory actions can unlock achievements
- **Combat System**: Combat outcomes can trigger achievements

## Best Practices
- Use `BaseAchievement` for all new achievement types
- Keep shared logic in the base class
- Use composition for complex achievement mechanics
- Document all new achievement types and methods

## Troubleshooting
| Issue | Solution | Notes |
|-------|----------|-------|
| Achievement not unlocking | Review `check_completion` logic | Check player state |
| Duplicate achievements | Ensure unique IDs for each achievement | Use a registry |

## References
- [Optimized Implementation Strategy](../../../notes/optimized_implementation.md)
- [Game Systems Integration TODO](../../../notes/game_systems_integration_todo.md)
- [Entity System](../entity/README.md)
- [Inventory System](../inventory/README.md)
- [Combat System](../combat/README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Initial draft, created technical documentation for Achievement System | [AI/Contributors] | 