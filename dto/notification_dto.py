from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from models.notification_model import NotificationType # Import the enum

# Base model (can be used for updates if needed)
class NotificationBase(SQLModel):
    is_read: Optional[bool] = None

# Model for reading notifications
class NotificationRead(SQLModel):
    id: int
    type: NotificationType
    message: str
    is_read: bool
    created_at: datetime
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None

# Model for updating the read status (could use NotificationBase too)
class NotificationUpdate(SQLModel):
    is_read: bool
