from typing import List, Optional, Union, Any # Added Union, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession

# Import unified session dependency and settings
from core.db import get_db_session
from core.config import settings
from models import Budget, User, Category # Import models
from dto import BudgetCreate, BudgetRead # Import DTOs
from middlewares.auth import get_current_active_user # Import dependency

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

@router.post("/", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
async def create_budget( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new budget for a specific month (and optionally category).
    """
    # Check if category exists and belongs to user if category_id is provided
    if budget_in.category_id:
        if settings.USE_ASYNC_DB:
            category = await session.get(Category, budget_in.category_id) # type: ignore [union-attr]
        else:
            category = session.get(Category, budget_in.category_id) # type: ignore [union-attr]
        if not category or category.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {budget_in.category_id} not found or not owned by user."
            )

    # Check if a budget for this user, year, month, category already exists
    statement = (
        select(Budget)
        .where(Budget.owner_id == current_user.id)
        .where(Budget.year == budget_in.year)
        .where(Budget.month == budget_in.month)
        .where(Budget.category_id == budget_in.category_id) # Handles None correctly
    )
    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        existing_budget = results.first()
    else:
        existing_budget = session.exec(statement).first() # type: ignore [union-attr]

    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget for this period and category already exists."
        )

    # Create budget
    db_budget = Budget.model_validate(budget_in, update={"owner_id": current_user.id})
    session.add(db_budget)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_budget) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_budget) # type: ignore [union-attr]
    return db_budget

@router.get("/", response_model=List[BudgetRead])
async def read_budgets( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    year: Optional[int] = Query(None, description="Filter by year"),
    month: Optional[int] = Query(None, description="Filter by month (1-12)", ge=1, le=12),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve budgets for the current user, optionally filtered by year, month, or category.
    """
    statement = select(Budget).where(Budget.owner_id == current_user.id)
    if year:
        statement = statement.where(Budget.year == year)
    if month:
        statement = statement.where(Budget.month == month)
    if category_id:
         # Verify category ownership before filtering
        if settings.USE_ASYNC_DB:
            category = await session.get(Category, category_id) # type: ignore [union-attr]
        else:
            category = session.get(Category, category_id) # type: ignore [union-attr]
        if not category or category.owner_id != current_user.id:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found for this user.")
        statement = statement.where(Budget.category_id == category_id)

    statement = statement.offset(skip).limit(limit).order_by(Budget.year, Budget.month, Budget.category_id)

    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        budgets = results.all()
    else:
        budgets = session.exec(statement).all() # type: ignore [union-attr]
    return budgets

@router.get("/{budget_id}", response_model=BudgetRead)
async def read_budget_by_id( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    budget_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific budget by its ID.
    """
    if settings.USE_ASYNC_DB:
        budget = await session.get(Budget, budget_id) # type: ignore [union-attr]
    else:
        budget = session.get(Budget, budget_id) # type: ignore [union-attr]

    if not budget or budget.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget

@router.put("/{budget_id}", response_model=BudgetRead)
async def update_budget( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    budget_id: int,
    budget_in: BudgetCreate, # Use Create DTO for update payload
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing budget.
    Note: This allows changing year/month/category, which might require re-checking for duplicates.
    """
    if settings.USE_ASYNC_DB:
        db_budget = await session.get(Budget, budget_id) # type: ignore [union-attr]
    else:
        db_budget = session.get(Budget, budget_id) # type: ignore [union-attr]

    if not db_budget or db_budget.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    # Check if the updated combination (year, month, category) already exists for another budget
    if (db_budget.year != budget_in.year or
        db_budget.month != budget_in.month or
        db_budget.category_id != budget_in.category_id):
        statement = (
            select(Budget)
            .where(Budget.owner_id == current_user.id)
            .where(Budget.year == budget_in.year)
            .where(Budget.month == budget_in.month)
            .where(Budget.category_id == budget_in.category_id)
            .where(Budget.id != budget_id) # Exclude the current budget being updated
        )
        if settings.USE_ASYNC_DB:
            results = await session.exec(statement) # type: ignore [union-attr]
            existing_budget = results.first()
        else:
            existing_budget = session.exec(statement).first() # type: ignore [union-attr]

        if existing_budget:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Another budget for this period and category already exists."
            )

    # Check category ownership if category_id is changing or being set
    if budget_in.category_id and budget_in.category_id != db_budget.category_id:
        if settings.USE_ASYNC_DB:
            category = await session.get(Category, budget_in.category_id) # type: ignore [union-attr]
        else:
            category = session.get(Category, budget_in.category_id) # type: ignore [union-attr]
        if not category or category.owner_id != current_user.id:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail=f"Category with id {budget_in.category_id} not found or not owned by user."
             )

    # Update fields
    budget_data = budget_in.model_dump(exclude_unset=True)
    for key, value in budget_data.items():
        setattr(db_budget, key, value)

    session.add(db_budget)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_budget) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_budget) # type: ignore [union-attr]
    return db_budget

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    budget_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a budget.
    """
    if settings.USE_ASYNC_DB:
        budget = await session.get(Budget, budget_id) # type: ignore [union-attr]
    else:
        budget = session.get(Budget, budget_id) # type: ignore [union-attr]

    if not budget or budget.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    if settings.USE_ASYNC_DB:
        await session.delete(budget) # type: ignore [union-attr]
        await session.commit() # type: ignore [union-attr]
    else:
        session.delete(budget) # type: ignore [union-attr]
        session.commit() # type: ignore [union-attr]
    # No content response
