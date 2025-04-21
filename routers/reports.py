import calendar
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
import calendar # Import calendar for month range
from datetime import date # Import date
from typing import List # Import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
import calendar
from datetime import date
from typing import List, Optional, Union, Any # Added Union, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, SQLModel # Import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from sqlalchemy.sql.expression import literal_column

# Import unified session dependency and settings
from core.db import get_db_session
from core.config import settings
from models import Transaction, Category, CategoryType, User # Import User
# Import all report DTOs
from dto.report_dto import MonthlyReport, YearlyReport, DateRangeReport, CategorySummary
from middlewares.auth import get_current_active_user # Import dependency

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

# --- Helper Function for Report Generation ---

async def _generate_report_data( # Changed to async def
    session: DbSession, user_id: int, start_date: date, end_date: date
) -> tuple[float, float, List[CategorySummary], List[CategorySummary]]:
    """Helper to calculate totals and breakdowns for a given period and user."""

    # Base statement filtered by user and date range
    base_statement = (
        select(Transaction)
        .where(Transaction.owner_id == user_id)
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
    )
    if settings.USE_ASYNC_DB:
        results = await session.exec(base_statement) # type: ignore [union-attr]
        transactions = results.all()
    else:
        transactions = session.exec(base_statement).all() # type: ignore [union-attr]


    total_income = sum(t.amount for t in transactions if t.type == CategoryType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == CategoryType.EXPENSE)

    # Income breakdown query
    income_summary_query = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"), # Explicit label
            func.sum(Transaction.amount).label("total_amount")
        )
        .join(Category) # Join Transaction with Category
        .where(Transaction.owner_id == user_id) # Filter by owner
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
        .where(Transaction.type == CategoryType.INCOME)
        .group_by(Transaction.category_id, Category.name) # Group by ID and name
        .order_by(func.sum(Transaction.amount).desc())
    )
    if settings.USE_ASYNC_DB:
        income_results = (await session.exec(income_summary_query)).mappings().all() # type: ignore [union-attr]
    else:
        income_results = session.exec(income_summary_query).mappings().all() # type: ignore [union-attr]
    income_by_category = [CategorySummary(**row) for row in income_results]

    # Expense breakdown query
    expense_summary_query = (
        select(
            Transaction.category_id,
            Category.name.label("category_name"), # Explicit label
            func.sum(Transaction.amount).label("total_amount")
        )
        .join(Category)
        .where(Transaction.owner_id == user_id) # Filter by owner
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
        .where(Transaction.type == CategoryType.EXPENSE)
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )
    if settings.USE_ASYNC_DB:
        expense_results = (await session.exec(expense_summary_query)).mappings().all() # type: ignore [union-attr]
    else:
        expense_results = session.exec(expense_summary_query).mappings().all() # type: ignore [union-attr]
    expense_by_category = [CategorySummary(**row) for row in expense_results]

    return total_income, total_expense, income_by_category, expense_by_category


# --- Report Endpoints ---

@router.get("/monthly", response_model=MonthlyReport)
async def get_monthly_report( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    year: int = Query(..., description="Year of the report (e.g., 2024)", ge=1900),
    month: int = Query(..., description="Month of the report (1-12)", ge=1, le=12),
    current_user: User = Depends(get_current_active_user)
):
    """Generates a financial report for a specific month and year."""
    try:
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid year or month")

    # Call the async helper function
    total_income, total_expense, income_by_category, expense_by_category = await _generate_report_data(
        session, current_user.id, start_date, end_date
    )

    return MonthlyReport(
        year=year,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category
    )

@router.get("/yearly", response_model=YearlyReport)
async def get_yearly_report( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    year: int = Query(..., description="Year of the report (e.g., 2024)", ge=1900),
    current_user: User = Depends(get_current_active_user)
):
    """Generates a financial report for a specific year."""
    try:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    except ValueError:
         # This should ideally not happen with year validation, but good practice
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid year")

    # Call the async helper function
    total_income, total_expense, income_by_category, expense_by_category = await _generate_report_data(
        session, current_user.id, start_date, end_date
    )

    return YearlyReport(
        year=year,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category
    )

@router.get("/custom", response_model=DateRangeReport)
async def get_custom_range_report( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user)
):
    """Generates a financial report for a custom date range."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date cannot be after end date."
        )

    # Call the async helper function
    total_income, total_expense, income_by_category, expense_by_category = await _generate_report_data(
        session, current_user.id, start_date, end_date
    )

    return DateRangeReport(
        start_date=start_date,
        end_date=end_date,
        total_income=total_income,
        total_expense=total_expense,
        net_balance=total_income - total_expense,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category
    )
