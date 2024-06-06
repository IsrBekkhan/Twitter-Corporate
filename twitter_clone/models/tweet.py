from typing import List, Optional
from pathlib import Path

from sqlalchemy import ForeignKey, select, delete, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.ext.asyncio import AsyncSession

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
        if tweet_media_ids is None:
            tweet_media_ids = []

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(Image).where(Image.id.in_(tweet_media_ids))
            )
            images = result.scalars().all()

            new_tweet = Tweet(
                content=content,
                author_id=author_id,
                tweet_media_ids=images
            )
            db_async_session.add(new_tweet)

        return new_tweet.id

    @classmethod
    async def delete_tweet(cls, db_async_session: AsyncSession, author_id: str, tweet_id: int) -> None:
        """
        Удаление твита из БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param author_id: id пользователя, к которому принадлежит твит
        :param tweet_id: id удаляемого твита
        """
        logger.debug("Удаление твита из БД: id автора = {}, id твита = {}".format(author_id, tweet_id))
        image_paths = await Image.get_image_paths(db_async_session, tweet_id)
        async with db_async_session.begin():
            await db_async_session.execute(
                delete(Tweet)
                .where(Tweet.author_id == author_id)
                .where(Tweet.id == tweet_id)
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
