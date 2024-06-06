import pytest

from fastapi.testclient import TestClient

from testcontainers.postgres import PostgresContainer

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from main import app, get_db_async_session
from database import Base

from utility.create_data import create_data


@pytest.fixture(scope="session")
async def db_session():
    with PostgresContainer("postgres:16.2") as postgres:
        engine = create_async_engine(postgres.get_connection_url(driver="asyncpg"))
        AsyncTestSession = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await create_data(
            AsyncSessionLocal=AsyncTestSession,
            users_count=5,
            subscribe_count=5,
            tweets_count=5,
            images_count=5,
            likes_count=5
        )

        yield AsyncTestSession


@pytest.fixture(scope="session")
async def client(db_session):
    async def override_get_db():
        try:
            db: AsyncSession = db_session()
            yield db
        finally:
            await db.aclose()

    app.dependency_overrides[get_db_async_session] = override_get_db

    yield TestClient(app)





