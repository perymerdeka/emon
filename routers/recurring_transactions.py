from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Union, Any # Added Union, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from datetime import date # Import date

# Import unified session dependency and settings
from core.db import get_db_session
from core.config import settings
from models import RecurringTransaction, User, Category # Import models
from dto import RecurringTransactionCreate, RecurringTransactionRead # Import DTOs
from middlewares.auth import get_current_active_user # Import dependency
# Import the service function
from services.recurring_transaction_service import generate_due_transactions # Keep sync for now

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

@router.post("/", response_model=RecurringTransactionRead, status_code=status.HTTP_201_CREATED)
async def create_recurring_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    recurring_tx_in: RecurringTransactionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new recurring transaction rule.
    """
    # Check if category exists and belongs to user
    if settings.USE_ASYNC_DB:
        category = await session.get(Category, recurring_tx_in.category_id) # type: ignore [union-attr]
    else:
        category = session.get(Category, recurring_tx_in.category_id) # type: ignore [union-attr]

    if not category or category.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {recurring_tx_in.category_id} not found or not owned by user."
        )

    # Optional: Add validation for end_date > start_date if end_date is provided
    if recurring_tx_in.end_date and recurring_tx_in.end_date < recurring_tx_in.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date."
        )

    # Create recurring transaction rule
    db_recurring_tx = RecurringTransaction.model_validate(
        recurring_tx_in,
        update={"owner_id": current_user.id}
    )
    session.add(db_recurring_tx)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_recurring_tx) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_recurring_tx) # type: ignore [union-attr]
    return db_recurring_tx

@router.get("/", response_model=List[RecurringTransactionRead])
async def read_recurring_transactions( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve recurring transaction rules for the current user.
    """
    statement = select(RecurringTransaction).where(RecurringTransaction.owner_id == current_user.id)
    if is_active is not None:
        statement = statement.where(RecurringTransaction.is_active == is_active)

    statement = statement.offset(skip).limit(limit).order_by(RecurringTransaction.start_date)

    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        recurring_txs = results.all()
    else:
        recurring_txs = session.exec(statement).all() # type: ignore [union-attr]
    return recurring_txs

@router.get("/{recurring_tx_id}", response_model=RecurringTransactionRead)
async def read_recurring_transaction_by_id( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    recurring_tx_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve a specific recurring transaction rule by its ID.
    """
    if settings.USE_ASYNC_DB:
        recurring_tx = await session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]
    else:
        recurring_tx = session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]

    if not recurring_tx or recurring_tx.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction rule not found")
    return recurring_tx

@router.put("/{recurring_tx_id}", response_model=RecurringTransactionRead)
async def update_recurring_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    recurring_tx_id: int,
    recurring_tx_in: RecurringTransactionCreate, # Use Create DTO for update
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing recurring transaction rule.
    """
    if settings.USE_ASYNC_DB:
        db_recurring_tx = await session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]
    else:
        db_recurring_tx = session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]

    if not db_recurring_tx or db_recurring_tx.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction rule not found")

    # Check category ownership if category_id is changing
    if recurring_tx_in.category_id != db_recurring_tx.category_id:
        if settings.USE_ASYNC_DB:
            category = await session.get(Category, recurring_tx_in.category_id) # type: ignore [union-attr]
        else:
            category = session.get(Category, recurring_tx_in.category_id) # type: ignore [union-attr]
        if not category or category.owner_id != current_user.id:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail=f"Category with id {recurring_tx_in.category_id} not found or not owned by user."
             )

    # Optional: Add validation for end_date > start_date if end_date is provided/changed
    if recurring_tx_in.end_date and recurring_tx_in.end_date < recurring_tx_in.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date."
        )

    # Update fields
    tx_data = recurring_tx_in.model_dump(exclude_unset=True)
    for key, value in tx_data.items():
        setattr(db_recurring_tx, key, value)

    # Reset last_created_date if start_date changes? Or handle in generation logic.
    # For now, we don't reset it here.

    session.add(db_recurring_tx)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_recurring_tx) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_recurring_tx) # type: ignore [union-attr]
    return db_recurring_tx

@router.delete("/{recurring_tx_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    recurring_tx_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a recurring transaction rule.
    Note: This does NOT delete transactions already generated by this rule.
    """
    if settings.USE_ASYNC_DB:
        recurring_tx = await session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]
    else:
        recurring_tx = session.get(RecurringTransaction, recurring_tx_id) # type: ignore [union-attr]

    if not recurring_tx or recurring_tx.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction rule not found")

    if settings.USE_ASYNC_DB:
        await session.delete(recurring_tx) # type: ignore [union-attr]
        await session.commit() # type: ignore [union-attr]
    else:
        session.delete(recurring_tx) # type: ignore [union-attr]
        session.commit() # type: ignore [union-attr]
    # No content response

# --- Manual Trigger Endpoint ---

@router.post("/generate-due", status_code=status.HTTP_202_ACCEPTED)
async def trigger_generate_due_transactions(
    background_tasks: BackgroundTasks,
    run_date_str: Optional[str] = Query(None, description="Optional date (YYYY-MM-DD) to run generation for, defaults to today"),
    current_user: User = Depends(get_current_active_user) # Ensure only logged-in users can trigger
    # TODO: Add admin role check here in a real application
):
    """
    Manually triggers the generation of due recurring transactions.
    Runs as a background task. Specify run_date to simulate running on a past/future date.
    """
    run_date = date.today()
    if run_date_str:
        try:
            run_date = date.fromisoformat(run_date_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    print(f"Received request to generate recurring transactions for date: {run_date}")
    # Run the generation logic in the background
    background_tasks.add_task(generate_due_transactions, run_date=run_date)

    return {"message": "Recurring transaction generation task accepted."}
