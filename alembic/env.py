from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from alembic.operations import ops
import sqlalchemy as sa
import sqlmodel

# Fungsi untuk mengubah tipe SQLModel ke SQLAlchemy standar
def process_revision_directives(context, revision, directives):
    for directive in directives:
        if isinstance(directive, ops.MigrationScript):
            for op in directive.upgrade_ops.ops:
                if isinstance(op, ops.CreateTableOp):
                    for col in op.columns:
                        if hasattr(col.type, '__origin__') and col.type.__origin__ == sqlmodel.sql.sqltypes.AutoString:
                            col.type = sa.String()
                elif isinstance(op, ops.AlterColumnOp):
                    if hasattr(op.modify_type, '__origin__') and op.modify_type.__origin__ == sqlmodel.sql.sqltypes.AutoString:
                        op.modify_type = sa.String()

# Tambahkan path project ke sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import settings dan models
from core.config import SYNC_DATABASE_URL
from sqlmodel import SQLModel
from models import *  # Import semua model untuk autogenerate

# Gunakan SQLModel.metadata sebagai target_metadata
Base = SQLModel

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Gunakan SYNC_DATABASE_URL dari core.config
config.set_main_option('sqlalchemy.url', SYNC_DATABASE_URL)

# Set target_metadata ke metadata dari SQLModel
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
