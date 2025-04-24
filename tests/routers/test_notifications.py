import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from sqlmodel import select
from fastapi import FastAPI # Import FastAPI for app fixture type hint

from core import create_app as app_factory # Rename original import
from middlewares.auth import get_current_active_user
from models import User, Notification, NotificationType # Import NotificationType
from dto import NotificationRead, NotificationUpdate
from core.db import get_db_session
from core import create_app as app

client = TestClient(app)

@pytest.fixture
def mock_user():
    return User(id=1, email="test@example.com", is_active=True)

@pytest.fixture
def mock_notification():
    return Notification(
        id=1,
        user_id=1,
        title="Test Notification",
        message="This is a test",
        is_read=False
    )

@pytest.fixture
def mock_notification_read():
    return NotificationRead(
        id=1,
        # user_id=1, # user_id is not part of NotificationRead DTO
        type=NotificationType.INFO, # Add missing type field
        title="Test Notification",
        message="This is a test",
        is_read=False,
        created_at="2023-01-01T00:00:00"
    )

@pytest.fixture
def mock_notification_update():
    return NotificationUpdate(is_read=True)

@pytest.mark.asyncio
async def test_read_notifications(app: FastAPI, client: TestClient, mock_user, mock_notification_read): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.exec", 
              new_callable=AsyncMock,
              return_value=AsyncMock(all=lambda: [mock_notification_read])) as mock_exec:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.get("/notifications/") # No await needed
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1
        assert response.json()[0]["title"] == "Test Notification"
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_read_notifications_filter_read(app: FastAPI, client: TestClient, mock_user, mock_notification_read): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.exec", 
              new_callable=AsyncMock,
              return_value=AsyncMock(all=lambda: [mock_notification_read])) as mock_exec:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.get("/notifications/?is_read=false") # No await needed
        
        assert response.status_code == status.HTTP_200_OK
        mock_exec.assert_called_once()
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mark_notification_as_read(app: FastAPI, client: TestClient, mock_user, mock_notification, mock_notification_update): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.get", 
              new_callable=AsyncMock,
              return_value=mock_notification) as mock_get:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.patch( # No await needed
            "/notifications/1",
            json=mock_notification_update.dict()
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_read"] is True
        mock_get.assert_awaited_once_with(Notification, 1)
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mark_notification_not_found(app: FastAPI, client: TestClient, mock_user, mock_notification_update): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.get", 
              new_callable=AsyncMock,
              return_value=None) as mock_get:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.patch( # No await needed
            "/notifications/999",
            json=mock_notification_update.dict()
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_get.assert_awaited_once_with(Notification, 999)
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mark_all_notifications_read(app: FastAPI, client: TestClient, mock_user, mock_notification): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.exec", 
              new_callable=AsyncMock,
              return_value=AsyncMock(all=lambda: [mock_notification])) as mock_exec:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.post("/notifications/mark-all-read") # No await needed
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_exec.assert_called_once()
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mark_all_notifications_read_no_unread(app: FastAPI, client: TestClient, mock_user): # Add app and client
    with patch("sqlmodel.ext.asyncio.session.AsyncSession.exec", 
              new_callable=AsyncMock,
              return_value=AsyncMock(all=lambda: [])) as mock_exec:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.post("/notifications/mark-all-read") # No await needed
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_exec.assert_called_once()
        
        app.dependency_overrides.clear()
