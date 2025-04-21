from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date
from models.recurring_transaction_model import RecurrenceFrequency # Import Enum

# --- Recurring Transaction DTOs ---

class RecurringTransactionBase(SQLModel):
    description: str
    amount: float = Field(..., gt=0)
    start_date: date
    end_date: Optional[date] = None
    frequency: RecurrenceFrequency
    category_id: int
    is_active: bool = True

class RecurringTransactionCreate(RecurringTransactionBase):
    pass

class RecurringTransactionRead(RecurringTransactionBase):
    id: int
    owner_id: int
    last_created_date: Optional[date] = None # Include tracking date

# Optional: Schema with Category details
# Need to handle potential circular imports if CategoryRead uses this
# from .category_dto import CategoryRead
# class RecurringTransactionReadWithCategory(RecurringTransactionRead):
#     category: Optional["CategoryRead"] = None # Use forward reference

# Remember to call model_rebuild in dto/__init__.py if using forward refs
