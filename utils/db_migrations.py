import os
import asyncio
import asyncpg
import logging
import yaml
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.migrations_dir = Path('migrations')
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish database connection"""
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("Connected to database for migrations")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            logger.info("Closed database connection")

    async def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        async with self.pool.acquire() as conn:
            # Create migrations table if it doesn't exist
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Get applied migrations
            rows = await conn.fetch('SELECT version FROM migrations ORDER BY id')
            return [row['version'] for row in rows]

    async def apply_migration(self, version: str, sql: str) -> None:
        """Apply a single migration"""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                logger.info(f"Applying migration {version}")
                await conn.execute(sql)
                await conn.execute(
                    'INSERT INTO migrations (version) VALUES ($1)',
                    version
                )
                logger.info(f"Successfully applied migration {version}")

    def get_migration_files(self) -> List[tuple[str, str]]:
        """Get all migration files sorted by version"""
        migrations = []
        for file in sorted(self.migrations_dir.glob('*.sql')):
            version = file.stem
            with open(file, 'r') as f:
                sql = f.read()
            migrations.append((version, sql))
        return migrations

    async def run_migrations(self) -> None:
        """Run all pending migrations"""
        try:
            await self.connect()
            
            applied = await self.get_applied_migrations()
            pending = [
                (version, sql) 
                for version, sql in self.get_migration_files()
                if version not in applied
            ]

            if not pending:
                logger.info("No pending migrations")
                return

            for version, sql in pending:
                try:
                    await self.apply_migration(version, sql)
                except Exception as e:
                    logger.error(f"Failed to apply migration {version}: {e}", exc_info=True)
                    raise

            logger.info("All migrations completed successfully")

        finally:
            await self.close()

async def run_migrations(config_path: str = 'config.yaml') -> None:
    """Run database migrations from config"""
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    db_url = config['database']['url']
    migrator = DatabaseMigrator(db_url)
    await migrator.run_migrations()

if __name__ == "__main__":
    asyncio.run(run_migrations()) 