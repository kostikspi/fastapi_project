import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
import json

from src.application.services.url_service import (
    generate_short_code,
    create_url,
    get_url_by_short_code,
    update_url,
    delete_url,
    increment_access_count
)
from src.application.schemas.url import URLCreate, URLUpdate
from src.application.models.models import URL

def test_generate_short_code():
    """Test short code generation."""
    code = generate_short_code()
    assert len(code) == 6
    assert code.isalnum()

def test_create_url(db: Session):
    """Test URL creation."""
    url_data = URLCreate(
        original_url="https://example.com",
        custom_alias="test-alias"
    )
    
    url = create_url(db, url_data)
    
    assert url.original_url == "https://example.com"
    assert url.short_code == "test-alias"
    assert url.custom_alias == "test-alias"
    assert url.access_count == 0
    assert url.created_at is not None

def test_get_url_by_short_code(db: Session):
    """Test URL retrieval by short code."""
    url_data = URLCreate(original_url="https://example.com")
    created_url = create_url(db, url_data)
    
    retrieved_url = get_url_by_short_code(db, created_url.short_code)
    
    assert retrieved_url is not None
    assert retrieved_url.original_url == created_url.original_url
    assert retrieved_url.short_code == created_url.short_code

def test_update_url(db: Session):
    """Test URL update."""
    url_data = URLCreate(original_url="https://example.com")
    created_url = create_url(db, url_data)
    
    update_data = URLUpdate(original_url="https://updated-example.com")
    updated_url = update_url(db, created_url.short_code, update_data)
    
    assert updated_url is not None
    assert updated_url.original_url == "https://updated-example.com"
    assert updated_url.short_code == created_url.short_code

def test_delete_url(db: Session):
    """Test URL deletion."""
    url_data = URLCreate(original_url="https://example.com")
    created_url = create_url(db, url_data)
    
    success = delete_url(db, created_url.short_code)
    
    assert success is True
    deleted_url = get_url_by_short_code(db, created_url.short_code)
    assert deleted_url is None

def test_increment_access_count(db: Session):
    """Test access count increment."""
    url_data = URLCreate(original_url="https://example.com")
    created_url = create_url(db, url_data)
    
    increment_access_count(db, created_url.short_code)
    
    updated_url = get_url_by_short_code(db, created_url.short_code)
    assert updated_url.access_count == 1
    assert updated_url.last_accessed_at is not None

@patch('src.application.services.url_service.redis_client')
def test_get_url_by_short_code_with_cache(mock_redis):
    """Test URL retrieval with Redis cache."""
    mock_redis.get.return_value = json.dumps({
        "original_url": "https://example.com",
        "short_code": "test123",
        "expires_at": None,
        "owner_id": 1,
        "access_count": 0,
        "last_accessed_at": None,
        "created_at": datetime.utcnow().isoformat(),
        "custom_alias": None
    })

    mock_db = Mock(spec=Session)

    url = get_url_by_short_code(mock_db, "test123")
    assert url.original_url == "https://example.com"
    assert url.short_code == "test123"
    assert url.owner_id == 1
    assert url.access_count == 0 