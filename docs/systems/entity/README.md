# Entity System

> **Note for contributors:** Please follow the [Documentation Standards](../../guides/documentation/standards.md) and use the [README template](../../templates/README-template.md) when updating or maintaining this document.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Draft
- **Authors**: [Contributors]
- **Related Documents**: [Inventory System](../inventory/README.md), [Combat System](../combat/README.md), [Achievement System](../achievement/README.md), [Optimized Implementation Strategy](../../../notes/optimized_implementation.md)

## Overview

The Entity System provides a unified, extensible base for all in-game entities (e.g., OSRS monsters, Pokemon, pets, NPCs). It enables code reuse, consistent data modeling, and shared logic across different game systems.

## Architecture

```
class BaseEntity:
    """Base class for all game entities."""
    def __init__(self, id: int, name: str, entity_type: str, base_data: dict, game_data: dict):
        self.id = id
        self.name = name
        self.entity_type = entity_type
        self.base_data = base_data  # Shared properties
        self.game_data = game_data  # Game-specific properties

class OSRSEntity(BaseEntity):
    # OSRS-specific logic
    pass

class PokemonEntity(BaseEntity):
    # Pokemon-specific logic
    pass
```

## Key Classes & Interfaces
- `BaseEntity`: Abstract base for all entities
- `OSRSEntity`, `PokemonEntity`: Game-specific extensions
- Integration with inventory, combat, and achievement systems

## Extending for Game-Specific Entities
- Inherit from `BaseEntity`
- Add/override methods for game-specific logic
- Store game-specific data in `game_data`

## Integration Points
- **Inventory System**: Entities can own or be owned by inventories
- **Combat System**: Entities participate in battles using shared combat logic
- **Achievement System**: Entities can trigger or be targets of achievements

## Best Practices
- Use `BaseEntity` for all new entity types
- Keep shared logic in the base class
- Use composition for complex behaviors
- Document all new entity types and methods

## Troubleshooting
| Issue | Solution | Notes |
|-------|----------|-------|
| Missing attributes | Ensure all required fields are set in `base_data` and `game_data` | Check constructor usage |
| Inheritance errors | Verify correct subclassing of `BaseEntity` | Use Python's `super()` |

## References
- [Optimized Implementation Strategy](../../../notes/optimized_implementation.md)
- [Game Systems Integration TODO](../../../notes/game_systems_integration_todo.md)
- [Inventory System](../inventory/README.md)
- [Combat System](../combat/README.md)
- [Achievement System](../achievement/README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Initial draft, created technical documentation for Entity System | [AI/Contributors] | 