from schemas.result import Result


class ErrorResult(Result):
    error_type: str
    error_message: str

