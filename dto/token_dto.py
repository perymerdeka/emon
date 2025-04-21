from sqlmodel import SQLModel
from typing import Optional

# --- Token DTOs ---

class Token(SQLModel):
    access_token: str
    refresh_token: str # Add refresh token field
    token_type: str = "bearer"

# Contents of JWT token payload
class TokenPayload(SQLModel):
    sub: Optional[str] = None # Subject (usually user ID or email)
