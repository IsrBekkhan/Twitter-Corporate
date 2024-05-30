from uuid import uuid4

from pydantic import BaseModel
from fastapi import UploadFile

from schemas.result import Result


class ImageResult(Result):
    media_id: str
