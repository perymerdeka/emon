from datetime import date as dt_date, datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

# Import related models
from .category_model import Category, CategoryType # Use relative import

# Forward references for relationships
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user_model import User # Add User for relationship type hint


# --- Transaction Model ---

# Database model (represents the table)
# Note: We are keeping only the core DB model here.
# Schemas (Base, Read, etc.) will be moved to DTOs.
class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float = Field(gt=0) # Transaction amount (always positive)
    type: CategoryType = Field(index=True) # Transaction type, derived from category
    date: dt_date = Field(index=True) # Date of transaction
    description: Optional[str] = Field(default=None) # Optional description
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False) # Record creation time
    updated_at: Optional[datetime] = Field(default=None) # Last update time

    # Foreign Key to Category table
    category_id: int = Field(foreign_key="category.id", index=True)

    # Relationship: Belongs to one Category
    category: Category = Relationship(back_populates="transactions")

    # Foreign Key to User table
    owner_id: int = Field(foreign_key="user.id", index=True)

    # Relationship: Belongs to one User
    owner: "User" = Relationship(back_populates="transactions")


# Schemas (Base, Read, etc.) are now defined in dto/transaction_dto.py
