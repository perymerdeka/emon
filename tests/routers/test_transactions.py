import pytest
import pytest_asyncio # Import asyncio marker
from fastapi.testclient import TestClient
from sqlmodel import Session, select # Keep sync Session for type hint if needed
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from datetime import date, timedelta

from models import Transaction, Category # Import models
from models.category_model import CategoryType # Import enum from correct location
from core.config import settings # Import settings

# Use fixtures defined in conftest.py

# --- Test Data ---
user1_email = "user1_trans@example.com"
user1_pw = "pw1_trans"
user2_email = "user2_trans@example.com"
user2_pw = "pw2_trans"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

# --- Fixtures ---
@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user1_trans_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user1 specific to transaction tests."""
    client.post("/auth/register", json={"email": user1_email, "password": user1_pw}) # REMOVE await
    login_data = {"username": user1_email, "password": user1_pw}
    response = client.post("/auth/token", data=login_data) # REMOVE await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user2_trans_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user2 specific to transaction tests."""
    client.post("/auth/register", json={"email": user2_email, "password": user2_pw}) # REMOVE await
    login_data = {"username": user2_email, "password": user2_pw}
    response = client.post("/auth/token", data=login_data) # REMOVE await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="function") # Change to async fixture
async def user1_categories(client: TestClient, user1_trans_headers: dict) -> dict: # Make async
    """Fixture to create some categories for user1."""
    income_data = {"name": "Salary_T", "type": CategoryType.INCOME}
    expense_data = {"name": "Food_T", "type": CategoryType.EXPENSE}
    resp_income = client.post("/categories/", headers=user1_trans_headers, json=income_data) # REMOVE await
    resp_expense = client.post("/categories/", headers=user1_trans_headers, json=expense_data) # REMOVE await
    assert resp_income.status_code == 201
    assert resp_expense.status_code == 201
    return {
        "income_id": resp_income.json()["id"],
        "expense_id": resp_expense.json()["id"]
    }

# --- Tests ---

@pytest.mark.asyncio
async def test_create_transaction_unauthenticated(client: TestClient): # Mark async
    """Test creating transaction without authentication fails."""
    trans_data = {"amount": 100, "date": str(date.today()), "category_id": 1}
    response = client.post("/transactions/", json=trans_data) # REMOVE await
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_transaction_success(client: TestClient, user1_trans_headers: dict, user1_categories: dict): # Mark async
    """Test successful transaction creation."""
    trans_data = {
        "amount": 50.5,
        "date": str(date.today()),
        "description": "Lunch",
        "category_id": user1_categories["expense_id"]
    }
    response = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == trans_data["amount"]
    assert data["description"] == trans_data["description"]
    assert data["category_id"] == trans_data["category_id"]
    assert data["type"] == CategoryType.EXPENSE # Check type derived correctly

@pytest.mark.asyncio
async def test_create_transaction_invalid_category(client: TestClient, user1_trans_headers: dict): # Mark async
    """Test creating transaction with a non-existent category ID."""
    trans_data = {"amount": 100, "date": str(date.today()), "category_id": 99999}
    response = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    assert response.status_code == 404 # Category not found

@pytest.mark.asyncio
async def test_create_transaction_wrong_user_category( # Mark async
    client: TestClient, user1_trans_headers: dict, user2_trans_headers: dict
):
    """Test creating transaction using a category belonging to another user."""
    # User 2 creates a category
    cat_data = {"name": "User2 Only Cat", "type": CategoryType.EXPENSE}
    resp_cat = client.post("/categories/", headers=user2_trans_headers, json=cat_data) # REMOVE await
    assert resp_cat.status_code == 201
    user2_cat_id = resp_cat.json()["id"]

    # User 1 tries to create transaction using User 2's category
    trans_data = {"amount": 25, "date": str(date.today()), "category_id": user2_cat_id}
    response = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    assert response.status_code == 404 # Should fail as category not found for user 1

