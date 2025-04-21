import pytest
import pytest_asyncio # Import asyncio marker
from fastapi.testclient import TestClient
from sqlmodel import Session # Keep sync Session for type hint if needed
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import Union # For type hint
from datetime import date, timedelta

from models import Transaction, Category # Import models
from dto import CategoryType # Import enum
from core.config import settings # Import settings

# Use fixtures defined in conftest.py and potentially test_categories.py/test_transactions.py
# Re-defining the helper here for now, but consider refactoring to conftest.py.

# --- Helper Function & Test Data (Consider moving/sharing via conftest.py) ---
user1_email_rep = "user1_rep@example.com"
user1_pw_rep = "pw1_rep"
user2_email_rep = "user2_rep@example.com"
user2_pw_rep = "pw2_rep"

# Type hint for the session fixture result
DbSession = Union[Session, AsyncSession]

@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user1_rep_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user1 specific to report tests."""
    await client.post("/auth/register", json={"email": user1_email_rep, "password": user1_pw_rep}) # Use await
    login_data = {"username": user1_email_rep, "password": user1_pw_rep}
    response = await client.post("/auth/token", data=login_data) # Use await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="module") # Change to async fixture
async def user2_rep_headers(client: TestClient) -> dict: # Make async
    """Fixture to get auth headers for user2 specific to report tests."""
    await client.post("/auth/register", json={"email": user2_email_rep, "password": user2_pw_rep}) # Use await
    login_data = {"username": user2_email_rep, "password": user2_pw_rep}
    response = await client.post("/auth/token", data=login_data) # Use await
    tokens = response.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest_asyncio.fixture(scope="function") # Change to async fixture
async def setup_report_data(client: TestClient, user1_rep_headers: dict, user2_rep_headers: dict) -> dict: # Make async
    """Fixture to set up categories and transactions for report testing."""
    # User 1 Categories
    cat1_u1_resp = await client.post("/categories/", headers=user1_rep_headers, json={"name": "Salary_R", "type": CategoryType.INCOME}) # Use await
    cat2_u1_resp = await client.post("/categories/", headers=user1_rep_headers, json={"name": "Groceries_R", "type": CategoryType.EXPENSE}) # Use await
    cat3_u1_resp = await client.post("/categories/", headers=user1_rep_headers, json={"name": "Bonus_R", "type": CategoryType.INCOME}) # Use await
    cat1_u1_id = cat1_u1_resp.json()["id"]
    cat2_u1_id = cat2_u1_resp.json()["id"]
    cat3_u1_id = cat3_u1_resp.json()["id"]

    # User 2 Category
    cat1_u2_resp = await client.post("/categories/", headers=user2_rep_headers, json={"name": "Consulting_R", "type": CategoryType.INCOME}) # Use await
    cat1_u2_id = cat1_u2_resp.json()["id"]

    # Transactions - This Month (assuming current month is test month)
    today = date.today()
    current_year = today.year
    current_month = today.month
    first_day_current_month = today.replace(day=1)
    last_month_date = (first_day_current_month - timedelta(days=1)).replace(day=15) # A day in last month

    # User 1 Transactions (Current Month)
    await client.post("/transactions/", headers=user1_rep_headers, json={"amount": 2000, "date": str(today), "category_id": cat1_u1_id}) # Use await
    await client.post("/transactions/", headers=user1_rep_headers, json={"amount": 150, "date": str(today), "category_id": cat2_u1_id}) # Use await
    await client.post("/transactions/", headers=user1_rep_headers, json={"amount": 80, "date": str(first_day_current_month), "category_id": cat2_u1_id}) # Use await
    await client.post("/transactions/", headers=user1_rep_headers, json={"amount": 500, "date": str(today), "category_id": cat3_u1_id}) # Use await
    # User 1 Transaction (Last Month)
    await client.post("/transactions/", headers=user1_rep_headers, json={"amount": 100, "date": str(last_month_date), "category_id": cat2_u1_id}) # Use await

    # User 2 Transaction (Current Month)
    await client.post("/transactions/", headers=user2_rep_headers, json={"amount": 3000, "date": str(today), "category_id": cat1_u2_id}) # Use await

    return {"year": current_year, "month": current_month}


# --- Tests ---

@pytest.mark.asyncio
async def test_get_monthly_report_unauthenticated(client: TestClient): # Mark async
    """Test getting report without authentication fails."""
    response = await client.get("/reports/monthly?year=2024&month=1") # Use await
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_monthly_report_missing_params(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test getting report with missing year/month parameters."""
    response_no_year = await client.get("/reports/monthly?month=1", headers=user1_rep_headers) # Use await
    assert response_no_year.status_code == 422 # Unprocessable Entity

    response_no_month = await client.get("/reports/monthly?year=2024", headers=user1_rep_headers) # Use await
    assert response_no_month.status_code == 422

