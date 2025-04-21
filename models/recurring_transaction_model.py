from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import date
from enum import Enum

# Define relationship imports conditionally for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .user_model import User
    from .category_model import Category

class RecurrenceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class RecurringTransaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str # Description for the recurring rule
    amount: float = Field(gt=0) # Amount for each occurrence
    start_date: date = Field(index=True) # Date the recurrence starts
    end_date: Optional[date] = Field(default=None, index=True) # Optional date the recurrence ends
    frequency: RecurrenceFrequency = Field(index=True) # How often it recurs
    last_created_date: Optional[date] = Field(default=None, index=True) # Tracks the date the last transaction was created

    # Foreign Key to User table
    owner_id: int = Field(foreign_key="user.id", index=True)
    owner: "User" = Relationship()

    # Foreign Key to Category table
    category_id: int = Field(foreign_key="category.id", index=True)
    category: "Category" = Relationship()

    is_active: bool = Field(default=True) # To easily enable/disable recurrence
