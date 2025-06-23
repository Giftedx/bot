# Pokemon API Documentation

> **Note for contributors:** Please follow the [Documentation Standards](../../guides/documentation/standards.md) and use the [API documentation template](../../templates/api-template.md) when updating or adding endpoints to this document.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Audited & Updated
- **Authors**: [Contributors]
- **Related Documents**: [Pokemon Commands](./commands.md), [API Documentation Template](../../templates/api-template.md)

## Overview

The Pokemon API provides interfaces for managing Pokemon data, battles, trades, and training mechanics. This API integrates with the Universal Data Layer to support cross-system functionality.

## Base URL
```
https://api.example.com/v1/pokemon
```

## Authentication

### API Key
```http
Authorization: Bearer <pokemon_api_key>
```

## Rate Limiting

- Rate limit: 100 requests per minute
- Headers:
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time in Unix timestamp

## Endpoints

### Pokemon Data

#### GET /pokemon/{id}
Retrieve Pokemon information.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | Yes | Pokemon ID or name |
| form | string | No | Specific form variant |

**Response**
```json
{
    "status": "success",
    "data": {
        "id": "25",
        "name": "Pikachu",
        "types": ["electric"],
        "stats": {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special-attack": 50,
            "special-defense": 50,
            "speed": 90
        },
        "abilities": [
            {
                "name": "Static",
                "is_hidden": false
            }
        ],
        "moves": [
            {
                "name": "Thunder Shock",
                "type": "electric",
                "power": 40,
                "accuracy": 100
            }
        ]
    }
}
```

### Player Pokemon

#### GET /trainer/{trainer_id}/pokemon
Retrieve trainer's Pokemon.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| trainer_id | string | Yes | Trainer's ID |
| box | integer | No | Specific box number |

**Response**
```json
{
    "status": "success",
    "data": {
        "pokemon": [
            {
                "uuid": "abc-123",
                "species": "Pikachu",
                "nickname": "Sparky",
                "level": 25,
                "experience": 15625,
                "moves": ["Thunder Shock", "Quick Attack"],
                "stats": {
                    "hp": 45,
                    "attack": 60
                }
            }
        ],
        "box_info": {
            "current": 1,
            "total": 8,
            "capacity": 30
        }
    }
}
```

### Battle System

#### POST /battle/start
Start a Pokemon battle.

**Request Body**
```json
{
    "trainer1_id": "user123",
    "trainer2_id": "user456",
    "format": "singles",
    "rules": {
        "level_cap": 50,
        "items_allowed": true
    }
}
```

**Response**
```json
{
    "status": "success",
    "data": {
        "battle_id": "battle-789",
        "turn": 1,
        "active_pokemon": {
            "trainer1": {
                "pokemon": "Pikachu",
                "hp": 45,
                "status": null
            },
            "trainer2": {
                "pokemon": "Charmander",
                "hp": 39,
                "status": null
            }
        }
    }
}
```

### Trading System

#### POST /trade/initiate
Initiate a Pokemon trade.

**Request Body**
```json
{
    "trainer1_id": "user123",
    "trainer2_id": "user456",
    "offered_pokemon": {
        "trainer1": ["pokemon-uuid-1"],
        "trainer2": ["pokemon-uuid-2"]
    }
}
```

**Response**
```json
{
    "status": "success",
    "data": {
        "trade_id": "trade-789",
        "status": "pending",
        "expiry": "2024-02-16T12:30:00Z",
        "pokemon": {
            "trainer1": [
                {
                    "uuid": "pokemon-uuid-1",
                    "species": "Pikachu",
                    "level": 25
                }
            ],
            "trainer2": [
                {
                    "uuid": "pokemon-uuid-2",
                    "species": "Charmander",
                    "level": 20
                }
            ]
        }
    }
}
```

### Evolution System

#### POST /pokemon/{pokemon_id}/evolve
Evolve a Pokemon.

**Request Body**
```json
{
    "item": "thunder-stone",
    "evolution": "Raichu"
}
```

**Response**
```json
{
    "status": "success",
    "data": {
        "pokemon_id": "pokemon-uuid-1",
        "from_species": "Pikachu",
        "to_species": "Raichu",
        "level": 25,
        "stats_change": {
            "hp": "+20",
            "attack": "+25"
        },
        "learned_moves": ["Thunder Punch"]
    }
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('wss://api.example.com/v1/pokemon/ws');
```

### Events

#### Battle Updates
```json
{
    "type": "battle_update",
    "data": {
        "battle_id": "battle-789",
        "turn": 2,
        "action": {
            "type": "move",
            "pokemon": "Pikachu",
            "move": "Thunder Shock",
            "damage": 15
        }
    }
}
```

#### Trade Updates
```json
{
    "type": "trade_update",
    "data": {
        "trade_id": "trade-789",
        "status": "completed",
        "timestamp": "2024-02-16T12:15:00Z"
    }
}
```

## Error Responses

### Error Format
```json
{
    "status": "error",
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
        "field": "Specific error details"
    }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| POKEMON_NOT_FOUND | Pokemon doesn't exist |
| INVALID_MOVE | Move not available |
| TRADE_ERROR | Trade validation failed |
| EVOLUTION_ERROR | Evolution requirements not met |
| BATTLE_ERROR | Battle execution failed |

## SDK Examples

### Python
```python
from pokemon_client import PokemonClient

client = PokemonClient('api_key')
pokemon = client.get_pokemon('Pikachu')
```

### JavaScript
```javascript
import { PokemonClient } from 'pokemon-client';

const client = new PokemonClient('api_key');
const pokemon = await client.getPokemon('Pikachu');
```

## Rate Limiting

### Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1619740800
```

### Response (429 Too Many Requests)
```json
{
    "status": "error",
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "details": {
        "reset_at": "2024-02-16T12:00:00Z"
    }
}
```

## Troubleshooting
| Issue | Solution | Notes |
|-------|----------|-------|
| 401 Unauthorized | Check your API key and authentication header | Ensure the key is valid and not expired |
| 429 Too Many Requests | Wait for the rate limit to reset | See `X-RateLimit-Reset` header |
| 404 Not Found | Verify endpoint URL and parameters | Check for typos or missing resources |
| 500 Internal Server Error | Try again later or contact support | May indicate a server issue |

## References
- [Documentation Standards](../../guides/documentation/standards.md)
- [API Documentation Template](../../templates/api-template.md)
- [Pokemon Commands](./commands.md)
- [Pokemon System README](./README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Audited, added metadata, troubleshooting, references, and changelog sections | [AI/Contributors] |

_Last Updated: February 2024_ 