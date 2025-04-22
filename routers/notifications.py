from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional, Union

from models import User, Notification
from dto import NotificationRead, NotificationUpdate
from middlewares.auth import get_current_active_user
from core.db import get_db_session
from core.config import settings

router = APIRouter()

# Type hint for the session dependency result
DbSession = Union[Session, AsyncSession]

@router.get("/", response_model=List[NotificationRead])
async def read_notifications(
    *,
    session: DbSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, le=200), # Limit results, max 200
    is_read: Optional[bool] = None # Filter by read status
):
    """
    Retrieve notifications for the current user, optionally filtered by read status.
    """
    statement = select(Notification).where(Notification.user_id == current_user.id)
    if is_read is not None:
        statement = statement.where(Notification.is_read == is_read)
    statement = statement.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        notifications = results.all()
    else:
        notifications = session.exec(statement).all() # type: ignore [union-attr]
    return notifications

@router.patch("/{notification_id}", response_model=NotificationRead)
async def mark_notification_as_read(
    *,
    session: DbSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
    notification_id: int,
    notification_update: NotificationUpdate # Expect {"is_read": true}
):
    """
    Mark a specific notification as read or unread.
    """
    if settings.USE_ASYNC_DB:
        db_notification = await session.get(Notification, notification_id) # type: ignore [union-attr]
    else:
        db_notification = session.get(Notification, notification_id) # type: ignore [union-attr]

    if not db_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if db_notification.user_id != current_user.id:
        # Do not reveal that the notification exists but belongs to another user
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    db_notification.is_read = notification_update.is_read
    session.add(db_notification)

    if settings.USE_ASYNC_DB:
        await session.commit() # type: ignore [union-attr]
        await session.refresh(db_notification) # type: ignore [union-attr]
    else:
        session.commit() # type: ignore [union-attr]
        session.refresh(db_notification) # type: ignore [union-attr]

    return db_notification

@router.post("/mark-all-read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    *,
    session: DbSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark all unread notifications for the current user as read.
    """
    statement = select(Notification).where(Notification.user_id == current_user.id).where(Notification.is_read == False)

    if settings.USE_ASYNC_DB:
        results = await session.exec(statement) # type: ignore [union-attr]
        unread_notifications = results.all()
        if not unread_notifications:
            return # Nothing to mark
        for notification in unread_notifications:
            notification.is_read = True
            session.add(notification)
        await session.commit() # type: ignore [union-attr]
    else:
        unread_notifications = session.exec(statement).all() # type: ignore [union-attr]
        if not unread_notifications:
            return # Nothing to mark
        for notification in unread_notifications:
            notification.is_read = True
            session.add(notification)
        session.commit() # type: ignore [union-attr]

    # No content response for successful bulk update
