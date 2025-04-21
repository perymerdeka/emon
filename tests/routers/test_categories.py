import pytest
import pytest_asyncio

from fastapi.testclient import TestClient

from sqlmodel import Session, select # Import select
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from models import Category # Import model for checking DB state
from dto import CategoryType # Import enum
from core.config import settings # Import settings

# --- Test Data ---
user1_email = "user1@example.com"
user1_pw = "pw1"
user2_email = "user2@example.com"
user2_pw = "pw2"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

# --- Fixtures ---
# Use pytest_asyncio.fixture for async fixtures that need client/session
@pytest_asyncio.fixture(scope="module")
async def user1_headers(client: TestClient) -> dict: # Make fixture async
    """Fixture to get auth headers for user1."""
    # Use await for client calls
    await client.post("/auth/register", json={"email": user1_email, "password": user1_pw})
    login_data = {"username": user1_email, "password": user1_pw}
    response = await client.post("/auth/token", data=login_data)
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="module")
async def user2_headers(client: TestClient) -> dict: # Make fixture async
    """Fixture to get auth headers for user2."""
    await client.post("/auth/register", json={"email": user2_email, "password": user2_pw})
    login_data = {"username": user2_email, "password": user2_pw}
    response = await client.post("/auth/token", data=login_data)
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


# --- Tests ---

@pytest.mark.asyncio
async def test_read_categories_unauthenticated(client: TestClient): # Mark async
    """Test accessing categories without authentication fails."""
    response = await client.get("/categories/") # Use await
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_category_unauthenticated(client: TestClient): # Mark async
    """Test creating category without authentication fails."""
    response = await client.post("/categories/", json={"name": "Salary", "type": "income"}) # Use await
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_and_read_categories(client: TestClient, user1_headers: dict, session: DbSession): # Mark async, use DbSession
    """Test creating categories and reading them back for the correct user."""
    # User 1 creates categories
    cat1_data = {"name": "Salary", "type": CategoryType.INCOME}
    response1 = await client.post("/categories/", headers=user1_headers, json=cat1_data) # Use await
    assert response1.status_code == 201
    cat1 = response1.json()
    assert cat1["name"] == cat1_data["name"]
    assert cat1["type"] == cat1_data["type"]

    cat2_data = {"name": "Groceries", "type": CategoryType.EXPENSE}
    response2 = await client.post("/categories/", headers=user1_headers, json=cat2_data) # Use await
    assert response2.status_code == 201
    cat2 = response2.json()
    assert cat2["name"] == cat2_data["name"]
    assert cat2["type"] == cat2_data["type"]

    # Read categories for User 1
    response_read = await client.get("/categories/", headers=user1_headers) # Use await
    assert response_read.status_code == 200
    categories = response_read.json()
    assert len(categories) == 2
    # Check if returned categories match created ones (order might vary)
    returned_names = {c["name"] for c in categories}
    assert returned_names == {"Salary", "Groceries"}

@pytest.mark.asyncio
async def test_create_duplicate_category_for_user(client: TestClient, user1_headers: dict): # Mark async
    """Test creating a category with a name that already exists for the user."""
    cat_data = {"name": "Rent", "type": CategoryType.EXPENSE}
    # Create first time
    response1 = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response1.status_code == 201
    # Attempt to create again
    response2 = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response2.status_code == 400
    assert "already exists for this user" in response2.json()["detail"]

@pytest.mark.asyncio
async def test_create_same_category_different_users(client: TestClient, user1_headers: dict, user2_headers: dict): # Mark async
    """Test that different users can have categories with the same name."""
    cat_data = {"name": "Utilities", "type": CategoryType.EXPENSE}
    # User 1 creates
    response1 = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response1.status_code == 201
    # User 2 creates
    response2 = await client.post("/categories/", headers=user2_headers, json=cat_data) # Use await
    assert response2.status_code == 201 # Should succeed for user 2

