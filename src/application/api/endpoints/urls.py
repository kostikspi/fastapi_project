from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from ...db.session import get_db
from ...schemas.url import URLCreate, URLUpdate, URLResponse, URLStats
from ...services import url_service
from ...services import user_service
from ...core.security import get_current_user
from ...schemas.user import User
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.post("/shorten", response_model=URLResponse)
def create_short_url(
    url: URLCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Create a new short URL."""
    
    existing_url = url_service.search_url_by_original(db, str(url.original_url))
    if existing_url and existing_url.owner_id == current_user.id:
        return URLResponse(
            short_url=f"/{existing_url.short_code}",
            original_url=existing_url.original_url,
            custom_alias=existing_url.custom_alias,
            expires_at=existing_url.expires_at
        )
    
    if url.custom_alias:
        existing_url = url_service.get_url_by_short_code(db, url.custom_alias)
        if existing_url:
            raise HTTPException(
                status_code=400,
                detail="Custom alias already taken"
            )
    
    db_url = url_service.create_url(db, url, current_user.id)
    return URLResponse(
        short_url=f"/{db_url.short_code}",
        original_url=db_url.original_url,
        custom_alias=db_url.custom_alias,
        expires_at=db_url.expires_at
    )

@router.get("/search")
def search_url(
    original_url: str = Query(..., description="Original URL to search for"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Search for a URL by its original URL."""
    original_url = original_url.rstrip('/')
    url = url_service.search_url_by_original(db, original_url, current_user.id if current_user else None)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return URLResponse(
        short_url=f"/{url.short_code}",
        original_url=url.original_url,
        custom_alias=url.custom_alias,
        expires_at=url.expires_at
    )

@router.get("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """Redirect to the original URL."""
    url = url_service.get_url_by_short_code(db, short_code)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    current_time = datetime.now(timezone.utc)
    if url.expires_at and url.expires_at.replace(tzinfo=timezone.utc) < current_time:
        raise HTTPException(status_code=410, detail="URL has expired")
    
    url_service.increment_access_count(db, short_code)
    return RedirectResponse(url=url.original_url, status_code=307)

@router.delete("/{short_code}")
def delete_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a URL (requires authentication)."""
    url = url_service.get_url_by_short_code(db, short_code)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if url.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = url_service.delete_url(db, short_code)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete URL")
    
    return {"message": "URL deleted successfully"}

@router.put("/{short_code}", response_model=URLResponse)
def update_url(
    short_code: str,
    url_update: URLUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a URL (requires authentication)."""
    url = url_service.get_url_by_short_code(db, short_code)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if url.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    updated_url = url_service.update_url(db, short_code, url_update)
    if not updated_url:
        raise HTTPException(status_code=500, detail="Failed to update URL")
    
    return URLResponse(
        short_url=f"/{updated_url.short_code}",
        original_url=updated_url.original_url,
        custom_alias=updated_url.custom_alias,
        expires_at=updated_url.expires_at
    )

@router.get("/{short_code}/stats", response_model=URLStats)
def get_url_stats(short_code: str, db: Session = Depends(get_db)):
    """Get statistics for a URL."""
    url = url_service.get_url_stats(db, short_code)
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    return URLStats(
        id=url.id,
        original_url=url.original_url,
        short_code=url.short_code,
        custom_alias=url.custom_alias,
        created_at=url.created_at,
        expires_at=url.expires_at,
        last_accessed_at=url.last_accessed_at,
        access_count=url.access_count,
        owner_id=url.owner_id
    ) 