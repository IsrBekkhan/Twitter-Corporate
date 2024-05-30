import asyncio

from faker import Faker

from database import engine, Base
# from models.user import User
# from models.tweet import Tweet
# from models.like import Like
# from models.follower import follower
# from models.image import Image
from utility.create_data import create_data

fake = Faker()


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await create_data(users_count=100, subscribe_count=300, images_count=100, tweets_count=300, likes_count=500)

    # from database import AsyncSessionLocal
    #
    # session = AsyncSessionLocal()
    # res = await User.get_user_data(session, "test")
    # print(res)
    # print()


if __name__ == "__main__":
    asyncio.run(init_models())


