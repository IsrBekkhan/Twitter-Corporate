from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from schemas.result import Result


class User(BaseModel):
    id: int
    name: str = Field(
        ...,
        title="Имя пользователя",
        max_length=20
    )
    model_config = ConfigDict(from_attributes=True)


class UserInfo(User):
    followers: List[Optional[User]]
    followings: List[Optional[User]]

    model_config = ConfigDict(from_attributes=True)


class UserInfoResult(Result):
    user: UserInfo



