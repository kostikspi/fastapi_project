import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Generator

def test_create_short_url(authorized_client: TestClient, test_url_data):
    """Test URL shortening endpoint."""
    response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    print(f"Response content: {response.content}")
    assert response.status_code == 200
    data = response.json()
    assert data["short_url"] == f"/{test_url_data['custom_alias']}"
    assert data["original_url"] == test_url_data["original_url"]
    assert data["custom_alias"] == test_url_data["custom_alias"]

    invalid_data = {**test_url_data, "original_url": "not-a-url"}
    response = authorized_client.post("/api/v1/links/shorten", json=invalid_data)
    assert response.status_code == 400

def test_create_short_url_duplicate_alias(authorized_client: TestClient, test_url_data):
    """Test URL shortening with duplicate alias."""
    response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    assert response.status_code == 200
    
    duplicate_data = {
        **test_url_data,
        "original_url": "https://another-example.com"
    }
    response = authorized_client.post("/api/v1/links/shorten", json=duplicate_data)
    assert response.status_code == 400
    assert "Custom alias already taken" in response.json()["detail"]

def test_redirect_to_url(authorized_client: TestClient, test_url_data):
    """Test URL redirection."""
    create_response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    short_code = test_url_data["custom_alias"]
    
    response = authorized_client.get(f"/api/v1/links/{short_code}", allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == test_url_data["original_url"]

    response = authorized_client.get("/api/v1/links/non-existent")
    assert response.status_code == 404

def test_redirect_to_expired_url(authorized_client: TestClient):
    """Test redirection to expired URL."""
    url_data = {
        "original_url": "https://example.com",
        "custom_alias": "expired-test",
        "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
    }
    authorized_client.post("/api/v1/links/shorten", json=url_data)
    
    response = authorized_client.get("/api/v1/links/expired-test")
    assert response.status_code == 410
    assert "URL has expired" in response.json()["detail"]

def test_delete_url(authorized_client: TestClient, test_url_data):
    """Test URL deletion."""
    response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    assert response.status_code == 200
    
    response = authorized_client.delete(f"/api/v1/links/{test_url_data['custom_alias']}")
    assert response.status_code == 200
    
    redirect_response = authorized_client.get(f"/api/v1/links/{test_url_data['custom_alias']}")
    assert redirect_response.status_code == 404

    response = authorized_client.delete("/api/v1/links/non-existent")
    assert response.status_code == 404

def test_update_url(authorized_client: TestClient, test_url_data):
    """Test URL update."""
    response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    assert response.status_code == 200
    
    update_data = {
        "original_url": "https://updated-example.com"
    }
    response = authorized_client.put(f"/api/v1/links/{test_url_data['custom_alias']}", json=update_data)
    assert response.status_code == 200
    
    redirect_response = authorized_client.get(f"/api/v1/links/{test_url_data['custom_alias']}", follow_redirects=True)
    assert redirect_response.status_code == 200

    response = authorized_client.put("/api/v1/links/non-existent", json=update_data)
    assert response.status_code == 404

def test_get_url_stats(authorized_client: TestClient, test_url_data):
    """Test URL statistics endpoint."""
    authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    
    response = authorized_client.get(f"/api/v1/links/{test_url_data['custom_alias']}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == test_url_data["original_url"]
    assert data["short_code"] == test_url_data["custom_alias"]
    assert data["access_count"] == 0

    response = authorized_client.get("/api/v1/links/non-existent/stats")
    assert response.status_code == 404

def test_search_url(authorized_client: TestClient, test_url_data, db):
    """Test URL search endpoint."""
    create_response = authorized_client.post("/api/v1/links/shorten", json=test_url_data)
    assert create_response.status_code == 200, f"Failed to create URL: {create_response.content}"
    
    from src.application.models.models import URL
    urls = db.query(URL).all()
    print(f"Database URLs: {[{'original_url': url.original_url, 'owner_id': url.owner_id} for url in urls]}")
    
    response = authorized_client.get(f"/api/v1/links/search?original_url={test_url_data['original_url']}")
    print(f"Search response: {response.content}")
    assert response.status_code == 200, f"Failed to search URL: {response.content}"
    data = response.json()
    assert data["short_url"] == f"/{test_url_data['custom_alias']}"
    assert data["original_url"] == test_url_data["original_url"]

    response = authorized_client.get("/api/v1/links/search?original_url=https://non-existent.com")
    assert response.status_code == 404 