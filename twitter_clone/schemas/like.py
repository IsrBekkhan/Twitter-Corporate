from pydantic import BaseModel, ConfigDict


class Like(BaseModel):
    user_id: str
    name: str

    model_config = ConfigDict(from_attributes=True)
