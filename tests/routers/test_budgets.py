import pytest
import pytest_asyncio # Import asyncio marker
from fastapi.testclient import TestClient
from sqlmodel import Session, select # Keep sync Session for type hint if needed
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from datetime import date

from models import Budget, Category # Import models
from dto import CategoryType # Import enum
from core.config import settings # Import settings

# Use fixtures defined in conftest.py
# Need user headers and potentially categories created

# --- Test Data ---
user1_email_bud = "user1_bud@example.com"
user1_pw_bud = "pw1_bud"
user2_email_bud = "user2_bud@example.com"
user2_pw_bud = "pw2_bud"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

# --- Fixtures ---
@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user1_bud_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user1 specific to budget tests."""
    await client.post("/auth/register", json={"email": user1_email_bud, "password": user1_pw_bud}) # Use await
    login_data = {"username": user1_email_bud, "password": user1_pw_bud}
    response = await client.post("/auth/token", data=login_data) # Use await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user2_bud_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user2 specific to budget tests."""
    await client.post("/auth/register", json={"email": user2_email_bud, "password": user2_pw_bud}) # Use await
    login_data = {"username": user2_email_bud, "password": user2_pw_bud}
    response = await client.post("/auth/token", data=login_data) # Use await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="function") # Change to async fixture
async def user1_bud_categories(client: TestClient, user1_bud_headers: dict) -> dict: # Make async
    """Fixture to create some categories for user1 for budget tests."""
    expense_data = {"name": "Groceries_B", "type": CategoryType.EXPENSE}
    resp_expense = await client.post("/categories/", headers=user1_bud_headers, json=expense_data) # Use await
    assert resp_expense.status_code == 201
    return {"expense_id": resp_expense.json()["id"]}

# --- Tests ---

@pytest.mark.asyncio
async def test_create_budget_unauthenticated(client: TestClient): # Mark async
    """Test creating budget without authentication fails."""
    budget_data = {"year": 2024, "month": 1, "amount": 500}
    response = await client.post("/budgets/", json=budget_data) # Use await
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_overall_budget(client: TestClient, user1_bud_headers: dict): # Mark async
    """Test creating a valid overall monthly budget."""
    budget_data = {"year": 2024, "month": 5, "amount": 1000.0}
    response = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response.status_code == 201
    data = response.json()
    assert data["year"] == budget_data["year"]
    assert data["month"] == budget_data["month"]
    assert data["amount"] == budget_data["amount"]
    assert data["category_id"] is None
    assert "id" in data

@pytest.mark.asyncio
async def test_create_category_budget(client: TestClient, user1_bud_headers: dict, user1_bud_categories: dict): # Mark async
    """Test creating a valid category-specific monthly budget."""
    budget_data = {
        "year": 2024,
        "month": 6,
        "amount": 250.0,
        "category_id": user1_bud_categories["expense_id"]
    }
    response = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response.status_code == 201
    data = response.json()
    assert data["year"] == budget_data["year"]
    assert data["month"] == budget_data["month"]
    assert data["amount"] == budget_data["amount"]
    assert data["category_id"] == budget_data["category_id"]

@pytest.mark.asyncio
async def test_create_budget_duplicate(client: TestClient, user1_bud_headers: dict, user1_bud_categories: dict): # Mark async
    """Test creating a duplicate budget (same user, year, month, category)."""
    budget_data = {"year": 2024, "month": 7, "amount": 100, "category_id": user1_bud_categories["expense_id"]}
    # Create first time
    response1 = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response1.status_code == 201
    # Attempt to create again
    response2 = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

    # Test duplicate overall budget
    budget_data_overall = {"year": 2024, "month": 8, "amount": 500}
    response3 = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data_overall) # Use await
    assert response3.status_code == 201
    response4 = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data_overall) # Use await
    assert response4.status_code == 400
    assert "already exists" in response4.json()["detail"]

