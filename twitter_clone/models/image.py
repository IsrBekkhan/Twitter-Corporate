from typing import List, Optional, Tuple
from pathlib import Path
from datetime import date
from uuid import uuid4

from sqlalchemy import ForeignKey, select, Uuid, CHAR
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import aiofiles
from aiofiles.os import remove as aio_remove, rmdir as aio_rmdir

from logger import logger
from database import Base


ABS_PATH = Path(__file__).parent.parent
IMAGES_PATH = Path(ABS_PATH, "static", "images")
IMAGES_PATH.mkdir(exist_ok=True)


class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(CHAR(32), primary_key=True)
    folder: Mapped[str] = mapped_column(CHAR(10), default=date.today().__str__())
    extension: Mapped[str] = mapped_column(CHAR(3))
    tweet_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tweets.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    @classmethod
    async def __get_extension_and_folder(cls, file_name: str) -> Tuple[str, str]:
        """
        Функция, возвращает расширение изображения и папку сохранения на основе текущаей даты

        :param file_name: название файла изображения
        :return: расширение и название папки
        """
        logger.debug("Генерация расширения и названия папки: file_name = {}".format(file_name))
        return file_name.split(".")[-1], date.today().__str__()

    @classmethod
    async def __save_image_to_disk(cls, image: bytes, image_path: str):
        """
        Функция, сохраняющая изображение в указанный каталог

        :param image: байтовое представление изображения
        :param image_path: относителный путь для сохранения нового изображения
        """
        logger.debug("Сохранение изображения на диск: relative_path = {}".format(image_path))
        image_abs_path = Path(IMAGES_PATH, image_path)
        async with aiofiles.open(image_abs_path.__str__(), mode="wb") as new_file:
            await new_file.write(image)

    @classmethod
    async def __generate_image_path(cls, image_id: str, image_folder: str, image_extension: str) -> str:
        """
        Функция, которая на основании даты и названия файла создаёт путь файла

        :param image_id: id нового изображения
        :param image_folder: название папки изображения
        :param image_extension: расширение изображения
        :return: путь нового изображения
        """
        logger.debug("Генерация относительного пути избражения: image_id = {}".format(image_id))
        image_name = f"{image_id}.{image_extension}"

        current_image_path = Path(IMAGES_PATH, image_folder)
        current_image_path.mkdir(exist_ok=True)
        return Path(image_folder, image_name).__str__()

    @classmethod
    async def delete_image_from_disk(cls, image_relative_path: str):
        """
        Функция для отладки, удаляет файл из указанной директории

        :param image_relative_path: относительный путь имеющегося на диске файла
        """
        logger.debug("Удаление существующегося файла с диска: путь к файлу = {}".format(image_relative_path))
        image_path = Path(IMAGES_PATH, image_relative_path)
        await aio_remove(image_path)
        try:
            await aio_rmdir(image_path.parent)
        except OSError as exc:
            pass

    @classmethod
    async def add_image(cls, db_async_session: AsyncSession, image: bytes, filename: str) -> str | None:
        """
        Функция, которая сохраняет изображение в каталог images, и добавляет путь изображения в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :param image: байтовое представление изображения
        :param filename: название и расширение изображения
        :return: id сохраненного изображения
        """
        logger.debug("Добаление нового изображения: filename = {}".format(filename))
        try:
            async with db_async_session.begin():
                image_id = uuid4().hex
                image_extension, image_folder = await cls.__get_extension_and_folder(filename)
                new_image = Image(
                    id=image_id,
                    folder=image_folder,
                    extension=image_extension
                )
                db_async_session.add(new_image)
                image_relative_path = await cls.__generate_image_path(image_id, image_folder, image_extension)
                await cls.__save_image_to_disk(image, image_relative_path)
            return new_image.id
        except (IntegrityError, OSError) as exc:
            return None

    @classmethod
    async def get_image_paths(cls, db_async_session: AsyncSession, tweet_id: int) -> List[str]:
        """
        Функция, которая извлекает из БД данные изображений по id твита, к которому они привязаны и
        возвращает список относительных путей файлов изображениq на диске

        :param db_async_session: асинхронная сессия подключения к БД
        :param tweet_id: id твита
        :return: список относительных путей изображений на диске
        """
        logger.debug("Получение информации из БД об файлах изображений: id твита = {}".format(tweet_id))

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(Image).where(Image.tweet_id == tweet_id)
            )
            images: List[Optional[Image]] = result.scalars().all()
            return [await cls.__generate_image_path(image.id, image.folder, image.extension) for image in images]

    @classmethod
    async def get_all_image_ids(cls, db_async_session: AsyncSession) -> List[str]:
        """
        Функция, возвращающая список id всех изображений в БД

        :param db_async_session: асинхронная сессия подключения к БД
        :return: список id всех изображений в БД
        """
        logger.debug("Получение списка id всех изображений в БД")

        async with db_async_session.begin():
            result = await db_async_session.execute(
                select(Image.id)
            )
            return result.scalars().all()