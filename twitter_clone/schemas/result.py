from pydantic import BaseModel, Field


class Result(BaseModel):
    result: bool = Field(default=True)
