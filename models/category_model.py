from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

# Forward references for relationships
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .transaction_model import Transaction # Keep Transaction for List type hint
    from .user_model import User # Add User for relationship type hint


# Enum for Category Type - Keep it here or move to a common place if used elsewhere
class CategoryType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


# --- Category Model ---

# Database model (represents the table)
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True) # Name doesn't need to be globally unique, but unique per user
    type: CategoryType = Field(default=CategoryType.EXPENSE)

    # Foreign Key to User table
    owner_id: int = Field(foreign_key="user.id", index=True)

    # Relationship: Belongs to one User
    owner: "User" = Relationship(back_populates="categories")

    # Relationship: One category can have many transactions
    transactions: List["Transaction"] = Relationship(back_populates="category")

# Schemas (Base, Read, etc.) are now defined in dto/category_dto.py
# Note: We might need constraints later (e.g., unique category name per user)
