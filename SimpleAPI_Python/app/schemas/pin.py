from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class PinCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    body: Optional[str] = None
    image_link: Optional[str] = Field(None, max_length=2048)


class PinResponse(BaseModel):
    pin_id: int
    author: str
    title: str
    body: Optional[str] = None
    image_link: Optional[str] = None
    created_at: datetime


class PinListResponse(BaseModel):
    pins: List[PinResponse]