@pytest.mark.asyncio
async def test_get_monthly_report_invalid_params(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test getting report with invalid month."""
    response = await client.get("/reports/monthly?year=2024&month=13", headers=user1_rep_headers) # Use await
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_monthly_report_no_data(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test getting report for a month with no transactions for the user."""
    # Assuming year 1999 month 1 has no data
    response = await client.get("/reports/monthly?year=1999&month=1", headers=user1_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 1999
    assert data["month"] == 1
    assert data["total_income"] == 0.0
    assert data["total_expense"] == 0.0
    assert data["net_balance"] == 0.0
    assert data["income_by_category"] == []
    assert data["expense_by_category"] == []

@pytest.mark.asyncio
async def test_get_monthly_report_success(client: TestClient, user1_rep_headers: dict, setup_report_data: dict): # Mark async
    """Test getting a report with data, verifying totals and breakdown."""
    year = setup_report_data["year"]
    month = setup_report_data["month"]

    response = await client.get(f"/reports/monthly?year={year}&month={month}", headers=user1_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()

    assert data["year"] == year
    assert data["month"] == month
    assert data["total_income"] == 2000.0 + 500.0 # Salary + Bonus
    assert data["total_expense"] == 150.0 + 80.0 # Groceries
    assert data["net_balance"] == (2000.0 + 500.0) - (150.0 + 80.0)

    assert len(data["income_by_category"]) == 2
    assert len(data["expense_by_category"]) == 1

    # Check income breakdown (order might vary based on sum)
    income_names = {item["category_name"] for item in data["income_by_category"]}
    assert income_names == {"Salary_R", "Bonus_R"}
    for item in data["income_by_category"]:
        if item["category_name"] == "Salary_R":
            assert item["total_amount"] == 2000.0
        elif item["category_name"] == "Bonus_R":
            assert item["total_amount"] == 500.0

    # Check expense breakdown
    expense_item = data["expense_by_category"][0]
    assert expense_item["category_name"] == "Groceries_R"
    assert expense_item["total_amount"] == 150.0 + 80.0

@pytest.mark.asyncio
async def test_get_monthly_report_user_isolation(client: TestClient, user2_rep_headers: dict, setup_report_data: dict): # Mark async
    """Test that user 2's report only contains user 2's data."""
    year = setup_report_data["year"]
    month = setup_report_data["month"]

    response = await client.get(f"/reports/monthly?year={year}&month={month}", headers=user2_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()

    assert data["year"] == year
    assert data["month"] == month
    assert data["total_income"] == 3000.0 # Only user 2's income
    assert data["total_expense"] == 0.0
    assert data["net_balance"] == 3000.0
    assert len(data["income_by_category"]) == 1
    assert data["income_by_category"][0]["category_name"] == "Consulting_R"
    assert data["income_by_category"][0]["total_amount"] == 3000.0
    assert data["expense_by_category"] == []

# --- Yearly Report Tests ---

@pytest.mark.asyncio
async def test_get_yearly_report_success(client: TestClient, user1_rep_headers: dict, setup_report_data: dict): # Mark async
    """Test getting a yearly report with data."""
    year = setup_report_data["year"]

    response = await client.get(f"/reports/yearly?year={year}", headers=user1_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()

    assert data["year"] == year
    # Includes current month's data + last month's data from setup
    assert data["total_income"] == 2000.0 + 500.0
    assert data["total_expense"] == 150.0 + 80.0 + 100.0 # Includes last month's expense
    assert data["net_balance"] == (2000.0 + 500.0) - (150.0 + 80.0 + 100.0)

    assert len(data["income_by_category"]) == 2
    assert len(data["expense_by_category"]) == 1 # Still only one expense category used

    expense_item = data["expense_by_category"][0]
    assert expense_item["category_name"] == "Groceries_R"
    assert expense_item["total_amount"] == 150.0 + 80.0 + 100.0 # Sum of all groceries in the year

@pytest.mark.asyncio
async def test_get_yearly_report_no_data(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test yearly report for a year with no data."""
    response = await client.get("/reports/yearly?year=1998", headers=user1_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 1998
    assert data["total_income"] == 0.0
    assert data["total_expense"] == 0.0
    assert data["net_balance"] == 0.0

# --- Custom Date Range Report Tests ---

@pytest.mark.asyncio
async def test_get_custom_range_report_success(client: TestClient, user1_rep_headers: dict, setup_report_data: dict): # Mark async
    """Test getting a report for a custom date range."""
    # Get range covering only last month's transaction from setup
    today = date.today()
    first_day_current_month = today.replace(day=1)
    last_month_start = (first_day_current_month - timedelta(days=1)).replace(day=1)
    last_month_end = first_day_current_month - timedelta(days=1)

    response = await client.get(f"/reports/custom?start_date={last_month_start}&end_date={last_month_end}", headers=user1_rep_headers) # Use await
    assert response.status_code == 200
    data = response.json()

    assert data["start_date"] == str(last_month_start)
    assert data["end_date"] == str(last_month_end)
    assert data["total_income"] == 0.0
    assert data["total_expense"] == 100.0 # Only the transaction from last month
    assert data["net_balance"] == -100.0
    assert len(data["income_by_category"]) == 0
    assert len(data["expense_by_category"]) == 1
    assert data["expense_by_category"][0]["category_name"] == "Groceries_R"
    assert data["expense_by_category"][0]["total_amount"] == 100.0

@pytest.mark.asyncio
async def test_get_custom_range_report_invalid_range(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test custom range report with start_date after end_date."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    response = await client.get(f"/reports/custom?start_date={today}&end_date={yesterday}", headers=user1_rep_headers) # Use await
    assert response.status_code == 400
    assert "Start date cannot be after end date" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_custom_range_report_missing_params(client: TestClient, user1_rep_headers: dict): # Mark async
    """Test custom range report with missing date parameters."""
    today = date.today()
    response = await client.get(f"/reports/custom?start_date={today}", headers=user1_rep_headers) # Use await
    assert response.status_code == 422 # Unprocessable Entity
