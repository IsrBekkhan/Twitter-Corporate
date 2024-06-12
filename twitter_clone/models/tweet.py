from typing import List, Optional
from pathlib import Path

from sqlalchemy import ForeignKey, select, delete, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from fastapi import HTTPException, status

from database import Base
from logger import logger

from models.image import Image
from models.user import User
from models.like import Like
from models.follower import follower


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(6553))
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    tweet_media_ids: Mapped[Optional[List[Image]]] = relationship(Image)
    author: Mapped[User] = relationship(User)
    likes: Mapped[Optional[List[Like]]] = relationship(Like)

    @hybrid_property
    def attachments(self) -> List[str]:
        return [Path("images", media.folder, f"{media.id}.{media.extension}").__str__()
                for media in self.tweet_media_ids]

    @classmethod
    async def add_tweet(
            cls,
            db_async_session: AsyncSession,
            author_id: str,
            content: str,
            tweet_media_ids: List[str] = None
    ) -> int:
        """
        Функия, добавляющая новый твит в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param author_id: id пользователя, который создаёт твит
        :param content: текст твита
        :param tweet_media_ids: id изображений, который привязаны к данному твиту
        :return: id добавленного в БД твита
        """
        logger.debug("Добавление нового твита в БД: id автора = {}".format(author_id))

        try:
            async with db_async_session.begin():

                if tweet_media_ids:
                    result = await db_async_session.execute(
                        select(Image).where(Image.id.in_(tweet_media_ids))
                    )
                    images = result.scalars().all()

                    if len(images) != len(set(tweet_media_ids)):
                        images_str = [image.id for image in images]
                        not_exist_ids = [image_id for image_id in tweet_media_ids if image_id not in images_str]

                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Получен список id изображений, которых не существуeт в БД: {str(not_exist_ids)}"
                        )
                else:
                    images = []

                new_tweet = Tweet(
                    content=content,
                    author_id=author_id,
                    tweet_media_ids=images
                )
                db_async_session.add(new_tweet)
        except IntegrityError as exc:
            exc_detail = str(exc.orig).split("\n")[1]

            if all([value in exc_detail
                    for value in (author_id, "author_id", "is not present in table")]):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователя с id {author_id} не существует"
                )

        return new_tweet.id

    @classmethod
    async def delete_tweet(cls, db_async_session: AsyncSession, author_id: str, tweet_id: int) -> None:
        """
        Удаление твита из БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param author_id: id пользователя, к которому принадлежит твит
        :param tweet_id: id удаляемого твита
        """
        if await User.is_user_exist(db_async_session, author_id) is False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователя с id {} не существует".format(author_id)
            )

        logger.debug("Удаление твита из БД: id автора = {}, id твита = {}".format(author_id, tweet_id))
        image_paths = await Image.get_image_paths(db_async_session, tweet_id)
        async with db_async_session.begin():
            result = await db_async_session.execute(
                delete(Tweet)
                .where(Tweet.author_id == author_id)
                .where(Tweet.id == tweet_id)
            )
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Твит с id {} не существует".format(tweet_id)
                )
            for image_path in image_paths:
                await Image.delete_image_from_disk(image_path)

    @classmethod
    async def get_tweet_from_followers(cls, db_async_session: AsyncSession, user_id: str) -> List["Tweet"]:
        """
        Функция, которая возвращает списко твитов пользователей, на которых подписан текущий пользователь,
        а также твиты, созданные текущим пользователем

        :param db_async_session: асинхронная сессия подключения к БД
        :param user_id: id текущего пользователя
        :return: список твитов, отсортированных по убыванию количества лайков
        """
        if not await User.is_user_exist(db_async_session, user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Пользоватлея с id {user_id} не существует в БД"
            )

        logger.debug("Получение списка твитов пользователя: id пользователя = {}".format(user_id))
        async with db_async_session.begin():
            followings = select(follower.c.following_user_id
                                ).where(follower.c.follower_user_id == user_id)

            result = await db_async_session.execute(
                select(Tweet)
                .options(
                    selectinload(Tweet.author),
                    selectinload(Tweet.tweet_media_ids),
                    selectinload(Tweet.likes).selectinload(Like.user)
                )
                .where(Tweet.author_id.in_(followings))
            )
            all_tweets: List[Optional[Tweet]] = result.scalars().all()

            user_tweets_result = await db_async_session.execute(
                select(Tweet)
                .options(
                    selectinload(Tweet.author),
                    selectinload(Tweet.tweet_media_ids),
                    selectinload(Tweet.likes).selectinload(Like.user)
                )
                .where(Tweet.author_id == user_id)
            )
            user_tweets: List[Optional[Tweet]] = user_tweets_result.scalars().all()
            all_tweets.extend(user_tweets)

        ordered_by_likes = sorted(all_tweets, key=lambda x: len(x.likes), reverse=True)
        return ordered_by_likes

    @classmethod
    async def get_all_tweet_ids(cls, db_async_session: AsyncSession) -> List[int]:
        """
        Функция, возвращающая список id всех твитов в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :return: список id всех твитов в БД
        """
        logger.debug("Получение списка id всех твитов в БД")

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(Tweet.id)
            )
            return result.scalars().all()

    @classmethod
    async def get_tweet_by_id(cls, db_async_session: AsyncSession, tweet_id: int) -> Optional["Tweet"]:
        """
        Функция, которая возвращает твит по указанному id

        :param db_async_session: асинхронная сессия подключения к БД
        :param tweet_id: id твита
        :return: объект твита
        """
        logger.debug("Получение твита с id {}".format(tweet_id))

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(Tweet)
                .options(selectinload(Tweet.tweet_media_ids))
                .where(Tweet.id == tweet_id)
            )
            return result.scalars().one_or_none()
