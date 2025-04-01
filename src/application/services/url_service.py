import random
import string
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from ..models.models import URL
from ..schemas.url import URLCreate, URLUpdate
from ..core.config import settings
import redis
import json

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def generate_short_code(length: int = 6) -> str:
    """Generate a random short code for the URL."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_url(db: Session, url: URLCreate, user_id: Optional[int] = None) -> URL:
    """Create a new URL with a short code."""
    short_code = url.custom_alias or generate_short_code()
    
    original_url = str(url.original_url).rstrip('/')
    
    db_url = URL(
        original_url=original_url,
        short_code=short_code,
        custom_alias=url.custom_alias,
        expires_at=url.expires_at,
        owner_id=user_id,
        created_at=datetime.utcnow(),
        access_count=0
    )
    
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    cache_key = f"url:{short_code}"
    redis_client.setex(
        cache_key,
        3600,
        json.dumps({
            "original_url": original_url,
            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
            "short_code": short_code,
            "custom_alias": url.custom_alias,
            "owner_id": user_id,
            "access_count": 0,
            "last_accessed_at": None,
            "created_at": datetime.utcnow().isoformat()
        })
    )
    
    return db_url

def get_url_by_short_code(db: Session, short_code: str) -> Optional[URL]:
    """Get URL by short code, first checking Redis cache."""
    cache_key = f"url:{short_code}"
    cached_url = redis_client.get(cache_key)
    
    if cached_url:
        try:
            cached_data = json.loads(cached_url)
            required_fields = ["original_url", "short_code", "expires_at", "owner_id", "access_count", "last_accessed_at", "created_at"]
            if not all(key in cached_data for key in required_fields):
                
                url = db.query(URL).filter(URL.short_code == short_code).first()
                if url:
                    redis_client.setex(
                        cache_key,
                        3600,
                        json.dumps({
                            "original_url": url.original_url,
                            "expires_at": url.expires_at.isoformat() if url.expires_at else None,
                            "short_code": url.short_code,
                            "custom_alias": url.custom_alias,
                            "owner_id": url.owner_id,
                            "access_count": url.access_count,
                            "last_accessed_at": url.last_accessed_at.isoformat() if url.last_accessed_at else None,
                            "created_at": url.created_at.isoformat()
                        })
                    )
                return url
            
            return URL(
                id=1,
                original_url=cached_data["original_url"],
                short_code=cached_data["short_code"],
                custom_alias=cached_data.get("custom_alias"),
                expires_at=datetime.fromisoformat(cached_data["expires_at"]) if cached_data["expires_at"] else None,
                owner_id=cached_data["owner_id"],
                access_count=cached_data["access_count"],
                last_accessed_at=datetime.fromisoformat(cached_data["last_accessed_at"]) if cached_data["last_accessed_at"] else None,
                created_at=datetime.fromisoformat(cached_data["created_at"])
            )
        except (json.JSONDecodeError, ValueError):
            url = db.query(URL).filter(URL.short_code == short_code).first()
            if url:
                redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps({
                        "original_url": url.original_url,
                        "expires_at": url.expires_at.isoformat() if url.expires_at else None,
                        "short_code": url.short_code,
                        "custom_alias": url.custom_alias,
                        "owner_id": url.owner_id,
                        "access_count": url.access_count,
                        "last_accessed_at": url.last_accessed_at.isoformat() if url.last_accessed_at else None,
                        "created_at": url.created_at.isoformat()
                    })
                )
            return url
    
    url = db.query(URL).filter(URL.short_code == short_code).first()
    
    if url:
        redis_client.setex(
            cache_key,
            3600,
            json.dumps({
                "original_url": url.original_url,
                "expires_at": url.expires_at.isoformat() if url.expires_at else None,
                "short_code": url.short_code,
                "custom_alias": url.custom_alias,
                "owner_id": url.owner_id,
                "access_count": url.access_count,
                "last_accessed_at": url.last_accessed_at.isoformat() if url.last_accessed_at else None,
                "created_at": url.created_at.isoformat()
            })
        )
    
    return url

def update_url(db: Session, short_code: str, url_update: URLUpdate) -> Optional[URL]:
    """Update URL details."""
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if not db_url:
        return None
    
    update_data = url_update.dict(exclude_unset=True)
    if "original_url" in update_data:
        update_data["original_url"] = str(update_data["original_url"]).rstrip('/')
    
    for field, value in update_data.items():
        setattr(db_url, field, value)
    
    db.commit()
    db.refresh(db_url)
    
    redis_client.delete(f"url:{short_code}")
    
    return db_url

def delete_url(db: Session, short_code: str) -> bool:
    """Delete URL by short code."""
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if not db_url:
        return False
    
    db.delete(db_url)
    db.commit()
    
    redis_client.delete(f"url:{short_code}")
    
    return True

def get_url_stats(db: Session, short_code: str) -> Optional[URL]:
    """Get URL statistics."""
    return get_url_by_short_code(db, short_code)

def search_url_by_original(db: Session, original_url: str, user_id: Optional[int] = None) -> Optional[URL]:
    """Search URL by original URL."""
    original_url = original_url.rstrip('/')
    query = db.query(URL).filter(URL.original_url == original_url)
    if user_id is not None:
        query = query.filter(URL.owner_id == user_id)
    return query.first()

def increment_access_count(db: Session, short_code: str) -> None:
    """Increment access count and update last accessed time."""
    db_url = db.query(URL).filter(URL.short_code == short_code).first()
    if db_url:
        db_url.access_count += 1
        db_url.last_accessed_at = datetime.utcnow()
        db.commit()
        
        redis_client.delete(f"url:{short_code}") 