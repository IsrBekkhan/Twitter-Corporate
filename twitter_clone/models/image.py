from typing import List, Optional
from pathlib import Path
from datetime import date

from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.exc import IntegrityError

from fastapi import UploadFile
import aiofiles
from aiofiles.os import remove as aio_remove, rmdir as aio_rmdir

from database.database import Base, session


ABS_PATH = Path(__file__).parent.parent
IMAGES_PATH = Path(ABS_PATH, "static", "images")
IMAGES_PATH.mkdir(exist_ok=True)


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str]
    tweet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    @classmethod
    async def __save_image_to_disk(cls, image: bytes, image_path: str):
        image_abs_path = Path(IMAGES_PATH, image_path)
        async with aiofiles.open(image_abs_path.__str__(), mode="wb") as new_file:
            await new_file.write(image)

    @classmethod
    async def __get_image_path(cls, image_id: int, image_filename: str) -> str:
        image_extension = image_filename.split(".")[-1]
        image_name = f"{image_id}.{image_extension}"

        date_path = Path(date.today().__str__())
        current_image_path = Path(IMAGES_PATH, date_path)
        current_image_path.mkdir(exist_ok=True)
        return Path(date_path, image_name).__str__()

    @classmethod
    async def delete_image_from_disk(cls, image_relative_path: str):
        image_path = Path(IMAGES_PATH, image_relative_path)
        await aio_remove(image_path)
        try:
            await aio_rmdir(image_path.parent)
        except OSError as exc:
            pass

    @classmethod
    async def add_image(cls, image: bytes, filename: str) -> Optional[int]:
        new_image = Image(path="")
        try:
            async with session.begin():
                session.add(new_image)
                await session.flush()

                image_relative_path = await cls.__get_image_path(new_image.id, filename)
                new_image.path = image_relative_path
                await cls.__save_image_to_disk(image, image_relative_path)
            return new_image.id
        except (IntegrityError, OSError) as exc:
            return None

    @classmethod
    async def get_image_paths(cls, tweet_id: int) -> List[int]:
        async with session.begin():
            result = await session.execute(
                select(Image).where(Image.tweet_id == tweet_id)
            )
            return [image.path for image in result.scalars().all()]
