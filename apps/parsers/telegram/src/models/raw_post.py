from datetime import datetime
from pydantic import BaseModel


class RawPost(BaseModel):
    channel_username: str
    message_id: int
    text: str
    date: datetime
    url: str
