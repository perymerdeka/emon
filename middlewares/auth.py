from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.types import RequestResponseFunction # Problematic import
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Optional, Callable, Awaitable, Union, Any # Import Callable and Awaitable, Union, Any

from core.security import decode_token # Use renamed function
# Import both session scopes and settings
from core.db import get_db_session, sync_session_scope, async_session_scope
from core.config import settings
from models import User # Need User model
from dto import TokenPayload # Need TokenPayload DTO
# Import session types for type hinting if needed inside the function
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

# This scheme can be used by dependencies later to extract the token easily
# Update tokenUrl to reflect the new router path (no /api/v1 prefix)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class AuthMiddleware(BaseHTTPMiddleware):
    # Use a more generic type hint for call_next
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Define paths that should bypass authentication
        # Update paths to remove /api/v1 prefix
        excluded_paths = [
            "/docs",
            "/openapi.json",
            "/auth/token", # Login endpoint
            "/auth/register", # Registration endpoint
            "/" # Root path
        ]

        # Allow requests to excluded paths without authentication
        # Keep the startswith check for /docs and /openapi.json subpaths
        if request.url.path in excluded_paths or any(request.url.path.startswith(path) for path in ["/docs", "/openapi.json"]):
             return await call_next(request)

        # Attempt to extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        token: Optional[str] = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[1]

        user: Optional[User] = None
        if token:
            # Use the generic decode_token function here
            payload = decode_token(token)
            if payload:
                token_data = TokenPayload(**payload)
                if token_data.sub: # Check if subject (user identifier) exists
                    try:
                        user_id = int(token_data.sub) # Assuming subject is user ID
                        # Use the appropriate session scope to fetch the user
                        if settings.USE_ASYNC_DB:
                            async with async_session_scope() as session:
                                user = await session.get(User, user_id)
                                if user and not user.is_active:
                                    user = None # Treat inactive users as unauthenticated
                                request.state.session = session # Attach the session to the request state
                        else:
                            with sync_session_scope() as session:
                                user = session.get(User, user_id)
                                if user and not user.is_active:
                                    user = None # Treat inactive users as unauthenticated
                                request.state.session = session # Attach the session to the request state
                    except (ValueError, TypeError):
                        print(f"Invalid user ID in token subject: {token_data.sub}")
                        user = None # Invalid user ID format
                    except Exception as e:
                        print(f"Error fetching user from DB in middleware: {e}")
                        user = None # Handle potential DB errors

        # Attach the user ID (or None) to the request state
        # Dependencies can later access this via request.state.user_id
        request.state.user_id = user_id if user else None

        # Proceed with the request
        response = await call_next(request)
        return response

# --- Dependency for getting current user ---

async def get_current_user(request: Request, session:  Any = Depends(get_db_session)) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    Relies on the AuthMiddleware having attached the user ID to request.state.
    Raises HTTPException if user is not authenticated or not active.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if settings.USE_ASYNC_DB:
        user = await session.get(User, user_id)
    else:
        user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Redundant check if middleware handles inactive users, but good for safety
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures the user fetched by get_current_user is active.
    This is slightly redundant if get_current_user already checks activity,
    but provides an explicit dependency name for clarity in endpoints.
    """
    # The active check is already performed in get_current_user or middleware
    # This dependency mainly serves as a clear way to require an active user.
    return current_user
