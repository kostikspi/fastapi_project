from pydantic import BaseModel, AnyHttpUrl
from datetime import datetime
from typing import Optional

class URLBase(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class URLCreate(URLBase):
    pass

class URLUpdate(BaseModel):
    original_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class URLInDB(URLBase):
    id: int
    short_code: str
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    access_count: int
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

class URLStats(URLInDB):
    pass

class URLResponse(BaseModel):
    short_url: str
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None 