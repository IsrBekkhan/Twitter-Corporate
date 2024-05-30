import asyncio
from random import randint, choice
from typing import Tuple, Optional, List, Dict
from asyncio.exceptions import TimeoutError
from uuid import uuid4

import aiohttp
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from logger import logger

from models.user import User
from models.image import Image
from models.tweet import Tweet
from models.like import Like


fake = Faker()


async def get_fox(url: str, client: aiohttp.ClientSession) -> Tuple[bytes, int]:
    """
    Функция, для скачивания случайного изображения из API по указанной URL

    :param url: URL api c изображениями
    :param client: клиент для HTTP-запроса
    :return: возвращает байтовое представление скачанного изображения и id изображения
    """
    image_id = randint(1, 100)
    logger.debug("HTTP-запрос изображения с id = {}".format(image_id))
    async with client.get(url.format(image_id=image_id)) as response:
        if response.status == 200:
            return await response.read(), image_id


async def add_image(
        db_async_session: AsyncSession,
        client: aiohttp.ClientSession,
        url: str,
        file_name: str
) -> Optional[str]:
    """
    Функция, которая скачивает случайное изображение по указанному URL и передаёт его функции для добавления записи
    в БД и сохранения на диск

    :param db_async_session: асинхронная сессия подключения к БД
    :param client: клиент для HTTP-запроса
    :param url: URL api c изображениями
    :param file_name: название файла изображения
    :return: id изображения при успешной операции
    """
    logger.debug("Добавление нового изображения")
    try:
        image, image_id = await get_fox(url, client)
        return await Image.add_image(db_async_session, image, file_name.format(image_id=image_id))
    except TimeoutError as exc:
        pass


async def get_text(client: aiohttp.ClientSession, api_url: str, api_params: Dict) -> str:
    """
    Функция, которая отправляет запрос к указанному URL, и возвращает случайный текст

    :param client: клиент для HTTP-запроса
    :param api_url: URL адрес API, который возвращает случайные обрезки текста
    :param api_params: параметры запроса к API, который возвращает случайные обрезки текста
    :return: случайный отрывок текста
    """
    logger.debug("HTTP-запрос случайного текста")
    async with client.get(api_url, params=api_params) as response:
        if response.status == 200:
            result = await response.json(encoding="utf-8", content_type="text/html")
            return result["text"]


async def add_tweet(
        db_async_session: AsyncSession,
        client: aiohttp.ClientSession,
        author_ids: List[str],
        image_ids: List[str],
        api_url: str,
        api_params: Dict
) -> int:
    """
    Функция, которая скачивает по указанному URL случайный текст и сохраняет его в качестве твита в БД

    :param db_async_session: асинхронная сессия подключения к БД
    :param client: клиент для HTTP-запроса
    :param author_ids: список id пользователей, из которых будет рандомно выбран автор твита
    :param image_ids: список id изображений, которые будут рандомно привязаны к твиту
    :param api_url: URL адрес API, который возвращает случайные обрезки текста
    :param api_params: параметры запроса к API, который возвращает случайные обрезки текста
    :return: id созданного твита
    """
    logger.debug("Добавление твита в БД")
    try:
        content = await get_text(client, api_url, api_params)
        random_image_ids = None

        if image_ids:
            random_image_ids = [choice(image_ids) for _ in range(randint(1, 6))]

        return await Tweet.add_tweet(
            db_async_session,
            choice(author_ids),
            content,
            random_image_ids
        )
    except TimeoutError as exc:
        pass


async def create_data(
        users_count: int,
        subscribe_count: int,
        tweets_count: int,
        images_count: int,
        likes_count: int
) -> None:
    """
    Функция, которая заполняет таблицы БД случайными записями

    :param users_count: количество пользователей в БД (Примечание: итоговое количество может быть меньше из-за
                        пропусков совпадений имён)
    :param subscribe_count: количество записей в БД с подписками (Примечание: итоговое количество может быть меньше
                            из-за пропусков повторяющихся записей)
    :param tweets_count: количество твитов в БД
    :param images_count: колчество изображений (Примечание: итоговое количество может быть меньше из-за
                         пропусков запросов, превышающих тайм-аут)
    :param likes_count: количество записей лайков в БД (Примечание: итоговое количество может быть меньше
                        из-за пропусков повторяющихся записей)
    """
    logger.debug("Заполнение таблиц базы данных тестовыми записями")

    # Добавление пользователей
    logger.debug("Добавление пользователей со случайными именами в БД: количество = {}".format(users_count))
    add_user_tasks = []
    for i in range(users_count):
        async_session = AsyncSessionLocal()
        user_id = uuid4().hex
        add_user_tasks.append(User.add_user(
            db_async_session=async_session, name=fake.first_name(), user_id=user_id
        ))
    async_session = AsyncSessionLocal()
    add_user_tasks.append(User.add_user(db_async_session=async_session, name="Testname", user_id="test"))
    users_result = await asyncio.gather(*add_user_tasks)
    user_ids = [user.id for user in users_result if user]
    logger.debug("Добавлено пользователей {}".format(len(user_ids)))
    await logger.complete()

    # Добавление подписок
    logger.debug("Добавление записей случайных подписок в БД: количество записей = {}".format(subscribe_count))
    subscribe_tasks = []
    for i in range(subscribe_count):
        async_session = AsyncSessionLocal()
        subscribe_tasks.append(User.follow(async_session, choice(user_ids), choice(user_ids)))
    subscribe_result = await asyncio.gather(*subscribe_tasks)
    true_results = [result for result in subscribe_result if result]
    logger.debug("Добавлено записей {}".format(len(true_results)))
    await logger.complete()

    # Добавление изображений
    logger.debug("Добавление изображений: количество = {}".format(images_count))
    file_name = "{image_id}.jpg"
    fox_url = "https://randomfox.ca/images/{image_id}.jpg"

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        image_tasks = []
        for _ in range(images_count):
            async_session = AsyncSessionLocal()
            image_tasks.append(add_image(async_session, client, fox_url, file_name))

        images_result = await asyncio.gather(*image_tasks)

    image_ids = [uuid_ for uuid_ in images_result if uuid_]
    logger.debug("Добавлено изображений: количество = {}".format(len(image_ids)))
    await logger.complete()

    # Добавление твитов
    logger.debug("Добавление твитов: количество = {}".format(tweets_count))
    api_url = "https://fish-text.ru/get"
    api_params = {
        "number": 1
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        tweets_tasks = []
        for _ in range(tweets_count):
            async_session = AsyncSessionLocal()
            tweets_tasks.append(add_tweet(
                db_async_session=async_session,
                client=client,
                author_ids=user_ids,
                image_ids=image_ids,
                api_url=api_url,
                api_params=api_params
            ))
        tweets_result = await asyncio.gather(*tweets_tasks)

    tweets_ids = [tweet_id for tweet_id in tweets_result if tweet_id]
    logger.debug("Добавлено твитов: количество = {}".format(len(tweets_ids)))
    await logger.complete()

    # Добавление лайков
    logger.debug("Добавление записей о лайках: количество {}".format(likes_count))
    likes_tasks = []
    for _ in range(likes_count):
        async_session = AsyncSessionLocal()
        likes_tasks.append(Like.add_like(
            db_async_session=async_session,
            user_id=choice(user_ids),
            tweet_id=choice(tweets_ids)
        ))
    like_results = await asyncio.gather(*likes_tasks)
    true_results = [result for result in like_results if result]
    logger.debug("Добавлено записей лайков: количество = {}".format(len(true_results)))
    await logger.complete()

