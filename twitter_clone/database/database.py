from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


POSTGRES_URL = f'postgresql+asyncpg://admin:admin@localhost:5432/twitter_db'

engine = create_async_engine(POSTGRES_URL, echo=True)

async_session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
session = async_session()

Base = declarative_base()
