from sqlalchemy import ForeignKey, delete
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError, DBAPIError
from sqlalchemy.ext.hybrid import hybrid_property

from database.database import Base, session
from models.user import User


class Like(Base):
    __tablename__ = "likes"

    user_id: Mapped[int] = mapped_column(
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
    async def add_like(cls, user_id: int, tweet_id: int) -> None:
        try:
            async with session.begin():
                await session.merge(Like(user_id=user_id, tweet_id=tweet_id))
        except (IntegrityError, DBAPIError) as exc:
            return

    @classmethod
    async def delete_like(cls, user_id: int, tweet_id: int) -> None:
        async with session.begin():
            await session.execute(
                delete(Like)
                .where(Like.user_id == user_id)
                .where(Like.tweet_id == tweet_id)
            )
