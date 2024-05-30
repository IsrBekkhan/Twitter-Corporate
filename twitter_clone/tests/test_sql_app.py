import pytest

from fastapi.testclient import TestClient
from fastapi import FastAPI
from httpx import AsyncClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from database import Base
from main import app, get_db_async_session


# sqlalchemy_database_url = "postgresql+asyncpg://"
#
# engine = create_engine(sqlalchemy_database_url, poolclass=StaticPool)
# TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
#
# Base.metadata.create_all(bind=engine)
#
#
# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()
#
#
# app.dependency_overrides[get_db_async_session] = override_get_db
#
# client = TestClient(app)


@pytest.fixture
def client() -> TestClient:
    sqlalchemy_database_url = "postgresql+asyncpg://"

    engine = create_engine(sqlalchemy_database_url)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_async_session] = override_get_db

    yield TestClient(app)


# @pytest.mark.anyio
# async def test_just_test():
#     async with AsyncClient(app=app, base_url="http://127.0.0.1:5000") as as_cl:
#         response = await as_cl.get("/api/tweets", headers={"api-key": "test"})
#     # response = client.get("/api/tweets", headers={"api-key": "test"})
#     assert response.status_code == 200


def test_just_test(client: TestClient):
    response = client.get("/api/tweets", headers={"api-key": "test"})
    assert response.status_code == 200




