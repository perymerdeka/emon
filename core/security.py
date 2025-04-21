from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt # Import PyJWT
from passlib.context import CryptContext

from core.config import settings

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Token Handling using PyJWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token using PyJWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default expiration time from settings
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)}) # Add issued at time
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Creates a JWT refresh token using PyJWT with longer expiry."""
    to_encode = data.copy()
    # Use longer expiry from settings for refresh token
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    # Add a claim to distinguish refresh tokens if needed, e.g., "type": "refresh"
    # to_encode.update({"type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# Rename decode_access_token to decode_token as it works for both
def decode_token(token: str) -> Optional[dict]:
    """
    Decodes a JWT token (access or refresh) using PyJWT.
    Returns payload dictionary or None if token is invalid or expired.
    """
    try:
        # PyJWT handles expiration check during decode
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        # Optionally, you could add checks here for specific claims if needed
        # e.g., check if 'sub' (subject/user id) exists
        if "sub" not in payload:
             print("Token missing 'sub' claim")
             return None
        return payload
    except jwt.ExpiredSignatureError:
        # Handle expired token specifically if needed, or just return None
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        # Handle other invalid token errors
        print(f"Invalid token error: {e}")
        return None
    except Exception as e:
        # Catch any other unexpected errors during decoding
        print(f"An unexpected error occurred during token decoding: {e}")
        return None
