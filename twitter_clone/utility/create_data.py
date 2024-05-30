from random import randint
from typing import Tuple
from asyncio.exceptions import TimeoutError

import aiohttp
from faker import Faker

from models.user import User
from models.image import Image
from models.tweet import Tweet
from models.like import Like
from models.follower import follower


fake = Faker()


async def get_fox(url: str, client: aiohttp.ClientSession) -> Tuple[bytes, int]:
    image_id = randint(1, 100)
    async with client.get(url.format(image_id=image_id)) as response:
        if response.status == 200:
            return await response.read(), image_id


async def get_text(client: aiohttp.ClientSession) -> str:
    api_url = "https://fish-text.ru/get"
    api_params = {
        "number": 1
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        async with client.get(api_url, params=api_params) as response:
            if response.status == 200:
                result = await response.json(encoding="utf-8", content_type="text/html")
                return result["text"]


async def create_data(users_count: int, tweets_count: int, images_count: int) -> None:
    # Добавление пользователей
    for i in range(1, users_count + 1):
        await User.add_user(fake.first_name())

    # Добавление подписок
    for i in range(users_count):
        await User.follow(randint(1, users_count // 2), randint(1, users_count // 2))

    # Добавление изображений
    file_name = "{image_id}.jpg"
    fox_url = "https://randomfox.ca/images/{image_id}.jpg"

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        for _ in range(images_count):
            try:
                image, image_id = await get_fox(fox_url, client)
            except TimeoutError as exc:
                continue
            result = await Image.add_image(image, file_name.format(image_id=image_id))

    # Добавление твитов
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        for _ in range(1, tweets_count + 1):
            try:
                tweet_data = await get_text(client)
            except TimeoutError as exc:
                continue
            result = await Tweet.add_tweet(
                randint(1, users_count // 2),
                tweet_data,
                [randint(1, images_count) for _ in range(randint(1, 6))]
            )

    # Добавление лайков
    for _ in range(100):
        await Like.add_like(randint(1, users_count // 2), randint(1, tweets_count))

