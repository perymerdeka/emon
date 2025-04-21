from fastapi import APIRouter, Depends, HTTPException, status, Request # Import Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

# Import the limiter instance
from core.limiter import limiter
# Import the oauth2_scheme used in the refresh endpoint dependency
from middlewares.auth import get_current_active_user, oauth2_scheme
from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union, Any # For type hints

# Import unified session dependency and settings
from core.db import get_db_session
from core.config import settings
# Import security functions
from core.security import (
    create_access_token, create_refresh_token, decode_token,
    get_password_hash, verify_password
)
from models import User
# Import necessary DTOs including the new password update one
from dto import UserCreate, UserRead, Token, UserPasswordUpdate
# get_current_active_user is already imported via middlewares.auth above

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

# Apply rate limit to registration endpoint
# Apply rate limit to registration endpoint
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute") # Example: Limit to 10 registrations per minute per IP
async def register_user( # Changed to async def
    request: Request, # Need request object for limiter
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    user_in: UserCreate
):
    """
    Register a new user.
    """
    # Check if user already exists
    statement = select(User).where(User.email == user_in.email)
    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        existing_user = results.first()
    else:
        existing_user = session.exec(statement).first() # type: ignore [union-attr]

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    # Hash the password before saving
    hashed_password = get_password_hash(user_in.password)
    # Create User instance, excluding the plain password
    db_user = User(email=user_in.email, hashed_password=hashed_password, is_active=True)

    session.add(db_user)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_user) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_user) # type: ignore [union-attr]

    return db_user


# Apply rate limit to login endpoint
@router.post("/token", response_model=Token)
@limiter.limit("5/minute") # Example: Limit to 5 login attempts per minute per IP
async def login_for_access_token(
    request: Request, # Need request object for limiter
    session: DbSession = Depends(get_db_session), # Use unified dependency
    form_data: OAuth2PasswordRequestForm = Depends() # Inject form data (username/password)
):
    """
    Authenticate user and return JWT token.
    Uses OAuth2PasswordRequestForm which expects 'username' and 'password' fields.
    We'll use the email as the username here.
    """
    statement = select(User).where(User.email == form_data.username)
    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        user = results.first()
    else:
        user = session.exec(statement).first() # type: ignore [union-attr]

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    # Create access and refresh tokens
    # The 'sub' (subject) of the token should be the user identifier (e.g., user.id)
    subject = str(user.id)
    access_token = create_access_token(data={"sub": subject})
    refresh_token = create_refresh_token(data={"sub": subject}) # Refresh token also contains user ID
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    # Expect refresh token in the Authorization header like an access token
    refresh_token: str = Depends(oauth2_scheme)
):
    """
    Exchange a valid refresh token for a new access token and the same refresh token.
    """
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Optional: Add check if refresh token has specific claim like "type": "refresh"
    # if payload.get("type") != "refresh":
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload (missing sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Need to fetch user from DB using session
        user_id_int = int(user_id)
        if settings.USE_ASYNC_DB:
            user = await session.get(User, user_id_int) # type: ignore [union-attr]
        else:
            user = session.get(User, user_id_int) # type: ignore [union-attr]
    except (ValueError, TypeError):
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID in token")

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue a new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})

    # Return new access token and the *original* refresh token
    # Note: Refresh token rotation (issuing a new refresh token here) is more secure
    # but adds complexity (client needs to store the new refresh token).
    # For simplicity, we return the original one.
    return Token(access_token=new_access_token, refresh_token=refresh_token, token_type="bearer")


# Endpoint to get current user's information
@router.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Fetch the current logged-in user's profile information.
    """
    # The dependency already fetches and validates the user
    return current_user

# Endpoint to change current user's password
@router.put("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    password_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the current logged-in user's password.
    """
    # Verify the current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Hash the new password
    new_hashed_password = get_password_hash(password_update.new_password)

    # Update the user's password in the database
    current_user.hashed_password = new_hashed_password
    session.add(current_user)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]

    # No response body needed for 204
