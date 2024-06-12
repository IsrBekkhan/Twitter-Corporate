from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, UploadFile, status, Header, Path, File
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, Base, engine

from logger import logger

from models.user import User
from models.image import Image
from models.tweet import Tweet
from models.like import Like

from schemas.tweet import NewTweet, TweetResult, TweetListResult
from schemas.image import ImageResult
from schemas.result import Result
from schemas.user import UserInfoResult, User as UserSchema, NewUserResult
from schemas.error import ErrorResult

from config import RESPONSES
from utility.create_data import create_data


front_app = FastAPI()
front_app.mount("/", StaticFiles(directory="static", html=True), name="static")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    logger.info("Запуск приложения")
    async with engine.begin() as conn:
        logger.debug("Создание таблиц БД")
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # await create_data(
    #     AsyncSessionLocal=AsyncSessionLocal,
    #     users_count=100,
    #     images_count=100,
    #     tweets_count=200,
    #     subscribe_count=300,
    #     likes_count=200
    # )
    yield
    logger.warning("Закрытие приложения")
    await engine.dispose()
    await logger.complete()


app = FastAPI(
    responses={
        **RESPONSES[status.HTTP_400_BAD_REQUEST],
        **RESPONSES[status.HTTP_422_UNPROCESSABLE_ENTITY]
    },
    lifespan=lifespan,
    title="Twitter Clone",
    summary="Документация API",
    description="Урезанная версия твиттера для использования в корпоративной сети",
    version="0.0.1",
    contact={
        "name": "Бекхан Исрапилов",
        "email": "israpal@bk.ru",
    }
)


# Database dependency
async def get_db_async_session():
    logger.debug("Создание сессии БД для текущего запроса")
    db_async_session: AsyncSession = AsyncSessionLocal()
    try:
        yield db_async_session
    finally:
        await db_async_session.aclose()


