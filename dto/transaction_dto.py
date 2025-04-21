from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# Import necessary types/models/DTOs
from models.category_model import CategoryType # Assuming CategoryType stays in models
# REMOVED direct import of CategoryRead to break circular dependency
# Rely on string forward reference "CategoryRead" in type hint below

# --- Transaction DTOs ---

# Base schema for validation (used for create/update input)
class TransactionBase(SQLModel):
    amount: float = Field(gt=0, description="Transaction amount must be greater than 0")
    date: date
    description: Optional[str] = None
    category_id: int # Use category_id for input, not the full object

# Schema for reading data (API output)
class TransactionRead(TransactionBase):
    id: int
    type: CategoryType # Include type derived from category
    created_at: datetime
    updated_at: Optional[datetime]

# Schema for reading Transaction with its Category details (API output)
class TransactionReadWithCategory(TransactionRead):
    category: "CategoryRead" # Use string forward reference

# Rebuild models that use forward references
# TransactionReadWithCategory.model_rebuild() # Moved to dto/__init__.py
