from fastapi import HTTPException, status
from sqlalchemy import ForeignKey, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from logger import logger
from models.user import User


class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True
    )
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    user: Mapped[User] = relationship(User)

    @hybrid_property
    def name(self) -> str:
        return self.user.name

    @classmethod
    async def add_like(
        cls, db_async_session: AsyncSession, user_id: str, tweet_id: int
    ) -> bool:
        """
        Добавляет like по указанной id твита

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя, который лайкнул
        :param tweet_id: id твита, которую лайкнул пользователь
        """
        logger.debug(
            "Добавление лайка: user_id = {}, tweet_id = {}".format(user_id, tweet_id)
        )
        try:
            async with db_async_session.begin():
                db_async_session.add(Like(user_id=user_id, tweet_id=tweet_id))
            return True
        except IntegrityError as exc:
            exc_detail = str(exc.orig).split("\n")[1]

            if all(
                [
                    value in exc_detail
                    for value in (user_id, "user_id", "is not present in table")
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователя с id {user_id} не существует",
                )

            if all(
                [
                    value in exc_detail
                    for value in (str(tweet_id), "tweet_id", "is not present in table")
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Твита с id {tweet_id} не существует",
                )

            if all(
                [
                    value in exc_detail
                    for value in (
                        user_id,
                        str(tweet_id),
                        "user_id",
                        "tweet_id",
                        "already exists",
                    )
                ]
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Запись о добавлении лайка твиту с id {tweet_id} пользователем с id {user_id} "
                    f"уже существует",
                )

    @classmethod
    async def delete_like(
        cls, db_async_session: AsyncSession, user_id: str, tweet_id: int
    ) -> bool:
        """
        Удаляет like по указанной id твита

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя, который дизлайкнул
        :param tweet_id: id твита, которую дизлайкнул пользователь
        """
        logger.debug(
            "Удаление лайка: user_id = {}, tweet_id = {}".format(user_id, tweet_id)
        )
        async with db_async_session.begin():
            result = await db_async_session.execute(
                delete(Like)
                .where(Like.user_id == user_id)
                .where(Like.tweet_id == tweet_id)
            )

            if result.rowcount != 0:
                return True
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Запись лайка твита с id {tweet_id} от пользователя с id {user_id} не существует",
            )

    @classmethod
    async def get_likes_count(cls, db_async_session: AsyncSession) -> int:
        """
        Функция, возвращающая количество записей лайков в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :return: int - количество записей лайков в БД
        """
        logger.debug("Получение количества записей лайков в БД")

        async with db_async_session.begin():
            result = await db_async_session.execute(select(func.count(Like.user_id)))
            return result.scalars().one()
