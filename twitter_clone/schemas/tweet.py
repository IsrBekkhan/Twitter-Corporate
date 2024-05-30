from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from schemas.result import Result
from schemas.user import User
from schemas.like import Like


class NewTweet(BaseModel):
    tweet_data: str = Field(
        ...,
        title="Текст нового твита",
        max_length=6553
    )
    tweet_media_ids: List[str] = Field(
        ...,
        title="Список id-изображений нового твита"
    )


class TweetView(BaseModel):
    id: int
    content: str
    attachments: List[Optional[str]]
    author: User
    likes: List[Optional[Like]]

    model_config = ConfigDict(from_attributes=True)


class TweetResult(Result):
    tweet_id: int


class TweetListResult(Result):
    tweets: List[Optional[TweetView]]


