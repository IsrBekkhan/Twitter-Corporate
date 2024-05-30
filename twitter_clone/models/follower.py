from sqlalchemy import Column, ForeignKey, Integer, Table

from database.database import Base


follower = Table(
    "followers",
    Base.metadata,
    Column(
        "follower_user_id",
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "following_user_id",
        Integer,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True
    ),
)
