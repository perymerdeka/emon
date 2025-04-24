import pytest
from fastapi import status, HTTPException, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Assuming your FastAPI app instance is named 'app' in 'main.py'
# Adjust the import path if necessary
from core import create_app as app 
from dto import AIConsultationRequest, AIConsultationResponse
from models import User
# Assuming your auth dependency function is named 'get_current_active_user'
# Adjust the import path if necessary
from middlewares.auth import get_current_active_user 

client = TestClient(app)

@pytest.fixture
def mock_user():
    # Create a mock User object
    return User(id=1, email="test@example.com", is_active=True, hashed_password="fakehashedpassword")

@pytest.fixture
def mock_ai_request():
    # Create a mock request object
    return AIConsultationRequest(
        question="How can I improve my savings?",
        provider="openai", # Example provider
        financial_context=False
    )

@pytest.fixture
def mock_ai_response(mock_ai_request: AIConsultationRequest): # Add request fixture dependency
    # Create a mock response object
    return AIConsultationResponse(
        question=mock_ai_request.question, # Add the missing question field
        answer="Consider setting up automatic transfers to a savings account.",
        provider="openai",
        cost=0.02 # Example cost
    )

@pytest.mark.asyncio
async def test_consult_ai_success(app: FastAPI, client: TestClient, mock_user, mock_ai_request, mock_ai_response): # Add app and client fixtures
    """Test successful AI consultation."""
    # Patch the service function
    with patch("routers.ai_consultation.get_ai_consultation", 
              new_callable=AsyncMock, 
              return_value=mock_ai_response) as mock_service_call:
        
        # Override the authentication dependency to return the mock user
        # Use the app fixture for overrides
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        # Make the API call
        response = client.post(
            "/ai-consultation/", # Ensure this matches your router prefix if any
            json=mock_ai_request.dict()
        )
        
        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_ai_response.dict()
        mock_service_call.assert_awaited_once_with(mock_ai_request)
        
        # Clean up dependency override
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_consult_ai_unauthenticated(app: FastAPI, client: TestClient, mock_ai_request): # Add app and client fixtures
    """Test AI consultation endpoint without authentication."""
    # Ensure no user is returned by the dependency override
    app.dependency_overrides[get_current_active_user] = lambda: None # Or raise HTTPException directly

    # Make the API call
    response = client.post(
        "/ai-consultation/",
        json=mock_ai_request.dict()
    )
    
    # Assertions - Expecting 401 Unauthorized
    # Note: The exact status code might depend on how get_current_active_user handles failure
    # If it raises HTTPException(status.HTTP_401_UNAUTHORIZED), this is correct.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED 
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_consult_ai_service_http_exception(app: FastAPI, client: TestClient, mock_user, mock_ai_request): # Add app and client fixtures
    """Test AI consultation when the service raises an HTTPException."""
    # Patch the service function to raise an HTTPException
    with patch("routers.ai_consultation.get_ai_consultation", 
              new_callable=AsyncMock, 
              side_effect=HTTPException(
                  status_code=status.HTTP_400_BAD_REQUEST, 
                  detail="Invalid provider"
              )) as mock_service_call:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.post(
            "/ai-consultation/",
            json=mock_ai_request.dict()
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"detail": "Invalid provider"}
        mock_service_call.assert_awaited_once_with(mock_ai_request)
        
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_consult_ai_service_unexpected_error(app: FastAPI, client: TestClient, mock_user, mock_ai_request): # Add app and client fixtures
    """Test AI consultation when the service raises an unexpected Exception."""
    # Patch the service function to raise a generic Exception
    with patch("routers.ai_consultation.get_ai_consultation", 
              new_callable=AsyncMock, 
              side_effect=Exception("Something went wrong")) as mock_service_call:
        
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        
        response = client.post(
            "/ai-consultation/",
            json=mock_ai_request.dict()
        )
        
        # The endpoint should catch this and return a 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "An error occurred while consulting the AI service."}
        mock_service_call.assert_awaited_once_with(mock_ai_request)
        
        app.dependency_overrides.clear()
