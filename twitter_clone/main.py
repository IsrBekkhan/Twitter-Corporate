from typing import Annotated, Dict

from fastapi import FastAPI, Request, UploadFile, status, Header
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from database.database import Base, engine, session

from logger.logger import logger

from models.user import User
from models.image import Image
from models.tweet import Tweet
from models.like import Like
from models.follower import follower

from utility.create_data import create_data

from schemas.tweet import NewTweet, TweetResult, TweetListResult
from schemas.image import ImageResult
from schemas.result import Result
from schemas.user import UserInfoResult
from schemas.error import ErrorResult


front_app = FastAPI()
front_app.mount("/", StaticFiles(directory="static", html=True), name="static")

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    logger.info("Starting fastapi")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # await create_data(users_count=100, images_count=50, tweets_count=100)


@app.on_event('shutdown')
async def shutdown_event():
    await session.close()
    await engine.dispose()


@app.get("/api/tweets", response_model=TweetListResult, status_code=status.HTTP_200_OK)
async def users(api_key: Annotated[str | None, Header()]):
    """
    Возвращает твиты пользователей на которых вы подписаны
    :param api_key:
    :return:
    """
    if api_key == "test":
        api_key = 1
    tweets = await Tweet.get_tweet_from_followers(user_id=int(api_key))
    return TweetListResult(tweets=tweets)


@app.post("/api/tweets", response_model=TweetResult, status_code=status.HTTP_201_CREATED)
async def add_tweet(tweet: NewTweet, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    tweet_id = await Tweet.add_tweet(
        author_id=int(api_key),
        content=tweet.tweet_data,
        tweet_media_ids=tweet.tweet_media_ids
    )
    return TweetResult(tweet_id=tweet_id)


@app.delete("/api/tweets/{tweet_id}", response_model=Result, status_code=status.HTTP_200_OK)
async def delete_tweet(tweet_id: int, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    await Tweet.delete_tweet(author_id=int(api_key), tweet_id=tweet_id)
    return Result()


@app.post("/api/tweets/{tweet_id}/likes", response_model=Result, status_code=status.HTTP_201_CREATED)
async def add_like(tweet_id: int, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    await Like.add_like(user_id=int(api_key), tweet_id=tweet_id)
    return Result()


@app.delete("/api/tweets/{tweet_id}/likes", response_model=Result, status_code=status.HTTP_200_OK)
async def delete_like(tweet_id: int, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    await Like.delete_like(user_id=int(api_key), tweet_id=tweet_id)
    return Result()


@app.post("/api/medias", response_model=ImageResult, status_code=status.HTTP_201_CREATED)
async def add_image(file: UploadFile) -> ImageResult:
    image_id = await Image.add_image(await file.read(), file.filename)
    return ImageResult(media_id=image_id)


@app.get("/api/users/me", response_model=UserInfoResult, status_code=status.HTTP_200_OK)
async def profile_info(api_key: Annotated[str | None, Header()]) -> Dict:
    if api_key == "test":
        api_key = 1
    user_data = await User.get_user_data(int(api_key))
    return UserInfoResult(user=user_data)


@app.get("/api/users/{user_id}", response_model=UserInfoResult, status_code=status.HTTP_200_OK)
async def profile_info(user_id: int) -> Dict:
    user_data = await User.get_user_data(user_id)
    return UserInfoResult(user=user_data)


@app.post("/api/users/{user_id}/follow", response_model=Result, status_code=status.HTTP_201_CREATED)
async def follow_to_user(user_id: int, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    await User.follow(follower_user_id=int(api_key), following_user_id=user_id)
    return Result()


@app.delete("/api/users/{user_id}/follow", response_model=Result, status_code=status.HTTP_200_OK)
async def unfollow_to_user(user_id: int, api_key: Annotated[str | None, Header()]):
    if api_key == "test":
        api_key = 1
    await User.unfollow(follower_user_id=int(api_key), following_user_id=user_id)
    return Result()


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    error_type = str(type(exc)).split("'")[1]
    content = ErrorResult(result=False, error_type=error_type, error_message=exc.__str__())
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(content)
    )


app.mount("/", front_app)

