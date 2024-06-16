import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from database import Base
from main import app, get_db_async_session
from utility.create_data import create_data

postgres = PostgresContainer(image="postgres:16.2", driver="asyncpg")
postgres.start()

engine = create_async_engine(postgres.get_connection_url(), poolclass=NullPool)
AsyncTestSession = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
async def db_session():
    yield AsyncTestSession
    postgres.stop()


@pytest.fixture(scope="session")
async def client(db_session):
    async def override_get_db():
        db: AsyncSession = db_session()
        try:
            yield db
        finally:
            await db.aclose()

    app.dependency_overrides[get_db_async_session] = override_get_db
    yield TestClient(app)


@pytest.fixture(scope="session", autouse=True)
async def filling_tables(db_session):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await create_data(async_session_local=db_session, users_count=1)
