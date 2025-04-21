from sqlmodel import SQLModel
from pydantic import EmailStr # Use EmailStr for validation

# --- User DTOs ---

# Properties to receive via API on creation
class UserCreate(SQLModel):
    email: EmailStr
    password: str # Plain password on creation

# Properties to return via API (never passwords)
class UserRead(SQLModel):
    id: int
    email: EmailStr
    is_active: bool

# Properties stored in DB (never return hashed_password)
# Not typically used as a DTO, but useful for internal representation
class UserInDB(SQLModel):
    id: int
    email: EmailStr
    hashed_password: str
    is_active: bool

# Schema for updating user password
class UserPasswordUpdate(SQLModel):
    current_password: str
    new_password: str
