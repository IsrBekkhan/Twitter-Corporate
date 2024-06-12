from pydantic import Field
from schemas.result import Result


class ErrorResult(Result):
    result: bool = Field(default=False)
    error_type: str
    error_message: str

