from sqlmodel import SQLModel
from enum import Enum
from pydantic import Field
from typing import Optional # Added Optional

class AIModelProvider(str, Enum):
    OPENAI = "openai" # ChatGPT
    GEMINI = "gemini"
    DEEPSEEK = "deepseek" # Placeholder
    MISTRAL = "mistral" # Placeholder

class AIConsultationRequest(SQLModel):
    question: str = Field(..., min_length=10) # Require a minimum question length
    provider: AIModelProvider = Field(..., description="The AI provider to consult")
    # Optional: Add context field if you want to send user's financial summary (requires careful handling)
    # financial_context: Optional[dict] = None

class AIConsultationResponse(SQLModel):
    provider: AIModelProvider
    question: str
    answer: str
    disclaimer: str = "AI responses are for informational purposes only and do not constitute financial advice. Consult with a qualified professional before making financial decisions."
