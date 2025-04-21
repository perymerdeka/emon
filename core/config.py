import os
from typing import Any, Dict # Import Any, Dict
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator # Import model_validator

class Settings(BaseSettings):
    DEBUG: bool = True

    # --- Database URL ---
    # Define the database connection string via DATABASE_URL environment variable.
    # Examples:
    # SQLite (SYNC):   sqlite:///./database.db
    # SQLite (ASYNC):  sqlite+aiosqlite:///./database.db
    # PostgreSQL (SYNC): postgresql+psycopg2://user:password@host:port/dbname
    # PostgreSQL (ASYNC): postgresql+asyncpg://user:password@host:port/dbname
    # MySQL (SYNC):    mysql+mysqlclient://user:password@host:port/dbname
    # MySQL (ASYNC):   mysql+aiomysql://user:password@host:port/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db") # Default to ASYNC SQLite

    # --- Async DB Setting ---
    # Explicitly control async mode via USE_ASYNC_DB environment variable (True/False/"1"/"0")
    # Default value will be set based on DATABASE_URL in the validator below.
    USE_ASYNC_DB: bool | None = Field(default=None) # Allow None initially

    # --- JWT Settings ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7") # Placeholder key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        # Optional: Load .env file if you prefer using python-dotenv
        # env_file = ".env"
        env_file_encoding = 'utf-8'
        # Allow extra fields if needed, though BaseSettings usually handles this
        # extra = 'ignore'

    @model_validator(mode='after')
    def set_async_db_default(self) -> 'Settings':
        """Set default for USE_ASYNC_DB based on DATABASE_URL if not set explicitly."""
        if self.USE_ASYNC_DB is None: # Only set default if not provided via env var
            is_async_url = self.DATABASE_URL.startswith(("sqlite+aiosqlite", "postgresql+asyncpg", "mysql+aiomysql"))
            self.USE_ASYNC_DB = is_async_url
            print(f"DEBUG: USE_ASYNC_DB defaulted to {self.USE_ASYNC_DB} based on DATABASE_URL")
        # Ensure USE_ASYNC_DB is bool after validation/defaulting
        if not isinstance(self.USE_ASYNC_DB, bool):
             # Attempt conversion for env vars like "True", "1", "False", "0"
             if isinstance(self.USE_ASYNC_DB, str):
                 self.USE_ASYNC_DB = self.USE_ASYNC_DB.lower() in ('true', '1', 't')
             else: # Fallback or raise error if conversion fails
                 self.USE_ASYNC_DB = False # Defaulting to False on invalid type
        return self

settings = Settings()

# Helper to get the appropriate sync URL for Alembic/Sync Engine
def get_sync_database_url(db_url: str) -> str:
    if db_url.startswith("sqlite+aiosqlite"):
        return db_url.replace('+aiosqlite', '', 1)
    elif db_url.startswith("postgresql+asyncpg"):
        # Assuming psycopg2 for sync counterpart
        return db_url.replace('+asyncpg', '+psycopg2', 1)
    elif db_url.startswith("mysql+aiomysql"):
        # Assuming PyMySQL for sync counterpart
        return db_url.replace('+aiomysql', '+pymysql', 1)
    # If it's already a sync URL or unknown, return as is
    return db_url

SYNC_DATABASE_URL = get_sync_database_url(settings.DATABASE_URL)

# Print effective settings for debugging during startup
print(f"--- Configuration ---")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"USE_ASYNC_DB: {settings.USE_ASYNC_DB}")
print(f"SYNC_DATABASE_URL (for Alembic/Sync Mode): {SYNC_DATABASE_URL}")
print(f"---------------------")
