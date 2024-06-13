from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.result import Result


class User(BaseModel):
    id: str = Field(..., title="ID пользователя", max_length=32, min_length=1)
    name: str = Field(..., title="Имя пользователя", max_length=20, min_length=2)
    model_config = ConfigDict(from_attributes=True)


class UserInfo(User):
    followers: List[Optional[User]]
    following: List[Optional[User]]

    model_config = ConfigDict(from_attributes=True)


class UserInfoResult(Result):
    user: UserInfo


class NewUserResult(Result):
    user: User
