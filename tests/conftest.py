import os
import sys
from pathlib import Path
import uuid

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Generator

from src.application.core.config import settings
from src.application.db.session import get_db

if os.getenv("TESTING"):
    settings.POSTGRES_SERVER = "db"
    settings.POSTGRES_USER = "postgres"
    settings.POSTGRES_PASSWORD = "postgres"
    settings.POSTGRES_DB = "url_shortener_test"
    settings.REDIS_HOST = "redis"
    settings.REDIS_PORT = 6379
else:
    settings.POSTGRES_SERVER = ":memory:"
    settings.POSTGRES_DB = "test.db"

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from src.application.db.base_class import Base

from src.application.main import app

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    from src.application.models.models import URL, User
    session.query(URL).delete()
    session.query(User).delete()
    session.commit()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db):
    from src.application.models.models import User
    from src.application.services.user_service import get_password_hash
    
    db.query(User).filter(User.email == "test@example.com").delete()
    db.commit()
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_token(test_user):
    from src.application.core.security import create_access_token
    return create_access_token(data={"sub": str(test_user.id)})

@pytest.fixture(scope="function")
def authorized_client(client, test_token) -> Generator:
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_token}"
    }
    return client

@pytest.fixture(scope="function")
def test_url(db, test_user):
    from src.application.models.models import URL
    from datetime import datetime
    
    unique_code = f"test-{uuid.uuid4().hex[:8]}"
    
    db.query(URL).filter(URL.short_code == unique_code).delete()
    db.commit()
    
    url = URL(
        original_url="https://example.com",
        short_code=unique_code,
        owner_id=test_user.id,
        created_at=datetime.utcnow(),
        access_count=0
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def test_url_data():
    unique_alias = f"test-alias-{uuid.uuid4().hex[:8]}"
    return {
        "original_url": "https://example.com",
        "custom_alias": unique_alias,
        "expires_at": None
    } 