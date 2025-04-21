from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

# Define relationship imports conditionally for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user_model import User
    from .category_model import Category

class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    year: int = Field(index=True)
    month: int = Field(index=True) # 1-12
    amount: float = Field(gt=0) # Budgeted amount must be positive

    # Foreign Key to User table (each budget belongs to one user)
    owner_id: int = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship() # Define relationship to User

    # Foreign Key to Category table (optional: for category-specific budgets)
    # If category_id is NULL, it represents an overall budget for the month.
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)
    category: Optional["Category"] = Relationship() # Define relationship to Category

    # Add constraint to ensure unique budget per user, year, month, category_id (including NULL)
    # This might require specific handling depending on the DB backend for NULL uniqueness.
    # A composite index might be sufficient for querying.
    # __table_args__ = (
    #     UniqueConstraint("owner_id", "year", "month", "category_id", name="uq_user_budget_period_category"),
    # )
