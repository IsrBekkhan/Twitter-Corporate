from sqlalchemy import Column, ForeignKey, Table, CHAR

from database import Base


# follower_user_id: id пользователя, который подписался на пользователя c id following_user_id
# following_user_id: id пользователя, на который подписался пользователь с id follower_user_id
follower = Table(
    "followers",
    Base.metadata,
    Column(
        "follower_user_id",
        CHAR(32),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "following_user_id",
        CHAR(32),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    ),
)
