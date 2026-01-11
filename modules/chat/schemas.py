from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional

class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    RECEIPT = "RECEIPT"

class MessageBase(BaseModel):
    content: str
    msg_type: MessageType = MessageType.TEXT
    recipient_id: Optional[int] = None # Если None -> Общий чат

class MessageCreate(MessageBase):
    pass

class MessageRead(MessageBase):
    id: int
    sender_id: int
    created_at: datetime
    sender_name: str # Имя отправителя (мы его достанем из базы)

    model_config = ConfigDict(from_attributes=True)