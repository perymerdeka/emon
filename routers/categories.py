from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, SQLModel # Import SQLModel for type hint
from sqlmodel.ext.asyncio.session import AsyncSession # Import AsyncSession
from typing import List, Union, Any # For type hints

# Import the unified session dependency and settings
from core.db import get_db_session
from core.config import settings
from models import Category, User # Import User model
from dto import CategoryBase, CategoryRead # Import DTOs
from middlewares.auth import get_current_active_user # Import dependency

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    category_in: CategoryBase,
    current_user: User = Depends(get_current_active_user)
):
    # Check if category name already exists for this user
    statement = (
        select(Category)
        .where(Category.name == category_in.name)
        .where(Category.owner_id == current_user.id)
    )
    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        existing_category = results.first()
    else:
        existing_category = session.exec(statement).first() # type: ignore [union-attr]

    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_in.name}' already exists for this user."
        )

    # Create model instance, adding the owner_id
    db_category = Category.model_validate(category_in, update={"owner_id": current_user.id})
    session.add(db_category)

    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_category) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_category) # type: ignore [union-attr]

    return db_category

@router.get("/", response_model=list[CategoryRead])
async def read_categories( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    # Filter categories by owner_id
    statement = (
        select(Category)
        .where(Category.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        categories = results.all()
    else:
        categories = session.exec(statement).all() # type: ignore [union-attr]

    return categories

@router.get("/{category_id}", response_model=CategoryRead)
async def read_category_by_id( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        category = await session.get(Category, category_id) # type: ignore [union-attr]
    else:
        category = session.get(Category, category_id) # type: ignore [union-attr]

    # Check if category exists AND belongs to the current user
    if not category or category.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryRead)
async def update_category( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    category_id: int,
    category_in: CategoryBase,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        db_category = await session.get(Category, category_id) # type: ignore [union-attr]
    else:
        db_category = session.get(Category, category_id) # type: ignore [union-attr]

    # Check if category exists AND belongs to the current user
    if not db_category or db_category.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Check if the new name conflicts with another existing category for this user
    if category_in.name != db_category.name:
        statement = (
            select(Category)
            .where(Category.name == category_in.name)
            .where(Category.owner_id == current_user.id)
        )
        if settings.USE_ASYNC_DB:
            results = await session.exec(statement) # type: ignore [union-attr]
            existing_category = results.first()
        else:
            existing_category = session.exec(statement).first() # type: ignore [union-attr]

        if existing_category and existing_category.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{category_in.name}' already exists for this user."
            )

    # Update model fields
    category_data = category_in.model_dump(exclude_unset=True)
    for key, value in category_data.items():
        setattr(db_category, key, value)

    session.add(db_category)

    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_category) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_category) # type: ignore [union-attr]

    return db_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category( # Changed to async def
    *,
    session: DbSession = Depends(get_db_session), # Use unified dependency
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    if settings.USE_ASYNC_DB:
        category = await session.get(Category, category_id) # type: ignore [union-attr]
    else:
        category = session.get(Category, category_id) # type: ignore [union-attr]

    # Check if category exists AND belongs to the current user
    if not category or category.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    # Optional: Check if category is used by any transactions owned by this user before deleting
    # ... (add async/sync logic here if check is enabled) ...

    if settings.USE_ASYNC_DB:
        await session.delete(category) # type: ignore [union-attr]
        await session.commit() # type: ignore [union-attr]
    else:
        session.delete(category) # type: ignore [union-attr]
        session.commit() # type: ignore [union-attr]

    # No response body needed for 204
