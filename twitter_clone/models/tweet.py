from typing import List, Optional
from pathlib import Path

from sqlalchemy import ForeignKey, select, delete, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.hybrid import hybrid_property

from database.database import Base, session
from models.image import Image
from models.user import User
from models.like import Like
from models.follower import follower


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(6553))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"))

    tweet_media_ids: Mapped[Optional[List[Image]]] = relationship(Image)
    author: Mapped[User] = relationship(User)
    likes: Mapped[Optional[List[Like]]] = relationship(Like)

    @hybrid_property
    def attachments(self) -> List[str]:
        return [Path("images", media.path).__str__() for media in self.tweet_media_ids]

    @classmethod
    async def add_tweet(cls, author_id: int,  content: str, tweet_media_ids: List[int] = None) -> Optional[int]:
        if tweet_media_ids is None:
            tweet_media_ids = []

        async with session.begin():
            result = await session.execute(
                select(Image).where(Image.id.in_(tweet_media_ids))
            )
            images = result.scalars().all()

        new_tweet = Tweet(
            content=content,
            author_id=author_id,
            tweet_media_ids=images
        )
        try:
            async with session.begin():
                session.add(new_tweet)
        except (IntegrityError, DBAPIError) as exc:
            return None
        return new_tweet.id

    @classmethod
    async def delete_tweet(cls, author_id: int, tweet_id: int) -> None:
        image_paths = await Image.get_image_paths(tweet_id)
        async with session.begin():
            await session.execute(
                delete(Tweet)
                .where(Tweet.author_id == author_id)
                .where(Tweet.id == tweet_id)
            )
            for image_path in image_paths:
                await Image.delete_image_from_disk(image_path)

    @classmethod
    async def get_tweet_from_followers(cls, user_id: int) -> List["Tweet"]:
        async with session.begin():
            followings = select(follower.c.following_user_id
                                ).where(follower.c.follower_user_id == user_id)

            result = await session.execute(
                select(Tweet)
                .options(
                    selectinload(Tweet.author),
                    selectinload(Tweet.tweet_media_ids),
                    selectinload(Tweet.likes).selectinload(Like.user)

                )
                .where(Tweet.author_id.in_(followings))
                .order_by(Tweet.id)
            )
            tweets = result.scalars().all()
            ordered_by_likes = sorted(tweets, key=lambda x: len(x.likes), reverse=True)
            return ordered_by_likes
