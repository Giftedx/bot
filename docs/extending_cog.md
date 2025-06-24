# Extending a Cog

Follow these steps to add a new feature cog:

1. **Create the Cog file** under `src/cogs/<your_feature>_commands.py`.
2. **Inherit from `CogBase`** to receive unified dependencies.
3. **Register commands** using `discord.ext.commands` decorators.
4. **Use helpers**:
   * `self.database` – repositories & helpers
   * `self.config` – config sections via `self.config.get("cogs.your.feature")`
   * `self.error_manager.retry_on_error()` – decorator for resiliency
   * `await self.log_command_usage(ctx, "command_name")` for analytics
5. **Add unit tests** in `tests/` using `pytest` & `pytest-asyncio`.
6. **Update documentation** by adding a section/page. 