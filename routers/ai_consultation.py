from fastapi import APIRouter, Depends, HTTPException, status

from models import User
from dto import AIConsultationRequest, AIConsultationResponse
from middlewares.auth import get_current_active_user
from services.ai_consultation_service import get_ai_consultation

router = APIRouter()

@router.post("/", response_model=AIConsultationResponse)
async def consult_ai(
    *,
    request_data: AIConsultationRequest,
    current_user: User = Depends(get_current_active_user) # Ensure user is logged in
):
    """
    Endpoint for users to ask financial questions to a selected AI provider.
    """
    # Optional: Add logic here to fetch user's financial summary/context
    # if request_data.financial_context is used, ensuring privacy.

    # Call the service function to handle the request
    try:
        response = await get_ai_consultation(request_data)
        return response
    except HTTPException as e:
        # Re-raise HTTPExceptions from the service
        raise e
    except Exception as e:
        # Catch unexpected errors from the service
        print(f"Unexpected error during AI consultation: {e}") # Log error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while consulting the AI service."
        )