@pytest.mark.asyncio
async def test_read_transactions_authenticated_empty(client: TestClient, user1_trans_headers: dict): # Mark async
    """Test reading transactions when none exist for the user."""
    response = client.get("/transactions/", headers=user1_trans_headers) # REMOVE await
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_read_transactions_filtering_and_ownership( # Mark async
    client: TestClient, user1_trans_headers: dict, user2_trans_headers: dict, user1_categories: dict, session: DbSession # Use DbSession
):
    """Test reading transactions, ensuring filtering and ownership work."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    # User 1 transactions
    t1_data = {"amount": 1000, "date": str(today), "category_id": user1_categories["income_id"]}
    t2_data = {"amount": 50, "date": str(today), "category_id": user1_categories["expense_id"]}
    t3_data = {"amount": 30, "date": str(yesterday), "category_id": user1_categories["expense_id"]}
    client.post("/transactions/", headers=user1_trans_headers, json=t1_data) # REMOVE await
    client.post("/transactions/", headers=user1_trans_headers, json=t2_data) # REMOVE await
    client.post("/transactions/", headers=user1_trans_headers, json=t3_data) # REMOVE await

    # User 2 transaction (create category first)
    cat_data_u2 = {"name": "User2 Income", "type": CategoryType.INCOME}
    resp_cat_u2 = client.post("/categories/", headers=user2_trans_headers, json=cat_data_u2) # REMOVE await
    user2_cat_id = resp_cat_u2.json()["id"]
    t4_data = {"amount": 2000, "date": str(today), "category_id": user2_cat_id}
    client.post("/transactions/", headers=user2_trans_headers, json=t4_data) # REMOVE await

    # Read all for User 1
    resp_all_u1 = client.get("/transactions/", headers=user1_trans_headers) # REMOVE await
    assert resp_all_u1.status_code == 200
    assert len(resp_all_u1.json()) == 3 # Should only see user 1's transactions

    # Read filtered by date for User 1
    resp_date_u1 = client.get(f"/transactions/?start_date={today}&end_date={today}", headers=user1_trans_headers) # REMOVE await
    assert resp_date_u1.status_code == 200
    assert len(resp_date_u1.json()) == 2

    # Read filtered by category for User 1
    resp_cat_u1 = client.get(f"/transactions/?category_id={user1_categories['expense_id']}", headers=user1_trans_headers) # REMOVE await
    assert resp_cat_u1.status_code == 200
    assert len(resp_cat_u1.json()) == 2

    # Read all for User 2
    resp_all_u2 = client.get("/transactions/", headers=user2_trans_headers) # REMOVE await
    assert resp_all_u2.status_code == 200
    assert len(resp_all_u2.json()) == 1 # Should only see user 2's transaction

@pytest.mark.asyncio
async def test_read_transaction_by_id_wrong_user( # Mark async
    client: TestClient, user1_trans_headers: dict, user2_trans_headers: dict, user1_categories: dict
):
    """Test reading a specific transaction fails if owned by another user."""
    trans_data = {"amount": 10, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]

    # User 2 tries to read User 1's transaction
    resp_read = client.get(f"/transactions/{trans_id}", headers=user2_trans_headers) # REMOVE await
    assert resp_read.status_code == 404 # Not found for user 2

@pytest.mark.asyncio
async def test_update_transaction(client: TestClient, user1_trans_headers: dict, user1_categories: dict, session: DbSession): # Mark async, use DbSession
    """Test updating a transaction."""
    trans_data = {"amount": 75, "date": str(date.today()), "category_id": user1_categories["expense_id"], "description": "Initial"}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]

    update_data = {"amount": 80.0, "date": str(date.today()), "category_id": user1_categories["expense_id"], "description": "Updated Desc"}
    resp_update = client.put(f"/transactions/{trans_id}", headers=user1_trans_headers, json=update_data) # REMOVE await
    assert resp_update.status_code == 200
    updated_trans = resp_update.json()
    assert updated_trans["amount"] == update_data["amount"]
    assert updated_trans["description"] == update_data["description"]

    # Verify in DB
    if settings.USE_ASYNC_DB:
        db_trans = await session.get(Transaction, trans_id) # type: ignore [union-attr]
    else:
        db_trans = session.get(Transaction, trans_id) # type: ignore [union-attr]
    assert db_trans
    assert db_trans.amount == update_data["amount"]
    assert db_trans.description == update_data["description"]

@pytest.mark.asyncio
async def test_update_transaction_change_category_and_type( # Mark async
    client: TestClient, user1_trans_headers: dict, user1_categories: dict, session: DbSession # Use DbSession
):
    """Test updating a transaction's category also updates its type."""
    # Start as expense
    trans_data = {"amount": 20, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]
    assert resp_create.json()["type"] == CategoryType.EXPENSE

    # Update to income category
    update_data = {"amount": 20, "date": str(date.today()), "category_id": user1_categories["income_id"]}
    resp_update = client.put(f"/transactions/{trans_id}", headers=user1_trans_headers, json=update_data) # REMOVE await
    assert resp_update.status_code == 200
    assert resp_update.json()["type"] == CategoryType.INCOME # Type should change

    # Verify in DB
    if settings.USE_ASYNC_DB:
        db_trans = await session.get(Transaction, trans_id) # type: ignore [union-attr]
    else:
        db_trans = session.get(Transaction, trans_id) # type: ignore [union-attr]
    assert db_trans
    assert db_trans.type == CategoryType.INCOME

@pytest.mark.asyncio
async def test_update_transaction_wrong_user( # Mark async
    client: TestClient, user1_trans_headers: dict, user2_trans_headers: dict, user1_categories: dict
):
    """Test updating another user's transaction fails."""
    trans_data = {"amount": 15, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]

    update_data = {"amount": 20, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_update = client.put(f"/transactions/{trans_id}", headers=user2_trans_headers, json=update_data) # REMOVE await
    assert resp_update.status_code == 404 # Not found for user 2

@pytest.mark.asyncio
async def test_delete_transaction(client: TestClient, user1_trans_headers: dict, user1_categories: dict, session: DbSession): # Mark async, use DbSession
    """Test deleting a transaction."""
    trans_data = {"amount": 5, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]

    # Verify exists
    if settings.USE_ASYNC_DB:
        assert await session.get(Transaction, trans_id) # type: ignore [union-attr]
    else:
        assert session.get(Transaction, trans_id) # type: ignore [union-attr]


    # Delete
    resp_delete = client.delete(f"/transactions/{trans_id}", headers=user1_trans_headers) # REMOVE await
    assert resp_delete.status_code == 204

    # Verify deleted
    if settings.USE_ASYNC_DB:
        await session.expire_all() # Use await
        assert await session.get(Transaction, trans_id) is None # type: ignore [union-attr]
    else:
        session.expire_all()
        assert session.get(Transaction, trans_id) is None # type: ignore [union-attr]


@pytest.mark.asyncio
async def test_delete_transaction_wrong_user( # Mark async
    client: TestClient, user1_trans_headers: dict, user2_trans_headers: dict, user1_categories: dict
):
    """Test deleting another user's transaction fails."""
    trans_data = {"amount": 99, "date": str(date.today()), "category_id": user1_categories["expense_id"]}
    resp_create = client.post("/transactions/", headers=user1_trans_headers, json=trans_data) # REMOVE await
    trans_id = resp_create.json()["id"]

    # User 2 tries to delete
    resp_delete = client.delete(f"/transactions/{trans_id}", headers=user2_trans_headers) # REMOVE await
    assert resp_delete.status_code == 404 # Not found for user 2
