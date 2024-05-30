from sqlalchemy import ForeignKey, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from database import Base
from models.user import User


class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    )
    user: Mapped[User] = relationship(User)

    @hybrid_property
    def name(self) -> str:
        return self.user.name

    @classmethod
    async def add_like(cls, db_async_session: AsyncSession, user_id: str, tweet_id: int) -> bool:
        """
        Добавляет like по указанной id твита

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя, который лайкнул
        :param tweet_id: id твита, которую лайкнул пользователь
        """
        logger.debug("Добавление лайка: user_id = {}, tweet_id = {}".format(user_id, tweet_id))
        try:
            async with db_async_session.begin():
                await db_async_session.merge(Like(user_id=user_id, tweet_id=tweet_id))
            return True
        except (IntegrityError, DBAPIError) as exc:
            return False

    @classmethod
    async def delete_like(cls, db_async_session: AsyncSession, user_id: str, tweet_id: int) -> None:
        """
        Удаляет like по указанной id твита

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя, который дизлайкнул
        :param tweet_id: id твита, которую дизлайкнул пользователь
        """
        logger.debug("Удаление лайка: user_id = {}, tweet_id = {}".format(user_id, tweet_id))
        async with db_async_session.begin():
            await db_async_session.execute(
                delete(Like)
                .where(Like.user_id == user_id)
                .where(Like.tweet_id == tweet_id)
            )
