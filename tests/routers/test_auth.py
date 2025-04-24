import pytest # Import pytest for the marker
from fastapi.testclient import TestClient
from sqlmodel import Session, select # Import select
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from core.config import settings
from core.security import verify_password
from models import User

# Test user data
test_email = "test@example.com"
test_password = "testpassword"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

@pytest.mark.asyncio
async def test_register_user(client: TestClient, session: DbSession): # Add session fixture, mark async
    """Test user registration."""
    response = client.post( # REMOVE await
        "/auth/register",
        json={"email": test_email, "password": test_password},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_email
    assert "id" in data
    assert data["is_active"] is True

    # Verify user is in the database and password is hashed
    if settings.USE_ASYNC_DB:
        user_in_db = await session.get(User, data["id"]) # type: ignore [union-attr]
    else:
        user_in_db = session.get(User, data["id"]) # type: ignore [union-attr]
    assert user_in_db
    assert user_in_db.email == test_email
    assert verify_password(test_password, user_in_db.hashed_password)

@pytest.mark.asyncio
async def test_register_existing_user(client: TestClient): # Mark async
    """Test registering a user with an email that already exists."""
    # First registration
    client.post( # REMOVE await
        "/auth/register",
        json={"email": test_email, "password": test_password},
    )
    # Second registration attempt
    response = client.post( # REMOVE await
        "/auth/register",
        json={"email": test_email, "password": "anotherpassword"},
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_for_access_token(client: TestClient): # Mark async
    """Test user login and token generation."""
    # Register user first
    client.post( # REMOVE await
        "/auth/register",
        json={"email": test_email, "password": test_password},
    )

    # Attempt login
    login_data = {"username": test_email, "password": test_password}
    response = client.post("/auth/token", data=login_data) # REMOVE await

    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: TestClient): # Mark async
    """Test login with incorrect password."""
    client.post( # REMOVE await
        "/auth/register",
        json={"email": test_email, "password": test_password},
    )
    login_data = {"username": test_email, "password": "wrongpassword"}
    response = client.post("/auth/token", data=login_data) # REMOVE await
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_nonexistent_user(client: TestClient): # Mark async
    """Test login with an email that doesn't exist."""
    login_data = {"username": "nosuchuser@example.com", "password": "password"}
    response = client.post("/auth/token", data=login_data) # REMOVE await
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

# TODO: Add tests for the /refresh endpoint
# TODO: Add tests for inactive user login attempt

@pytest.mark.asyncio
async def test_read_users_me(client: TestClient): # Mark async
    """Test fetching the current user's profile."""
    # Register and login to get token
    email = "me@example.com"
    password = "passwordme"
    reg_response = client.post("/auth/register", json={"email": email, "password": password}) # REMOVE await
    assert reg_response.status_code == 201
    user_id = reg_response.json()["id"]

    login_data = {"username": email, "password": password}
    token_response = client.post("/auth/token", data=login_data) # REMOVE await
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch user profile
    me_response = client.get("/auth/users/me", headers=headers) # REMOVE await
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["id"] == user_id
    assert me_data["email"] == email
    assert me_data["is_active"] is True

@pytest.mark.asyncio
async def test_read_users_me_unauthenticated(client: TestClient): # Mark async
    """Test fetching profile without authentication."""
    response = client.get("/auth/users/me") # REMOVE await
    assert response.status_code == 401

# --- Password Change Tests ---

@pytest.mark.asyncio
async def test_update_user_password_success(client: TestClient, session: DbSession): # Mark async, use DbSession
    """Test successfully changing the user's password."""
    email = "changepw@example.com"
    old_password = "oldpassword"
    new_password = "newpassword"

    # Register user
    reg_response = client.post("/auth/register", json={"email": email, "password": old_password}) # REMOVE await
    assert reg_response.status_code == 201
    user_id = reg_response.json()["id"]

    # Login to get token
    login_data = {"username": email, "password": old_password}
    token_response = client.post("/auth/token", data=login_data) # REMOVE await
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Change password
    pw_change_data = {"current_password": old_password, "new_password": new_password}
    pw_change_response = client.put("/auth/users/me/password", headers=headers, json=pw_change_data) # REMOVE await
    assert pw_change_response.status_code == 204

    # Verify password changed in DB
    if settings.USE_ASYNC_DB:
        await session.expire_all() # Use await
        db_user = await session.get(User, user_id) # Use await
    else:
        session.expire_all()
        db_user = session.get(User, user_id) # type: ignore [union-attr]
    assert db_user
    assert verify_password(new_password, db_user.hashed_password)
    assert not verify_password(old_password, db_user.hashed_password) # Old password should fail

    # Verify login with new password works
    new_login_data = {"username": email, "password": new_password}
    new_token_response = client.post("/auth/token", data=new_login_data) # REMOVE await
    assert new_token_response.status_code == 200

    # Verify login with old password fails
    old_login_data = {"username": email, "password": old_password}
    old_token_response = client.post("/auth/token", data=old_login_data) # REMOVE await
    assert old_token_response.status_code == 401

@pytest.mark.asyncio
async def test_update_user_password_wrong_current(client: TestClient): # Mark async
    """Test changing password with incorrect current password."""
    email = "wrongpw@example.com"
    correct_password = "correctpassword"
    new_password = "newpassword"

    # Register user
    client.post("/auth/register", json={"email": email, "password": correct_password}) # REMOVE await

    # Login to get token
    login_data = {"username": email, "password": correct_password}
    token_response = client.post("/auth/token", data=login_data) # REMOVE await
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Attempt password change with wrong current password
    pw_change_data = {"current_password": "incorrect_old_password", "new_password": new_password}
    pw_change_response = client.put("/auth/users/me/password", headers=headers, json=pw_change_data) # REMOVE await
    assert pw_change_response.status_code == 400
    assert "Incorrect current password" in pw_change_response.json()["detail"]

@pytest.mark.asyncio
async def test_update_user_password_unauthenticated(client: TestClient): # Mark async
    """Test changing password without authentication."""
    pw_change_data = {"current_password": "any", "new_password": "any"}
    response = client.put("/auth/users/me/password", json=pw_change_data) # REMOVE await
    assert response.status_code == 401
