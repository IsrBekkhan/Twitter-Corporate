from typing import List, Dict, Any, Optional

from sqlalchemy import CHAR, delete, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.exc import IntegrityError, DBAPIError

from database.database import Base, engine, session
from models.follower import follower


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(CHAR(20), unique=True)
    followers: Mapped[List["User"]] = relationship(
        "User",
        secondary=follower,
        primaryjoin=follower.c.follower_user_id == id,
        secondaryjoin=follower.c.following_user_id == id,
        back_populates="followings"
    )
    followings: Mapped[List["User"]] = relationship(
        "User",
        secondary=follower,
        primaryjoin=follower.c.following_user_id == id,
        secondaryjoin=follower.c.follower_user_id == id,
        back_populates="followers"
    )

    def to_json(self) -> Dict[str, Any]:
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }

    @classmethod
    async def add_user(cls, name: str) -> Optional["User"]:
        new_user = User(name=name)
        try:
            async with session.begin():
                session.add(new_user)
        except (IntegrityError, DBAPIError) as exc:
            return
        return new_user

    @classmethod
    async def get_user_data(cls, user_id: int) -> Optional["User"]:
        async with session.begin():
            result = await session.execute(
                select(User)
                .options(selectinload(User.followers), selectinload(User.followings))
                .where(User.id == user_id)
            )
            user = result.scalars().one_or_none()
            return user

    @classmethod
    async def delete_user(cls, user_id: int) -> None:
        async with session.begin():
            await session.execute(
                delete(User).where(User.id == user_id)
            )

    @classmethod
    async def follow(cls, follower_user_id, following_user_id: int) -> bool:
        if follower_user_id == following_user_id:
            return False
        try:
            async with session.begin():
                await session.execute(
                    follower.insert().values((follower_user_id, following_user_id))
                )
        except IntegrityError as exc:
            return False
        return True

    @classmethod
    async def unfollow(cls, follower_user_id, following_user_id: int) -> None:
        async with session.begin():
            await session.execute(
                follower.delete()
                .where(follower.c.follower_user_id == follower_user_id)
                .where(follower.c.following_user_id == following_user_id)
            )
