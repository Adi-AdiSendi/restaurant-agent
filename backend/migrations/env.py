"""Alembic environment: async engine, URL from app settings."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings
from app.db.base import Base

# Each feature's models module registers its tables on Base.metadata.
from app.memory import models as _memory_models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from app.memory import preference as _preference_model  # noqa: F401  # pyright: ignore[reportUnusedImport]
from app.menu import models as _menu_models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from app.menu import restaurant as _restaurant_model  # noqa: F401  # pyright: ignore[reportUnusedImport]
from app.users import models as _user_models  # noqa: F401  # pyright: ignore[reportUnusedImport]

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
