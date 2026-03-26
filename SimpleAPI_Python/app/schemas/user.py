import uuid
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    # Field(...) means it's mandatory to have a value when initialized
    username: str = Field(..., min_length=4, max_length=20)
    password: str = Field(..., min_length=8, max_length=32)


class UserRegistrationResponse(BaseModel):
    user_id: uuid.UUID
    access_token: str
    refresh_token: str
    expires_in: int
