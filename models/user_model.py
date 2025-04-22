from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

# Define relationship imports conditionally for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # Import related models for type hinting relationships
    from .category_model import Category
    from .transaction_model import Transaction
    from .budget_model import Budget # Assuming Budget exists
    from .recurring_transaction_model import RecurringTransaction # Assuming RecurringTransaction exists
    from .notification_model import Notification # Add Notification

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    is_active: bool = Field(default=True)

    # Relationships: A user can have many categories and transactions
    categories: List["Category"] = Relationship(back_populates="owner")
    transactions: List["Transaction"] = Relationship(back_populates="owner")
    notifications: List["Notification"] = Relationship(back_populates="user") # Add notifications relationship
