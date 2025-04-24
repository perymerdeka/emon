import pytest
import pytest_asyncio # Import the asyncio marker/fixtures
from typing import Generator, AsyncGenerator, Any, Union # Add AsyncGenerator, Union
import pytest
import pytest_asyncio # Import the asyncio marker/fixtures
from typing import Generator, AsyncGenerator, Any, Union # Add AsyncGenerator, Union
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession # Keep AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine # Import AsyncEngine from sqlalchemy
from sqlmodel.pool import StaticPool

# Import the app creation function and settings
from core import create_app
from core.config import settings
# Import the unified dependency and specific session types/engines
from core.db import get_db_session, sync_engine as app_sync_engine, async_engine as app_async_engine, AsyncSession, Session

# Import all models to ensure they are registered with SQLModel metadata
import models # noqa


# --- Test Database Setup ---

# Use in-memory SQLite for testing, create both sync and async engines
# Use StaticPool for predictable connection handling in tests
# IMPORTANT: Use different memory locations for sync/async test DBs
# to avoid potential conflicts if tests run in parallel or state leaks.
test_sync_db_url = "sqlite:///file:test_sync.db?mode=memory&cache=shared"
test_async_db_url = "sqlite+aiosqlite:///file:test_async.db?mode=memory&cache=shared"

# Create engines specifically for testing
test_sync_engine = create_engine(
    test_sync_db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
test_async_engine = create_async_engine(
    test_async_db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool
)

# Fixture to create/drop tables for each test function
# Needs to be async if using async engine
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """Creates database tables before each test function using the appropriate engine."""
    if settings.USE_ASYNC_DB:
        async with test_async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        yield
        async with test_async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    else:
        # Keep original sync logic if not using async DB
        SQLModel.metadata.create_all(test_sync_engine)
        yield
        SQLModel.metadata.drop_all(test_sync_engine)

# Fixture to provide the correct session type based on settings
# Use pytest_asyncio.fixture for async fixtures
@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[Union[Session, AsyncSession], None]:
    """Provides a test database session (sync or async based on settings)."""
    if settings.USE_ASYNC_DB:
        # print("DEBUG: Providing ASYNC test session") # Debug print
        async with AsyncSession(test_async_engine, expire_on_commit=False) as async_session:
            yield async_session
            # Rollback changes after test? Depends on desired test isolation.
            # await async_session.rollback() # Optional: Rollback after each test
    else:
        # print("DEBUG: Providing SYNC test session") # Debug print
        with Session(test_sync_engine) as sync_session:
            yield sync_session
            # Rollback changes after test?
            # sync_session.rollback() # Optional: Rollback after each test


# Fixture to create the FastAPI app instance for testing
# Needs to be function-scoped if session override depends on function-scoped session
@pytest.fixture(scope="function")
def app(session: Union[Session, AsyncSession]) -> FastAPI:
    """Creates a FastAPI app instance with test DB session override."""
    app_ = create_app()

    # Override the get_db_session dependency
    async def get_session_override() -> AsyncGenerator[Union[Session, AsyncSession], None]:
        yield session
        # No need to close/rollback here, handled by the session fixture

    app_.dependency_overrides[get_db_session] = get_session_override
    return app_

# Fixture to provide an HTTP test client
# Needs to be function-scoped because the app fixture is function-scoped
# Make it depend on setup_test_database to ensure tables exist first
@pytest.fixture(scope="function")
def client(app: FastAPI, setup_test_database: Any) -> Generator[TestClient, None, None]:
    """Provides a FastAPI TestClient."""
    with TestClient(app) as client_:
        yield client_

# --- Optional: Fixtures for Authentication ---
# You might add fixtures here later to create test users and get tokens easily