@pytest.mark.asyncio
async def test_read_category_by_id(client: TestClient, user1_headers: dict): # Mark async
    """Test reading a specific category by its ID."""
    cat_data = {"name": "Transport", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    response_read = await client.get(f"/categories/{created_cat_id}", headers=user1_headers) # Use await
    assert response_read.status_code == 200
    read_cat = response_read.json()
    assert read_cat["id"] == created_cat_id
    assert read_cat["name"] == cat_data["name"]

@pytest.mark.asyncio
async def test_read_category_by_id_not_found(client: TestClient, user1_headers: dict): # Mark async
    """Test reading a non-existent category ID."""
    response = await client.get("/categories/99999", headers=user1_headers) # Use await
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_read_category_by_id_wrong_user(client: TestClient, user1_headers: dict, user2_headers: dict): # Mark async
    """Test that user 2 cannot read user 1's category."""
    cat_data = {"name": "User1 Cat", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    # User 2 tries to read User 1's category
    response_read = await client.get(f"/categories/{created_cat_id}", headers=user2_headers) # Use await
    assert response_read.status_code == 404 # Should be not found for user 2

@pytest.mark.asyncio
async def test_update_category(client: TestClient, user1_headers: dict, session: DbSession): # Mark async, use DbSession
    """Test updating a category."""
    cat_data = {"name": "Entertainment", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    update_data = {"name": "Fun Money", "type": CategoryType.EXPENSE}
    response_update = await client.put(f"/categories/{created_cat_id}", headers=user1_headers, json=update_data) # Use await
    assert response_update.status_code == 200
    updated_cat = response_update.json()
    assert updated_cat["id"] == created_cat_id
    assert updated_cat["name"] == update_data["name"]

    # Verify change in DB
    if settings.USE_ASYNC_DB:
        db_cat = await session.get(Category, created_cat_id) # type: ignore [union-attr]
    else:
        db_cat = session.get(Category, created_cat_id) # type: ignore [union-attr]
    assert db_cat
    assert db_cat.name == update_data["name"]

@pytest.mark.asyncio
async def test_update_category_wrong_user(client: TestClient, user1_headers: dict, user2_headers: dict): # Mark async
    """Test that user 2 cannot update user 1's category."""
    cat_data = {"name": "User1 Update Test", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    update_data = {"name": "User2 Tries Update", "type": CategoryType.EXPENSE}
    response_update = await client.put(f"/categories/{created_cat_id}", headers=user2_headers, json=update_data) # Use await
    assert response_update.status_code == 404 # Should not find it for user 2

@pytest.mark.asyncio
async def test_update_category_name_conflict(client: TestClient, user1_headers: dict): # Mark async
    """Test updating a category name to one that already exists for the user."""
    cat1_data = {"name": "Food", "type": CategoryType.EXPENSE}
    cat2_data = {"name": "Dining Out", "type": CategoryType.EXPENSE}
    resp1 = await client.post("/categories/", headers=user1_headers, json=cat1_data) # Use await
    resp2 = await client.post("/categories/", headers=user1_headers, json=cat2_data) # Use await
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    cat2_id = resp2.json()["id"]

    # Try to update cat2's name to "Food" (which is cat1's name)
    update_data = {"name": "Food", "type": CategoryType.EXPENSE}
    response_update = await client.put(f"/categories/{cat2_id}", headers=user1_headers, json=update_data) # Use await
    assert response_update.status_code == 400
    assert "already exists for this user" in response_update.json()["detail"]

@pytest.mark.asyncio
async def test_delete_category(client: TestClient, user1_headers: dict, session: DbSession): # Mark async, use DbSession
    """Test deleting a category."""
    cat_data = {"name": "To Delete", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    # Verify it exists
    if settings.USE_ASYNC_DB:
        db_cat_before = await session.get(Category, created_cat_id) # type: ignore [union-attr]
    else:
        db_cat_before = session.get(Category, created_cat_id) # type: ignore [union-attr]
    assert db_cat_before

    # Delete it
    response_delete = await client.delete(f"/categories/{created_cat_id}", headers=user1_headers) # Use await
    assert response_delete.status_code == 204

    # Verify it's gone from DB
    if settings.USE_ASYNC_DB:
        await session.expire_all() # Use await
        db_cat_after = await session.get(Category, created_cat_id) # type: ignore [union-attr]
    else:
        session.expire_all()
        db_cat_after = session.get(Category, created_cat_id) # type: ignore [union-attr]
    assert db_cat_after is None

    # Verify reading it again gives 404
    response_read = await client.get(f"/categories/{created_cat_id}", headers=user1_headers) # Use await
    assert response_read.status_code == 404

@pytest.mark.asyncio
async def test_delete_category_wrong_user(client: TestClient, user1_headers: dict, user2_headers: dict): # Mark async
    """Test that user 2 cannot delete user 1's category."""
    cat_data = {"name": "User1 Delete Test", "type": CategoryType.EXPENSE}
    response_create = await client.post("/categories/", headers=user1_headers, json=cat_data) # Use await
    assert response_create.status_code == 201
    created_cat_id = response_create.json()["id"]

    # User 2 tries to delete
    response_delete = await client.delete(f"/categories/{created_cat_id}", headers=user2_headers) # Use await
    assert response_delete.status_code == 404 # Should not find it for user 2
