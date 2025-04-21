from datetime import date
from typing import Optional

from datetime import date
from datetime import date
from typing import Optional, List, Union, Any # Added List, Union, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, SQLModel # Import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession

# Import unified session dependency and settings
from core.db import get_db_session
from core.config import settings
from models import Transaction, Category, User # Import User model
from dto import TransactionBase, TransactionRead, TransactionReadWithCategory # Import DTOs
from middlewares.auth import get_current_active_user # Import dependency

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

@router.post("/", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def create_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    transaction_in: TransactionBase,
    current_user: User = Depends(get_current_active_user)
):
    # 1. Get the category and verify ownership
    if settings.USE_ASYNC_DB:
        category = await session.get(Category, transaction_in.category_id) # type: ignore [union-attr]
    else:
        category = session.get(Category, transaction_in.category_id) # type: ignore [union-attr]

    if not category or category.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 403 Forbidden if category exists but isn't owned
            detail=f"Category with id {transaction_in.category_id} not found or not owned by user."
        )

    # 2. Create the transaction instance, adding owner_id and type
    transaction_data = transaction_in.model_dump()
    db_transaction = Transaction(
        **transaction_data,
        type=category.type,
        owner_id=current_user.id # Set owner_id
    )

    # 3. Add, commit, refresh
    session.add(db_transaction)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_transaction) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_transaction) # type: ignore [union-attr]

    return db_transaction

@router.get("/", response_model=list[TransactionReadWithCategory]) # Return with category details
async def read_transactions( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    current_user: User = Depends(get_current_active_user)
):
    # Start query, always filter by owner_id
    statement = select(Transaction).where(Transaction.owner_id == current_user.id)

    if start_date:
        statement = statement.where(Transaction.date >= start_date)
    if end_date:
        statement = statement.where(Transaction.date <= end_date)
    if category_id:
        # Verify the category_id belongs to the user before filtering
        if settings.USE_ASYNC_DB:
            category = await session.get(Category, category_id) # type: ignore [union-attr]
        else:
            category = session.get(Category, category_id) # type: ignore [union-attr]
        if not category or category.owner_id != current_user.id:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found for this user.")
        statement = statement.where(Transaction.category_id == category_id)

    statement = statement.offset(skip).limit(limit).order_by(Transaction.date.desc(), Transaction.id.desc()) # Order by date desc

    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        transactions = results.all()
    else:
        transactions = session.exec(statement).all() # type: ignore [union-attr]

    # Note: SQLModel/SQLAlchemy handles loading relationships even in async mode
    return transactions

@router.get("/{transaction_id}", response_model=TransactionReadWithCategory)
async def read_transaction_by_id( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    transaction_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        transaction = await session.get(Transaction, transaction_id) # type: ignore [union-attr]
    else:
        transaction = session.get(Transaction, transaction_id) # type: ignore [union-attr]

    # Check if transaction exists AND belongs to the current user
    if not transaction or transaction.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=TransactionRead)
async def update_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    transaction_id: int,
    transaction_in: TransactionBase,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        db_transaction = await session.get(Transaction, transaction_id) # type: ignore [union-attr]
    else:
        db_transaction = session.get(Transaction, transaction_id) # type: ignore [union-attr]

    # Check if transaction exists AND belongs to the current user
    if not db_transaction or db_transaction.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    # Get the new category and verify ownership
    if settings.USE_ASYNC_DB:
        new_category = await session.get(Category, transaction_in.category_id) # type: ignore [union-attr]
    else:
        new_category = session.get(Category, transaction_in.category_id) # type: ignore [union-attr]

    if not new_category or new_category.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 403
            detail=f"Category with id {transaction_in.category_id} not found or not owned by user."
        )

    # Update model fields from the input DTO
    transaction_data = transaction_in.model_dump(exclude_unset=True)
    for key, value in transaction_data.items():
        setattr(db_transaction, key, value)

    # Crucially, update the transaction type based on the potentially new category
    db_transaction.type = new_category.type

    session.add(db_transaction)
    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_transaction) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_transaction) # type: ignore [union-attr]

    return db_transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    transaction_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        transaction = await session.get(Transaction, transaction_id) # type: ignore [union-attr]
    else:
        transaction = session.get(Transaction, transaction_id) # type: ignore [union-attr]

    # Check if transaction exists AND belongs to the current user
    if not transaction or transaction.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if settings.USE_ASYNC_DB:
        await session.delete(transaction) # type: ignore [union-attr]
        await session.commit() # type: ignore [union-attr]
    else:
        session.delete(transaction) # type: ignore [union-attr]
        session.commit() # type: ignore [union-attr]

    # No response body needed for 204

# Removed TODO comment as reports are in a separate file
