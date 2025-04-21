import pytest
import pytest_asyncio # Import asyncio marker
from fastapi.testclient import TestClient
from sqlmodel import Session, select # Keep sync Session for type hint if needed
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from datetime import date, timedelta

from models import RecurringTransaction, Transaction, Category, RecurrenceFrequency # Import models
from dto import CategoryType # Import enum
from core.config import settings # Import settings
# Import the service function to test its effect
from services.recurring_transaction_service import generate_due_transactions

# --- Test Data & Fixtures ---
user1_email_rec = "user1_rec@example.com"
user1_pw_rec = "pw1_rec"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user1_rec_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user1 specific to recurring tests."""
    await client.post("/auth/register", json={"email": user1_email_rec, "password": user1_pw_rec}) # Use await
    login_data = {"username": user1_email_rec, "password": user1_pw_rec}
    response = await client.post("/auth/token", data=login_data) # Use await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="function") # Change to async fixture
async def user1_rec_categories(client: TestClient, user1_rec_headers: dict) -> dict: # Make async
    """Fixture to create categories for user1 for recurring tests."""
    income_data = {"name": "Salary_Rec", "type": CategoryType.INCOME}
    expense_data = {"name": "Rent_Rec", "type": CategoryType.EXPENSE}
    resp_income = await client.post("/categories/", headers=user1_rec_headers, json=income_data) # Use await
    resp_expense = await client.post("/categories/", headers=user1_rec_headers, json=expense_data) # Use await
    assert resp_income.status_code == 201
    assert resp_expense.status_code == 201
    return {
        "income_id": resp_income.json()["id"],
        "expense_id": resp_expense.json()["id"]
    }

# --- Tests for CRUD ---

@pytest.mark.asyncio
async def test_create_recurring_transaction(client: TestClient, user1_rec_headers: dict, user1_rec_categories: dict): # Mark async
    """Test creating a valid recurring transaction rule."""
    start_date = date.today()
    rec_data = {
        "description": "Monthly Rent",
        "amount": 1200.0,
        "start_date": str(start_date),
        "frequency": RecurrenceFrequency.MONTHLY,
        "category_id": user1_rec_categories["expense_id"],
        "is_active": True
    }
    response = await client.post("/recurring-transactions/", headers=user1_rec_headers, json=rec_data) # Use await
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == rec_data["description"]
    assert data["amount"] == rec_data["amount"]
    assert data["frequency"] == rec_data["frequency"]
    assert data["category_id"] == rec_data["category_id"]
    assert data["is_active"] is True
    assert data["last_created_date"] is None # Initially null

@pytest.mark.asyncio
async def test_read_recurring_transactions(client: TestClient, user1_rec_headers: dict, user1_rec_categories: dict): # Mark async
    """Test reading recurring transaction rules."""
    # Create a rule first
    start_date = date.today()
    rec_data = {"description": "Weekly Allowance", "amount": 20, "start_date": str(start_date), "frequency": RecurrenceFrequency.WEEKLY, "category_id": user1_rec_categories["expense_id"]}
    await client.post("/recurring-transactions/", headers=user1_rec_headers, json=rec_data) # Use await

    response = await client.get("/recurring-transactions/", headers=user1_rec_headers) # Use await
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1 # Should include the one we just created
    # Find the created rule (order might not be guaranteed)
    allowance_rule = next((r for r in data if r["description"] == rec_data["description"]), None)
    assert allowance_rule is not None

# TODO: Add tests for GET by ID, PUT, DELETE, filtering, ownership checks

# --- Tests for Generation Logic ---

@pytest.mark.asyncio
async def test_generate_due_transactions_monthly(client: TestClient, user1_rec_headers: dict, user1_rec_categories: dict, session: DbSession): # Mark async, use DbSession
    """Test the generation of a monthly recurring transaction."""
    start_date = date.today().replace(day=1) - timedelta(days=40) # Start last month
    rec_data = {
        "description": "Monthly Subscription",
        "amount": 9.99,
        "start_date": str(start_date),
        "frequency": RecurrenceFrequency.MONTHLY,
        "category_id": user1_rec_categories["expense_id"],
    }
    resp_create = await client.post("/recurring-transactions/", headers=user1_rec_headers, json=rec_data) # Use await
    assert resp_create.status_code == 201
    rule_id = resp_create.json()["id"]

    # Trigger generation for today
    resp_gen = await client.post("/recurring-transactions/generate-due", headers=user1_rec_headers) # Use await
    assert resp_gen.status_code == 202 # Accepted

    # Need to wait for background task or run synchronously for testing
    # For now, let's call the service function directly (requires dateutil)
    # Note: This bypasses the API layer for the generation part
    try:
        from dateutil.relativedelta import relativedelta
        # Call the async service function
        await generate_due_transactions() # Run for today
    except ImportError:
        pytest.skip("python-dateutil not installed, skipping generation test")
        return

    # Verify transactions were created
    if settings.USE_ASYNC_DB:
        await session.expire_all() # Use await
        # Expect two transactions: one for start_date month, one for current month
        stmt = select(Transaction).where(Transaction.description == rec_data["description"])
        results = await session.exec(stmt) # type: ignore [union-attr]
        created_txs = results.all()
        assert len(created_txs) == 2

        # Verify the rule's last_created_date is updated
        rule = await session.get(RecurringTransaction, rule_id) # type: ignore [union-attr]
    else:
        session.expire_all()
        stmt = select(Transaction).where(Transaction.description == rec_data["description"])
        created_txs = session.exec(stmt).all() # type: ignore [union-attr]
        assert len(created_txs) == 2
        rule = session.get(RecurringTransaction, rule_id) # type: ignore [union-attr]

    assert rule
    assert rule.last_created_date is not None
    # Check if last_created_date is the expected date for the *second* transaction
    expected_last_date = start_date + relativedelta(months=1)
    assert rule.last_created_date == expected_last_date

# TODO: Add more generation tests (weekly, daily, yearly, end_date, multiple due)
# TODO: Add tests for the manual trigger endpoint itself (checking background task acceptance)
