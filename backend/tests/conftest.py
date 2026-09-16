import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DATABASE_URL"] = "sqlite:///./test_audit_demo.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import seed as seed_module

TEST_DB_PATH = "./test_audit_demo.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="function")
def test_engine():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def db_session(test_engine, monkeypatch):
    monkeypatch.setattr(seed_module, "engine", test_engine)
    monkeypatch.setattr(seed_module, "Base", Base)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr(seed_module, "SessionLocal", TestSessionLocal)

    seed_module.run_seed()

    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(test_engine, db_session):
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client, username, password):
    resp = client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