@app.get(
    "/api/tweets",
    summary="получить твиты",
    response_description="Успешное получение списка твитов",
    status_code=status.HTTP_200_OK,
    tags=["Твиты"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def get_tweets(
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> TweetListResult:
    """
    Получение всех твитов текущего пользователия и твитов пользователей на которых он подписан

    """
    logger.debug("Запрос на получение твитов для пользователя с id = {}".format(api_key))
    tweets = await Tweet.get_tweet_from_followers(db_async_session, user_id=api_key)
    await logger.complete()
    return TweetListResult(tweets=tweets)


@app.post(
    "/api/tweets",
    summary="добавить твит",
    response_description="Успешное добавление нового твита",
    status_code=status.HTTP_201_CREATED,
    tags=["Твиты"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def add_tweet(
        tweet: NewTweet,
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> TweetResult:
    """
    Добавление нового твита в БД

    """
    logger.debug("Добавление нового твита: id пользователя = {}".format(api_key))
    tweet_id = await Tweet.add_tweet(
        db_async_session=db_async_session,
        author_id=api_key,
        content=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids
    )
    await logger.complete()
    return TweetResult(tweet_id=tweet_id)


@app.delete(
    "/api/tweets/{tweet_id}",
    summary="удалить твит",
    response_description="Успешное удаление твита",
    status_code=status.HTTP_200_OK,
    tags=["Твиты"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def delete_tweet(
        tweet_id: int,
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Удаление твита пользователя по указанной id твита

    """
    logger.debug("Запрос на удаление твита: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Tweet.delete_tweet(db_async_session=db_async_session, author_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.post(
    "/api/tweets/{tweet_id}/likes",
    summary="поставить лайк",
    response_description="Успешное добавление лайка",
    status_code=status.HTTP_201_CREATED,
    tags=["Лайки"],
    responses={
        **RESPONSES[status.HTTP_404_NOT_FOUND],
        **RESPONSES[status.HTTP_409_CONFLICT]
    }
)
async def add_like(
        tweet_id: int,
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Добавление лайка для твита по его id

    """
    logger.debug("Запрос на добавление лайка: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Like.add_like(db_async_session=db_async_session, user_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.delete(
    "/api/tweets/{tweet_id}/likes",
    summary="удалить лайк",
    response_description="Успешное удаление лайка",
    status_code=status.HTTP_200_OK,
    tags=["Лайки"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def delete_like(
        tweet_id: int,
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Удаление лайка по id твита

    """
    logger.debug("Запрос на удаление лайка: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Like.delete_like(db_async_session=db_async_session, user_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.post(
    "/api/medias",
    summary="добавить изображение",
    response_description="Успешное добавление изображения",
    status_code=status.HTTP_201_CREATED,
    tags=["Медиа"]
)
async def post_image(
        file: Annotated[UploadFile, File],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> ImageResult:
    """
    Добавление изображения в приложение: сохраняет его в папке images и добавляет об этом запись в БД

    """
    if file.size < 1024:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="В запросе отсутствует файл изображения"
        )
    logger.debug("Добавление изображения: file_name = {}".format(file.filename))
    image_id = await Image.add_image(db_async_session, await file.read(), file.filename)
    await logger.complete()
    return ImageResult(media_id=image_id)


@app.get(
    "/api/users/me",
    summary="инфо моего профиля",
    status_code=status.HTTP_200_OK,
    response_description="Инфо о текущем пользователе",
    tags=["Пользователи"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def my_profile_info(
        api_key: Annotated[str | None, Header(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> UserInfoResult:
    """
    Получение информации о профиле текущего пользователя по id, указанном в ключе заголовка api-key

    """
    logger.debug("Запрос информации о профиле пользователя: api-key = {}".format(api_key))
    user_data = await User.get_user_data(db_async_session, api_key)
    await logger.complete()
    return UserInfoResult(user=user_data)


@app.get(
    "/api/users/{user_id}",
    summary="инфо профиля пользователя",
    status_code=status.HTTP_200_OK,
    response_description="Инфо об указанном пользователе",
    tags=["Пользователи"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def users_profile_info(
        user_id: Annotated[str, Path(title="id пользователя", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> UserInfoResult:
    """
    Получение информации о профиле пользователя по указанном в строке url id

    """
    logger.debug("Запрос информации о профиле пользователя: user_id = {}".format(user_id))
    user_data = await User.get_user_data(db_async_session, user_id)
    await logger.complete()
    return UserInfoResult(user=user_data)


@app.post(
    "/api/users/{user_id}/follow",
    summary="подписаться",
    response_description="Успешная подписка на пользователя",
    status_code=status.HTTP_201_CREATED,
    tags=["Подписки"],
    responses={
        **RESPONSES[status.HTTP_404_NOT_FOUND],
        **RESPONSES[status.HTTP_409_CONFLICT]
    }
)
async def follow_to_user(
        user_id: Annotated[str, Path(title="id пользователя", max_length=32)],
        api_key: Annotated[str | None, Header(title="id подписчика", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Подписка текущего пользователя на другого пользователя с id, указанным в строке url

    """
    logger.debug("Запрос пользователя с id = {} на подписку на пользователя с id = {}".format(api_key, user_id))
    await User.follow(db_async_session=db_async_session, follower_user_id=api_key, following_user_id=user_id)
    await logger.complete()
    return Result()


@app.delete(
    "/api/users/{user_id}/follow",
    summary="отписаться",
    response_description="Успешная отписка от пользователя",
    status_code=status.HTTP_200_OK,
    tags=["Подписки"],
    responses=RESPONSES[status.HTTP_404_NOT_FOUND]
)
async def unfollow_to_user(
        user_id: Annotated[str, Path(title="id пользователя", max_length=32)],
        api_key: Annotated[str | None, Header(title="id подписчика", max_length=32)],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Отписка текущего пользователя от другого пользователя с id, указанного в строке url

    """
    logger.debug("Запрос пользователя с id = {} на отписку от пользователя с id = {}".format(api_key, user_id))
    await User.unfollow(db_async_session=db_async_session, follower_user_id=api_key, following_user_id=user_id)
    await logger.complete()
    return Result()


@app.post(
    "/api/users",
    summary="добавить пользователя",
    response_description="Успешное добавление нового пользователя",
    status_code=status.HTTP_201_CREATED,
    tags=["Пользователи"],
    responses=RESPONSES[status.HTTP_409_CONFLICT]
)
async def add_user(user: UserSchema, db_async_session: AsyncSession = Depends(get_db_async_session)) -> NewUserResult:
    """
    Добавление нового пользователя в БД

    """
    logger.debug("Запрос на добавление нового пользователя в БД: id = {}, name = {}".format(user.id, user.name))
    new_user = await User.add_user(db_async_session, user_id=user.id, name=user.name)
    await logger.complete()
    return NewUserResult(user=new_user)


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Обработчик непредвиденных исключений

    """
    error_type = str(type(exc)).split("'")[1]
    content = ErrorResult(result=False, error_type=error_type, error_message=exc.__str__())
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(content)
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Обработчик ошибок валидации

    """
    error_type = str(type(exc)).split("'")[1]
    content = ErrorResult(result=False, error_type=error_type, error_message=str(exc.errors()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(content)
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Обработчик исключений HTTPException

    """
    error_type = str(type(exc)).split("'")[1]
    content = ErrorResult(result=False, error_type=error_type, error_message=exc.detail)
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(content))


app.mount("/", front_app)