@pytest.mark.asyncio
async def test_create_budget_invalid_category(client: TestClient, user1_bud_headers: dict): # Mark async
    """Test creating budget with non-existent category."""
    budget_data = {"year": 2024, "month": 9, "amount": 50, "category_id": 99999}
    response = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_budget_wrong_user_category( # Mark async
    client: TestClient, user1_bud_headers: dict, user2_bud_headers: dict
):
    """Test creating budget using another user's category."""
    # User 2 creates category
    cat_data = {"name": "User2 Budget Cat", "type": CategoryType.EXPENSE}
    resp_cat = await client.post("/categories/", headers=user2_bud_headers, json=cat_data) # Use await
    user2_cat_id = resp_cat.json()["id"]

    # User 1 tries to create budget with User 2's category
    budget_data = {"year": 2024, "month": 10, "amount": 100, "category_id": user2_cat_id}
    response = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    assert response.status_code == 404 # Category not found for user 1

@pytest.mark.asyncio
async def test_read_budgets(client: TestClient, user1_bud_headers: dict, user1_bud_categories: dict): # Mark async
    """Test reading budgets with filtering."""
    # Create budgets for different periods/categories
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2024, "month": 1, "amount": 1000}) # Use await
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2024, "month": 1, "amount": 200, "category_id": user1_bud_categories["expense_id"]}) # Use await
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2024, "month": 2, "amount": 1100}) # Use await
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2025, "month": 1, "amount": 1200}) # Use await

    # Read all for user
    resp_all = await client.get("/budgets/", headers=user1_bud_headers) # Use await
    assert resp_all.status_code == 200
    assert len(resp_all.json()) == 4

    # Filter by year
    resp_year = await client.get("/budgets/?year=2024", headers=user1_bud_headers) # Use await
    assert resp_year.status_code == 200
    assert len(resp_year.json()) == 3

    # Filter by year and month
    resp_ym = await client.get("/budgets/?year=2024&month=1", headers=user1_bud_headers) # Use await
    assert resp_ym.status_code == 200
    assert len(resp_ym.json()) == 2

    # Filter by category
    resp_cat = await client.get(f"/budgets/?category_id={user1_bud_categories['expense_id']}", headers=user1_bud_headers) # Use await
    assert resp_cat.status_code == 200
    assert len(resp_cat.json()) == 1
    assert resp_cat.json()[0]["amount"] == 200

@pytest.mark.asyncio
async def test_read_budgets_wrong_user( # Mark async
    client: TestClient, user1_bud_headers: dict, user2_bud_headers: dict
):
    """Test reading budgets only returns budgets for the authenticated user."""
    # User 1 creates budget
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2024, "month": 3, "amount": 300}) # Use await
    # User 2 reads budgets
    resp_u2 = await client.get("/budgets/", headers=user2_bud_headers) # Use await
    assert resp_u2.status_code == 200
    assert len(resp_u2.json()) == 0 # Should see none of user 1's budgets

@pytest.mark.asyncio
async def test_read_budget_by_id(client: TestClient, user1_bud_headers: dict): # Mark async
    """Test reading a specific budget by ID."""
    budget_data = {"year": 2025, "month": 1, "amount": 1500}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    resp_read = await client.get(f"/budgets/{budget_id}", headers=user1_bud_headers) # Use await
    assert resp_read.status_code == 200
    assert resp_read.json()["id"] == budget_id
    assert resp_read.json()["amount"] == 1500

@pytest.mark.asyncio
async def test_read_budget_by_id_wrong_user(client: TestClient, user1_bud_headers: dict, user2_bud_headers: dict): # Mark async
    """Test reading another user's budget by ID fails."""
    budget_data = {"year": 2025, "month": 2, "amount": 500}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    resp_read = await client.get(f"/budgets/{budget_id}", headers=user2_bud_headers) # Use await
    assert resp_read.status_code == 404

