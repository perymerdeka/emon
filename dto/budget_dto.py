from typing import Optional, Annotated
from sqlmodel import SQLModel, Field
from pydantic import conint # For constraining month value

# --- Budget DTOs ---

# Base schema for common fields
class BudgetBase(SQLModel):
    year: int = Field(..., ge=1900)
    month: Annotated[int, conint(ge=1, le=12)] # Constrained integer 1-12
    amount: float = Field(..., gt=0)
    category_id: Optional[int] = None # Optional category link

# Schema for creating a budget
class BudgetCreate(BudgetBase):
    pass # Inherits all fields from Base

# Schema for reading a budget (includes ID)
class BudgetRead(BudgetBase):
    id: int
    owner_id: int # Include owner_id for clarity/debugging if needed

# Optional: Schema to read budget with category details
# Need to handle circular imports if CategoryRead imports BudgetRead
# from .category_dto import CategoryRead # Avoid direct import here

# class BudgetReadWithCategory(BudgetRead):
#     category: Optional["CategoryRead"] = None # Use forward reference

# Need to call model_rebuild in dto/__init__.py if using forward refs
