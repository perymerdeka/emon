from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
import enum

# Forward references for relationships
from models.user_model import User

class NotificationType(str, enum.Enum):
    BUDGET_WARNING = "budget_warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    RECURRING_TX_GENERATED = "recurring_tx_generated"
    BILL_REMINDER = "bill_reminder"
    INFO = "info" # General information

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    type: NotificationType = Field(index=True)
    message: str
    is_read: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    related_entity_id: Optional[int] = Field(default=None, description="Optional ID of related entity (e.g., Budget ID, Transaction ID)")
    related_entity_type: Optional[str] = Field(default=None, description="Optional type of related entity (e.g., 'budget', 'transaction')")

    # Relationship back to the user
    user: User = Relationship(back_populates="notifications")
