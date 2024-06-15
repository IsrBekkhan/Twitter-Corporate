import asyncio
from asyncio.exceptions import TimeoutError
from random import choice, randint
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import aiohttp
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session

from config import GET_FOX_URL, GET_TEXT_PARAMS, GET_TEXT_URL, MEDIA_FILE_NAME
from logger import logger
from models.image import Image
from models.like import Like
from models.tweet import Tweet
from models.user import User

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
    file_name: str,
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
        return await Image.add_image(
            db_async_session, image, file_name.format(image_id=image_id)
        )
    except TimeoutError:
        pass


async def get_text(
    client: aiohttp.ClientSession, api_url: str, api_params: Dict
) -> str:
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
    api_params: Dict,
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
            db_async_session, choice(author_ids), content, random_image_ids
        )
    except TimeoutError:
        pass


async def create_data(
    async_session_local: async_scoped_session,
    users_count: int = 0,
    subscribe_count: int = 0,
    tweets_count: int = 0,
    images_count: int = 0,
    likes_count: int = 0,
    test_user_added: bool = True,
) -> None:
    """
    Функция, которая заполняет таблицы БД случайными записями

    :rtype: object
    :param async_session_local: экземпляр сессии к БД, которую нужно создать и использовать в функции
    :param users_count: количество пользователей в БД (Примечание: итоговое количество может быть меньше из-за
                        пропусков совпадений имён)
    :param subscribe_count: количество записей в БД с подписками (Примечание: итоговое количество может быть меньше
                            из-за пропусков повторяющихся записей)
    :param tweets_count: количество твитов в БД
    :param images_count: колчество изображений (Примечание: итоговое количество может быть меньше из-за
                         пропусков запросов, превышающих тайм-аут)
    :param likes_count: количество записей лайков в БД (Примечание: итоговое количество может быть меньше
                        из-за пропусков повторяющихся записей)
    :param test_user_added: если False, операция добавления тестового пользователя не будет повторяться
    """
    logger.debug(
        "Заполнение таблиц базы данных тестовыми записями: "
        "users={}, subscribes={}, tweets={}, images={}, likes={}".format(
            users_count, subscribe_count, tweets_count, images_count, likes_count
        )
    )

    # Добавление пользователей
    logger.debug(
        "Добавление пользователей со случайными именами в БД: количество = {}".format(
            users_count
        )
    )
    add_user_tasks = []
    current_users_count = users_count

    if test_user_added:
        current_users_count -= 1
        async_session_t = async_session_local()
        add_user_tasks.append(
            User.add_user(
                db_async_session=async_session_t, name="Testname", user_id="test"
            )
        )

    for _ in range(current_users_count):
        async_session = async_session_local()
        user_id = uuid4().hex
        add_user_tasks.append(
            User.add_user(
                db_async_session=async_session, name=fake.first_name(), user_id=user_id
            )
        )

    users_result = await asyncio.gather(*add_user_tasks, return_exceptions=True)

    async_session = async_session_local()
    user_ids = await User.get_all_user_ids(async_session)
    user_added_count = len([user for user in users_result if isinstance(user, User)])

    logger.debug("Добавлено пользователей {}".format(user_added_count))
    await logger.complete()

    # Добавление подписок
    logger.debug(
        "Добавление записей случайных подписок в БД: количество записей = {}".format(
            subscribe_count
        )
    )
    subscribe_tasks = []

    for _ in range(subscribe_count):
        async_session = async_session_local()
        subscribe_tasks.append(
            User.follow(async_session, choice(user_ids), choice(user_ids))
        )

    subscribe_result = await asyncio.gather(*subscribe_tasks, return_exceptions=True)
    subscribe_added_count = len(
        [subscribe for subscribe in subscribe_result if subscribe]
    )
    logger.debug("Добавлено записей {}".format(subscribe_added_count))
    await logger.complete()

    # Добавление изображений
    logger.debug("Добавление изображений: количество = {}".format(images_count))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        image_tasks = []
        for _ in range(images_count):
            async_session = async_session_local()
            image_tasks.append(
                add_image(async_session, client, GET_FOX_URL, MEDIA_FILE_NAME)
            )

        images_result = await asyncio.gather(*image_tasks)

    async_session = async_session_local()
    image_ids = await Image.get_all_image_ids(async_session)
    image_added_count = len([image for image in images_result if image])

    logger.debug("Добавлено изображений: количество = {}".format(image_added_count))
    await logger.complete()

    # Добавление твитов
    logger.debug("Добавление твитов: количество = {}".format(tweets_count))

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(10)) as client:
        tweets_tasks = []

        for _ in range(tweets_count):
            async_session = async_session_local()
            tweets_tasks.append(
                add_tweet(
                    db_async_session=async_session,
                    client=client,
                    author_ids=user_ids,
                    image_ids=image_ids,
                    api_url=GET_TEXT_URL,
                    api_params=GET_TEXT_PARAMS,
                )
            )

        tweets_result = await asyncio.gather(*tweets_tasks)

    async_session = async_session_local()
    tweets_ids = await Tweet.get_all_tweet_ids(async_session)
    tweets_added_count = len([tweet for tweet in tweets_result if tweet])

    logger.debug("Добавлено твитов: количество = {}".format(tweets_added_count))
    await logger.complete()

    # Добавление лайков
    logger.debug("Добавление записей о лайках: количество {}".format(likes_count))
    likes_tasks = []

    for _ in range(likes_count):
        async_session = async_session_local()
        likes_tasks.append(
            Like.add_like(
                db_async_session=async_session,
                user_id=choice(user_ids),
                tweet_id=choice(tweets_ids),
            )
        )

    like_results = await asyncio.gather(*likes_tasks, return_exceptions=True)
    likes_added_count = len([like for like in like_results if like])

    logger.debug("Добавлено записей лайков: количество = {}".format(likes_added_count))
    await logger.complete()

    # Проверка количества добавленных записей, запрошенных в функции
    if not all(
        [
            user_added_count == users_count,
            tweets_added_count == tweets_count,
            image_added_count == images_count,
            subscribe_added_count == subscribe_count,
            likes_added_count == likes_count,
        ]
    ):
        # рекурсивное использование функции в случае, если количество добавленных записей меньше запрошенных
        await create_data(
            async_session_local=async_session_local,
            users_count=users_count - user_added_count,
            subscribe_count=subscribe_count - subscribe_added_count,
            tweets_count=tweets_count - tweets_added_count,
            images_count=images_count - image_added_count,
            likes_count=likes_count - likes_added_count,
            test_user_added=False,
        )
