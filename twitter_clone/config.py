from fastapi import status

from schemas.error import ErrorResult

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
