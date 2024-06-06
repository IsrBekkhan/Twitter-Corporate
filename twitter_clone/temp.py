import asyncio
from utility.create_data import create_data
from database import engine, Base, AsyncSessionLocal
from models.like import Like
from models.user import User
from models.tweet import Tweet
from models.like import Like


async def data_add_func() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await create_data(
        AsyncSessionLocal=AsyncSessionLocal,
        users_count=100,
        subscribe_count=200,
        tweets_count=100,
        images_count=100,
        likes_count=200
    )


if __name__ == "__main__":
    asyncio.run(data_add_func())
