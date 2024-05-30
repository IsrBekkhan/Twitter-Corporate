from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, UploadFile, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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


front_app = FastAPI()
front_app.mount("/", StaticFiles(directory="static", html=True), name="static")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    logger.info("Запуск приложения")
    async with engine.begin() as conn:
        logger.debug("Создание таблиц БД")
        await conn.run_sync(Base.metadata.create_all)
    # await create_data(users_count=100, images_count=50, tweets_count=100)
    yield
    logger.warning("Закрытие приложения")
    await engine.dispose()
    await logger.complete()


app = FastAPI(responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResult}}, lifespan=lifespan)


# Database dependency
async def get_db_async_session():
    logger.debug("Создание сессии БД для текущего запроса")
    db_async_session: AsyncSession = AsyncSessionLocal()
    try:
        yield db_async_session
    finally:
        await db_async_session.close()


@app.get("/api/tweets", response_model=TweetListResult, status_code=status.HTTP_200_OK, tags=["Твиты"])
async def get_tweets(
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
):
    """
    Возвращает твиты текущего пользователия и твиты пользователей на которых он подписан

    """
    logger.debug("Запрос на получение твитов для пользователя с id = {}".format(api_key))
    tweets = await Tweet.get_tweet_from_followers(db_async_session, user_id=api_key)
    await logger.complete()
    return TweetListResult(tweets=tweets)


@app.post("/api/tweets", response_model=TweetResult, status_code=status.HTTP_201_CREATED, tags=["Твиты"])
async def add_tweet(
        tweet: NewTweet,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> TweetResult:
    """
    Добавляет новый твит в БД

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


@app.delete("/api/tweets/{tweet_id}", response_model=Result, status_code=status.HTTP_200_OK, tags=["Твиты"])
async def delete_tweet(
        tweet_id: int,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Удаляет твит пользователя по указанной id твита

    """
    logger.debug("Запрос на удаление твита: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Tweet.delete_tweet(db_async_session=db_async_session, author_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.post(
    "/api/tweets/{tweet_id}/likes",
    response_model=Result,
    status_code=status.HTTP_201_CREATED,
    tags=["Лайки"]
)
async def add_like(
        tweet_id: int,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Добавляет лайк для твита по его id

    """
    logger.debug("Запрос на добавление лайка: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Like.add_like(db_async_session=db_async_session, user_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.delete("/api/tweets/{tweet_id}/likes", response_model=Result, status_code=status.HTTP_200_OK, tags=["Лайки"])
async def delete_like(
        tweet_id: int,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Удаляет лайк твита по его id

    """
    logger.debug("Запрос на удаление лайка: api_key = {}, tweet_id = {}".format(api_key, tweet_id))
    await Like.delete_like(db_async_session=db_async_session, user_id=api_key, tweet_id=tweet_id)
    await logger.complete()
    return Result()


@app.post("/api/medias", response_model=ImageResult, status_code=status.HTTP_201_CREATED, tags=["Медиа"])
async def post_image(file: UploadFile, db_async_session: AsyncSession = Depends(get_db_async_session)) -> ImageResult:
    """
    Добавляет изображение в приложение: сохраняет его в папке images и добавляет об этом запись в БД

    """
    logger.debug("Добавление изображения: file_name = {}".format(file.filename))
    image_id = await Image.add_image(db_async_session, await file.read(), file.filename)
    await logger.complete()
    return ImageResult(media_id=image_id)


@app.get("/api/users/me", response_model=UserInfoResult, status_code=status.HTTP_200_OK, tags=["Пользователи"])
async def my_profile_info(
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> UserInfoResult:
    """
    Возвращает информацию о текущим пользователе по id указанном в ключе заголовка api-key

    """
    logger.debug("Запрос информации о профиле пользователя: api-key = {}".format(api_key))
    user_data = await User.get_user_data(db_async_session, api_key)
    await logger.complete()
    return UserInfoResult(user=user_data)


@app.get(
    "/api/users/{user_id}",
    response_model=UserInfoResult,
    status_code=status.HTTP_200_OK,
    tags=["Пользователи"]
)
async def users_profile_info(
        user_id: str,
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> UserInfoResult:
    """
    Возвращает информацию о пользователе по указанном в строке url id

    """
    logger.debug("Запрос информации о профиле пользователя: user_id = {}".format(user_id))
    user_data = await User.get_user_data(db_async_session, user_id)
    await logger.complete()
    return UserInfoResult(user=user_data)


@app.post(
    "/api/users/{user_id}/follow",
    response_model=Result,
    status_code=status.HTTP_201_CREATED,
    tags=["Подписки"]
)
async def follow_to_user(
        user_id: str,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Подписка текущего пользователя на другого пользователя с id указанным в строке url

    """
    logger.debug("Запрос пользователя с id = {} на подписку на пользователя с id = {}".format(api_key, user_id))
    await User.follow(db_async_session=db_async_session, follower_user_id=api_key, following_user_id=user_id)
    await logger.complete()
    return Result()


@app.delete(
    "/api/users/{user_id}/follow",
    response_model=Result,
    status_code=status.HTTP_200_OK,
    tags=["Подписки"]
)
async def unfollow_to_user(
        user_id: str,
        api_key: Annotated[str | None, Header()],
        db_async_session: AsyncSession = Depends(get_db_async_session)
) -> Result:
    """
    Отписка текущего пользователя от другого пользователя с id, указанным в строке url

    """
    logger.debug("Запрос пользователя с id = {} на отписку от пользователя с id = {}".format(api_key, user_id))
    await User.unfollow(db_async_session=db_async_session, follower_user_id=api_key, following_user_id=user_id)
    await logger.complete()
    return Result()


@app.post(
    "/api/users",
    response_model=NewUserResult,
    response_description="Успешное добавление нового пользователя",
    status_code=status.HTTP_201_CREATED,
    tags=["Пользователи"],
    responses={status.HTTP_409_CONFLICT: {
        "model": ErrorResult, "description": "Ошибка добавления существующего пользователя"}
    }
)
async def add_user(user: UserSchema, db_async_session: AsyncSession = Depends(get_db_async_session)) -> Request:
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
        status_code=400,
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
