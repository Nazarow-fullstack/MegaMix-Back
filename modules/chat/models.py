from enum import Enum
from sqlalchemy import String, Enum as SAEnum, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db_config import Base

class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"     
    RECEIPT = "RECEIPT"

class Message(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True) # Null = General Chat
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_type: Mapped[MessageType] = mapped_column(SAEnum(MessageType), default=MessageType.TEXT, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sender = relationship("modules.auth.models.User", foreign_keys=[sender_id])
    recipient = relationship("modules.auth.models.User", foreign_keys=[recipient_id])
