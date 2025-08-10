---
name: "Failing tests tracker"
about: "Track and fix failing test groups"
title: "Failing tests tracker"
labels: ["tests", "tracking"]
assignees: []
---

Use this issue to track and resolve test failures by group. Please link PRs that fix each item and check off when merged to main.

## Integration / Bot
- [ ] Integration: `tests/integration/test_bot_integration.py` (fix import for `src.lib.cog_utils` or adjust cog paths)

## Battle System / Database
- [ ] Battle DB: `tests/test_battle_integration.py` (install/configure `asyncpg` or switch to SQLite for tests)

## Dependency Injection / Services
- [ ] DI container: `tests/test_di_container.py` (export missing exceptions in `src/core/exceptions.py` or update references)

## Error Handling
- [ ] Error manager: `tests/test_error_manager.py` (decorator should be `@staticmethod` or classmethod-compatible)

## API Routes
- [ ] API routes: `tests/test_feature_*` and `tests/test_user_authentication.py` (fix `src/api/api/routes.py` relative imports; ensure `src/api/core` exists or correct paths)

## Media / FFmpeg / Player
- [ ] FFmpeg manager: `tests/test_ffmpeg_manager.py` (implement `src/core/ffmpeg_manager.py` or adjust tests)
- [ ] Media player: `tests/test_media_player.py`, `tests/test_media_playback.py` (add `src/core/media_player.py` or reconcile naming)

## Monitoring / Metrics
- [ ] Metrics: `tests/test_metrics.py` (align package path for metrics module; currently expects `src/monitoring`)

## OSRS / Models
- [ ] OSRS commands: `tests/test_osrs_commands.py` (provide `src/core/models/osrs_data.py` or update imports)
- [ ] World manager: `tests/test_world_manager.py` (ensure `World` is exported from `src/osrs/core/world_manager.py`)

## Plex
- [ ] Plex client: `tests/test_plex.py` (create `src/core/plex.py` or update path to `src/core/plex_manager.py`)
- [ ] Plex cog: `tests/test_plex_cog.py` (fix path `src/bot/discord/cogs/plex_cog.py` vs existing `src/core/plex_cog.py`)
- [ ] Plex selfbot: `tests/test_plex_selfbot.py` (provide `src/bot/plex_selfbot.py` or adjust test)

## Queue / Rate Limit / Redis
- [ ] Queue manager: `tests/test_queue_manager.py` (add `src/core/queue_manager.py` or re-point to existing)
- [ ] Rate limiter: `tests/test_rate_limiter.py` (add `src/core/rate_limiter.py` or adjust tests)
- [ ] Redis manager exceptions: `tests/test_redis_manager.py` (export `RedisConnectionError` and `RedisOperationError` in `src/core/exceptions.py`)

## Configuration / Secrets
- [ ] Secrets syntax: `tests/test_secrets.py` (fix unterminated triple-quoted string in test or fixture)

## Notes
- For import path mismatches, prefer updating code to match `tests/` where feasible, or update tests with consensus.
- Ensure CI runs `make test` and fails fast on collection errors.