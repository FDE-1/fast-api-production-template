from pydantic import BaseModel, ConfigDict


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    post_id: int
    content: str
