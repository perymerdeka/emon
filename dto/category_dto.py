from typing import List, Optional
from sqlmodel import SQLModel

# Import Enum
from models.category_model import CategoryType # Assuming CategoryType stays in models or a common place
# REMOVED direct import of TransactionRead to break circular dependency
# Rely on string forward reference "TransactionRead" in List hint below

# --- Category DTOs ---

# Base schema for validation (used for create/update input)
class CategoryBase(SQLModel):
    name: str
    type: CategoryType = CategoryType.EXPENSE

# Schema for reading data (API output)
class CategoryRead(CategoryBase):
    id: int

# Schema for reading Category with its Transactions (API output)
class CategoryReadWithTransactions(CategoryRead):
    transactions: List["TransactionRead"] = [] # Use string forward reference

# Rebuild models that use forward references
# Needs to be called after all dependent models/schemas are defined.
# If TransactionRead is defined in transaction_dto.py, this might need adjustment
# or be called after both DTO files are processed. For now, place it here.
# Consider a central place or calling it in __init__.py after importing all DTOs.
# CategoryReadWithTransactions.model_rebuild() # Moved to dto/__init__.py
