from pydantic import BaseModel, ConfigDict


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    content: str
