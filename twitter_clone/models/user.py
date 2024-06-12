from typing import List, Dict, Any, Optional

from sqlalchemy import delete, select, String, CHAR, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from logger import logger
from database import Base
from models.follower import follower


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(CHAR(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(20), unique=True)

    # followers: список пользователей, которые подписаны на текущего пользователя (подписчики)
    followers: Mapped[List["User"]] = relationship(
        "User",
        secondary=follower,
        primaryjoin=follower.c.following_user_id == id,
        secondaryjoin=follower.c.follower_user_id == id,
        back_populates="following"
    )
    # following: список пользователей, на которыx подписан текущий пользователь (подписки)
    following: Mapped[List["User"]] = relationship(
        "User",
        secondary=follower,
        primaryjoin=follower.c.follower_user_id == id,
        secondaryjoin=follower.c.following_user_id == id,
        back_populates="followers"
    )

    def to_json(self) -> Dict[str, Any]:
        """
        Функция, для отладки
        в логике приложения не использутся
        :return: возвращает словарное представление объекта
        """
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns
        }

    @classmethod
    async def add_user(cls, db_async_session: AsyncSession, user_id: str, name: str) -> Optional["User"]:
        """
        Функция, которая добавляет нового пользователся в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param name: имя пользователя
        :param user_id: id пользователя (по умолчанию uuid)
        :return: data-объект добавленного пользователя
        """
        logger.debug("Добавление нового пользователя: name = {}, id = {}".format(name, user_id))
        new_user = User(id=user_id, name=name)

        try:
            async with db_async_session.begin():
                db_async_session.add(new_user)
        except IntegrityError as exc:
            if name in str(exc.orig):
                logger.warning("Пользователь с именем {} уже существует".format(name))
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Пользователь с именем {name} уже существует"
                )
            logger.warning("Пользователь с id {} уже существует".format(user_id))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Пользователь с id {user_id} уже существует"
            )

        return new_user

    @classmethod
    async def get_user_data(cls, db_async_session: AsyncSession, user_id: str) -> "User":
        """
        Функция, которая возвращает полную информацию профиля пользователя

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя
        :return: data-объект пользователя
        """
        logger.debug("Получение информации профиля пользователя: user_id = {}".format(user_id))
        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(User)
                .options(selectinload(User.followers), selectinload(User.following))
                .where(User.id == user_id)
            )
            user = result.scalars().one_or_none()

            if user:
                return user

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользователь с id {user_id} не существует"
            )

    @classmethod
    async def delete_user(cls, db_async_session: AsyncSession, user_id: str) -> None:
        """
        Функция, которая удаляет пользователя из БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id удаляемого пользователя
        """
        logger.debug("Удаление пользовалея из БД: user_id = {}".format(user_id))
        async with db_async_session.begin():
            await db_async_session.execute(
                delete(User).where(User.id == user_id)
            )

    @classmethod
    async def follow(cls, db_async_session: AsyncSession, follower_user_id: str, following_user_id: str) -> bool:
        """
        Функция, которая добавляет подписку на пользователя

        :param db_async_session: асинхронная сессия подключения к БД
        :param follower_user_id: id пользователя, который подписывается на пользователя с id following_user_id
        :param following_user_id: id пользователя, на которого подписывается пользователь с id follower_user_id
        :return: bool-евый результат выполнения
        """
        logger.debug("Подписка пользователя c id = {} на пользователя с id = {}".format(
            follower_user_id, following_user_id)
        )
        if follower_user_id == following_user_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Пользователь не может подписаться сам на себя"
            )
        try:
            async with db_async_session.begin():
                result = await db_async_session.execute(
                    follower.insert().values((follower_user_id, following_user_id))
                )
        except IntegrityError as exc:
            exc_detail = str(exc.orig).split("\n")[1]

            if all([value in exc_detail
                    for value in (follower_user_id, "follower_user_id", "is not present in table")]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователя с id {follower_user_id} не существует"
                )

            if all([value in exc_detail
                    for value in (following_user_id, "following_user_id", "is not present in table")]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователя с id {following_user_id} не существует"
                )

            if all([value in exc_detail
                    for value in (
                            follower_user_id,
                            following_user_id,
                            "follower_user_id",
                            "following_user_id",
                            "already exists"
                    )]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Запись о подписке пользователя с id {follower_user_id} "
                           f"на пользователя с {following_user_id} уже существует в БД"
                )

        return True

    @classmethod
    async def unfollow(cls, db_async_session: AsyncSession, follower_user_id: str, following_user_id: str) -> bool:
        """
        Функция, которая удаляет подписку от пользователя

        :param db_async_session: асинхронная сессия подключения к БД
        :param follower_user_id: id пользователя, который отписывается от пользователя с id following_user_id
        :param following_user_id: id пользователя, от которого отписывается пользователь с id follower_user_id
        """
        logger.debug("Отписка пользователя c id = {} от пользователя с id = {}".format(
            follower_user_id, following_user_id)
        )
        async with db_async_session.begin():
            row = await db_async_session.execute(
                follower.delete()
                .where(follower.c.follower_user_id == follower_user_id)
                .where(follower.c.following_user_id == following_user_id)
            )
            if row.rowcount != 0:
                return True
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Запись об отписке пользователя с id {follower_user_id} "
                       f"от пользователя с {following_user_id} не существует в БД"
            )

    @classmethod
    async def get_all_user_ids(cls, db_async_session: AsyncSession) -> List[str]:
        """
        Функция, которая возвращает список id всех пользователей в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :return: список id всех пользователей в БД
        """
        logger.debug("Получение списка id всех пользователей из БД")

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(User.id)
            )
            return result.scalars().all()

    @classmethod
    async def get_subscribes_count(cls, db_async_session: AsyncSession) -> int:
        """
        Функция, возвращающая количество записей подписок в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :return: int - количество записей подписок в БД
        """
        logger.debug("Получение количества записей подписок в БД")

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(func.count(follower.table_valued()))
            )
            return result.scalars().one()

    @classmethod
    async def is_user_exist(cls, db_async_session: AsyncSession, user_id: str) -> bool:
        """
        Функция, которая проверяет существует ли пользователь с заданным id в БД.

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id пользователя
        :return: True если пользователь существует, иначе False
        """
        logger.debug("Проверка на наличие пользователя с id {} в БД".format(user_id))

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalars().one_or_none()

        if user:
            return True
        return False
