# OSRS API Documentation

> **Note for contributors:** Please follow the [Documentation Standards](../../guides/documentation/standards.md) and use the [API documentation template](../../templates/api-template.md) when updating or adding endpoints to this document.

## Metadata
- **Last Updated**: 2024-06-07
- **Version**: 1.0.0
- **Status**: Audited & Updated
- **Authors**: [Contributors]
- **Related Documents**: [OSRS Commands](./commands.md), [API Documentation Template](../../templates/api-template.md)

## Overview

The OSRS API provides interfaces for interacting with Old School RuneScape data and functionality. This API supports skill tracking, player stats, item information, and game mechanics integration.

## Base URL
```
https://api.example.com/v1/osrs
```

## Authentication

### API Key
```http
Authorization: Bearer <osrs_api_key>
```

## Rate Limiting

- Rate limit: 100 requests per minute
- Headers:
  - `X-RateLimit-Limit`: 100
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time in Unix timestamp

## Endpoints

### Player Stats

#### GET /player/{username}/stats
Retrieve player skill statistics.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | OSRS username |
| skills | string | No | Comma-separated list of skills |

**Response**
```json
{
    "status": "success",
    "data": {
        "username": "string",
        "combat_level": 126,
        "skills": {
            "attack": {
                "level": 99,
                "experience": 13034431
            },
            "strength": {
                "level": 99,
                "experience": 13034431
            }
        },
        "updated_at": "2024-02-16T12:00:00Z"
    }
}
```

### Items

#### GET /items
Retrieve item information.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| ids | string | No | Comma-separated item IDs |
| name | string | No | Item name search |
| limit | integer | No | Max items to return |

**Response**
```json
{
    "status": "success",
    "data": [
        {
            "id": 4151,
            "name": "Abyssal whip",
            "description": "A weapon from the Abyss.",
            "tradeable": true,
            "price": {
                "current": 2500000,
                "trend": "rising"
            }
        }
    ],
    "metadata": {
        "total": 100,
        "limit": 10,
        "offset": 0
    }
}
```

### Grand Exchange

#### GET /ge/item/{id}/price
Get current Grand Exchange price for an item.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | integer | Yes | Item ID |
| history | boolean | No | Include price history |

**Response**
```json
{
    "status": "success",
    "data": {
        "item_id": 4151,
        "name": "Abyssal whip",
        "price": 2500000,
        "trend": "rising",
        "history": [
            {
                "date": "2024-02-15",
                "price": 2450000
            }
        ]
    }
}
```

### Combat

#### POST /combat/calculate
Calculate combat-related statistics.

**Request Body**
```json
{
    "attack": 99,
    "strength": 99,
    "defence": 99,
    "hitpoints": 99,
    "prayer": 99,
    "ranged": 99,
    "magic": 99
}
```

**Response**
```json
{
    "status": "success",
    "data": {
        "combat_level": 126,
        "attack_style": "melee",
        "max_hit": 47,
        "accuracy": 234
    }
}
```

### Achievements

#### GET /achievements/{username}
Get player achievement status.

**Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | OSRS username |
| category | string | No | Achievement category |

**Response**
```json
{
    "status": "success",
    "data": {
        "total": 150,
        "completed": 75,
        "in_progress": 25,
        "achievements": [
            {
                "id": "quest_cape",
                "name": "Quest Point Cape",
                "status": "completed",
                "completed_at": "2024-01-15T00:00:00Z"
            }
        ]
    }
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('wss://api.example.com/v1/osrs/ws');
```

### Events

#### Player Updates
```json
{
    "type": "skill_update",
    "data": {
        "username": "player123",
        "skill": "woodcutting",
        "level": 70,
        "experience": 737627
    }
}
```

#### Price Updates
```json
{
    "type": "price_update",
    "data": {
        "item_id": 4151,
        "price": 2550000,
        "trend": "rising"
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
| PLAYER_NOT_FOUND | Player username not found |
| ITEM_NOT_FOUND | Item ID not found |
| INVALID_STATS | Invalid skill statistics |
| RATE_LIMITED | Too many requests |
| API_ERROR | General API error |

## SDK Examples

### Python
```python
from osrs_client import OSRSClient

client = OSRSClient('api_key')
stats = client.get_player_stats('username')
```

### JavaScript
```javascript
import { OSRSClient } from 'osrs-client';

const client = new OSRSClient('api_key');
const stats = await client.getPlayerStats('username');
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
- [OSRS Commands](./commands.md)
- [OSRS System README](./README.md)

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-07 | 1.0.0 | Audited, added metadata, troubleshooting, references, and changelog sections | [AI/Contributors] |

_Last Updated: February 2024_ 