@pytest.mark.asyncio
async def test_update_budget(client: TestClient, user1_bud_headers: dict, user1_bud_categories: dict, session: DbSession): # Mark async, use DbSession
    """Test updating a budget's amount and category."""
    # Create initial overall budget
    budget_data = {"year": 2025, "month": 3, "amount": 800}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    # Update amount and add category
    update_data = {
        "year": 2025,
        "month": 3,
        "amount": 850.50,
        "category_id": user1_bud_categories["expense_id"]
    }
    resp_update = await client.put(f"/budgets/{budget_id}", headers=user1_bud_headers, json=update_data) # Use await
    assert resp_update.status_code == 200
    updated_data = resp_update.json()
    assert updated_data["amount"] == 850.50
    assert updated_data["category_id"] == user1_bud_categories["expense_id"]

    # Verify DB
    if settings.USE_ASYNC_DB:
        db_budget = await session.get(Budget, budget_id) # type: ignore [union-attr]
    else:
        db_budget = session.get(Budget, budget_id) # type: ignore [union-attr]
    assert db_budget
    assert db_budget.amount == 850.50
    assert db_budget.category_id == user1_bud_categories["expense_id"]

@pytest.mark.asyncio
async def test_update_budget_wrong_user(client: TestClient, user1_bud_headers: dict, user2_bud_headers: dict): # Mark async
    """Test updating another user's budget fails."""
    budget_data = {"year": 2025, "month": 4, "amount": 400}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    update_data = {"year": 2025, "month": 4, "amount": 450}
    resp_update = await client.put(f"/budgets/{budget_id}", headers=user2_bud_headers, json=update_data) # Use await
    assert resp_update.status_code == 404

@pytest.mark.asyncio
async def test_update_budget_duplicate_period(client: TestClient, user1_bud_headers: dict, user1_bud_categories: dict): # Mark async
    """Test updating a budget to a period/category that already has a budget."""
    # Budget 1: Overall Jan 2025
    await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2025, "month": 1, "amount": 1000}) # Use await
    # Budget 2: Category Jan 2025
    resp_cat = await client.post("/budgets/", headers=user1_bud_headers, json={"year": 2025, "month": 1, "amount": 200, "category_id": user1_bud_categories["expense_id"]}) # Use await
    budget2_id = resp_cat.json()["id"]

    # Try updating Budget 2 to be an overall budget for Jan 2025 (conflict with Budget 1)
    update_data = {"year": 2025, "month": 1, "amount": 250, "category_id": None}
    resp_update = await client.put(f"/budgets/{budget2_id}", headers=user1_bud_headers, json=update_data) # Use await
    assert resp_update.status_code == 400
    assert "already exists" in resp_update.json()["detail"]

@pytest.mark.asyncio
async def test_delete_budget(client: TestClient, user1_bud_headers: dict, session: DbSession): # Mark async, use DbSession
    """Test deleting a budget."""
    budget_data = {"year": 2025, "month": 5, "amount": 500}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    # Verify exists
    if settings.USE_ASYNC_DB:
        assert await session.get(Budget, budget_id) # type: ignore [union-attr]
    else:
        assert session.get(Budget, budget_id) # type: ignore [union-attr]


    # Delete
    resp_delete = await client.delete(f"/budgets/{budget_id}", headers=user1_bud_headers) # Use await
    assert resp_delete.status_code == 204

    # Verify deleted
    if settings.USE_ASYNC_DB:
        await session.expire_all() # Use await
        assert await session.get(Budget, budget_id) is None # type: ignore [union-attr]
    else:
        session.expire_all()
        assert session.get(Budget, budget_id) is None # type: ignore [union-attr]


@pytest.mark.asyncio
async def test_delete_budget_wrong_user(client: TestClient, user1_bud_headers: dict, user2_bud_headers: dict): # Mark async
    """Test deleting another user's budget fails."""
    budget_data = {"year": 2025, "month": 6, "amount": 600}
    resp_create = await client.post("/budgets/", headers=user1_bud_headers, json=budget_data) # Use await
    budget_id = resp_create.json()["id"]

    resp_delete = await client.delete(f"/budgets/{budget_id}", headers=user2_bud_headers) # Use await
    assert resp_delete.status_code == 404
