import os

from fastapi import status

from schemas.error import ErrorResult

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("DB_NAME")
DEMO_MODE = os.getenv("DEMO_MODE")

if POSTGRES_USER is None:
    POSTGRES_USER = "admin"

if POSTGRES_PASSWORD is None:
    POSTGRES_PASSWORD = "admin"

if POSTGRES_HOST is None:
    POSTGRES_HOST = "localhost"

if POSTGRES_PORT is None:
    POSTGRES_PORT = "5432"

if POSTGRES_DB is None:
    POSTGRES_DB = "twitter_db"

if DEMO_MODE is None:
    DEMO_MODE = False
else:
    if DEMO_MODE.lower() == "true":
        DEMO_MODE = True
    else:
        DEMO_MODE = False

MEDIA_FILE_NAME = "{image_id}.jpg"
GET_FOX_URL = "https://randomfox.ca/images/{image_id}.jpg"

GET_TEXT_URL = "https://fish-text.ru/get"
GET_TEXT_PARAMS = {"number": 1}

RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {
        400: {
            "model": ErrorResult,
            "description": "Необработанное исключение, которое может возникнуть на стороне сервера",
        }
    },
    status.HTTP_404_NOT_FOUND: {
        404: {
            "model": ErrorResult,
            "description": "Ошибка, возникающее при передаче в запросе id записей, которых не существует в БД",
        }
    },
    status.HTTP_409_CONFLICT: {
        409: {
            "model": ErrorResult,
            "description": "Ошибка добавления уже существующих данных в БД",
        }
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        422: {
            "model": ErrorResult,
            "description": "Ошибка валидации входных данных",
        },
    },
}
