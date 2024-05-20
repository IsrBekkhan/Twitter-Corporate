import asyncio

from faker import Faker

from database.database import engine, Base
from models.user import User
from models.image import Image
from models.tweet import Tweet
from models.like import Like
from models.follower import follower
from utility.create_data import create_data

fake = Faker()


async def users(user_id):
    return await Tweet.get_tweet_from_followers(user_id)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # await create_data(users_count=100, images_count=50, tweets_count=100)

    # for i in range(1, 20):
    #     user = await User.get_user_data(user_id=i)
    #     tweet = await Tweet.get_tweet_from_followers(user_id=i)
    #     user = await User.get_user_data(user_id=i+20)
    #     print(tweet)
    # print()
    # await Tweet.test_method(12)

    tasks = [users(i) for i in range(1, 11)]
    group = asyncio.gather(*tasks)
    print(group)


if __name__ == "__main__":
    asyncio.run(init_models())


