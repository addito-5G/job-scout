"""Alembic environment: metadata from ORM, URL from config."""

from __future__ import annotations

from logging.config import fileConfig

import config
from alembic import context
from db.engine import resolve_database_url
from db.tables import Base
from sqlalchemy import engine_from_config, pool

target_metadata = Base.metadata

alembic_config = context.config

if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)


def _database_url() -> str:
    return resolve_database_url(config.DATABASE_URL)


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = alembic_config.get_section(alembic_config.config_ini_section, {})
    url = _database_url()
    configuration["sqlalchemy.url"] = url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
