from sqlmodel import SQLModel, Session, create_engine
# Import async session from sqlmodel, async engine from sqlalchemy
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator, Union, Any

# Import settings and the derived SYNC_DATABASE_URL
from core.config import settings, SYNC_DATABASE_URL
import models # noqa

# --- Engine Creation ---
# Create sync engine (always needed for Alembic, used by app if USE_ASYNC_DB=False)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=settings.DEBUG if not settings.USE_ASYNC_DB else False)

# Create async engine only if USE_ASYNC_DB is True
async_engine: AsyncEngine | None = None
if settings.USE_ASYNC_DB:
    async_engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    print("Initialized ASYNC database engine.")
else:
    print("Initialized SYNC database engine.")


# --- Session Dependencies ---
# Sync Session Dependency
def get_sync_session() -> Generator[Session, None, None]:
    # print("DEBUG: Getting SYNC session") # Debug print
    with Session(sync_engine) as session:
        yield session

# Async Session Dependency
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    if not async_engine:
         raise RuntimeError("Async engine not initialized. Check USE_ASYNC_DB setting and DATABASE_URL.")
    # print("DEBUG: Getting ASYNC session") # Debug print
    # Use AsyncSession directly as a context manager
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        yield session

# --- Session Scopes ---
# Sync Session Scope
@contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    session = Session(sync_engine)
    # print("DEBUG: Entering SYNC session scope") # Debug print
    try:
        yield session
        session.commit()
    except Exception:
        print("Sync session rollback due to exception")
        session.rollback()
        raise
    finally:
        # print("DEBUG: Closing SYNC session scope") # Debug print
        session.close()

# Async Session Scope
@asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    if not async_engine:
         raise RuntimeError("Async engine not initialized. Check USE_ASYNC_DB setting and DATABASE_URL.")
    session = AsyncSession(async_engine, expire_on_commit=False)
    # print("DEBUG: Entering ASYNC session scope") # Debug print
    try:
        yield session
        await session.commit()
    except Exception:
        print("Async session rollback due to exception")
        await session.rollback()
        raise
    finally:
        # print("DEBUG: Closing ASYNC session scope") # Debug print
        await session.close()

# --- Unified Dependency (Attempt) ---
# This dependency tries to yield the correct session type based on settings.
# Type hinting is tricky; using Any for now.
# Note: FastAPI handles injecting sync dependencies into async endpoints if needed,
# but explicitly yielding the correct type might be cleaner if feasible.
# However, the dependency function itself MUST be async if it *might* yield an async session.
async def get_db_session() -> Any: # Return type Any due to conditional yield
    """Dependency that returns either an AsyncSession or sync Session based on settings."""
    if settings.USE_ASYNC_DB:
        return AsyncSession(async_engine, expire_on_commit=False)
    else:
        return Session(sync_engine)
