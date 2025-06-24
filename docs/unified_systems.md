# Unified Systems

This project consolidates disparate helpers into three core modules:

| Module | Responsibility |
|--------|----------------|
| `src/core/unified_config.py` | Hierarchical configuration loader supporting YAML/JSON, env overrides, Vault/ dotenv secrets, auto-reload. |
| `src/core/unified_database.py` | Single SQLite/WAL manager with repository pattern and convenience helpers (pets, effects, watch history, etc.). |
| `src/core/error_manager.py` | Central error capture, retry logic, Prometheus counters, optional owner notifications. |

### Dependency Injection for Cogs

`src/lib/cog_utils.py` exposes `CogBase` and `CogDependencies`.

```python
class MyCommands(CogBase):
    def __init__(self, bot, **kwargs):
        super().__init__(bot, **kwargs)  # gives self.database, self.config, self.error_manager
```

### Metrics

`src/core/metrics.py` sets up Prometheus metrics and starts an internal server. A FastAPI wrapper in `src/core/metrics_endpoint.py` exposes these on `/metrics` (default port `8080`).

---

## Adding a New Repository

1. Define a dataclass model (e.g., `Pet`).
2. Add a SQL schema entry in `UnifiedDatabaseManager.SCHEMA`.
3. Implement a subclass of `DatabaseRepository`.
4. Instantiate in `UnifiedDatabaseManager.__init__`. 