from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from typing import List, Optional
from .models import Message, MessageType
from .schemas import MessageCreate
from modules.auth.models import User

def create_message(db: Session, message_data: MessageCreate, sender_id: int) -> Message:
    db_message = Message(
        sender_id=sender_id,
        recipient_id=message_data.recipient_id,
        content=message_data.content,
        msg_type=message_data.msg_type
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Eager load sender for immediate return if needed
    db_message.sender_name = db.query(User).filter(User.id == sender_id).first().username
    return db_message

def get_chat_history(
    db: Session, 
    user_id: int, 
    recipient_id: Optional[int] = None, 
    skip: int = 0, 
    limit: int = 50
) -> List[Message]:
    
    query = db.query(Message).options(joinedload(Message.sender))

    if recipient_id:
        # Private Chat: (Sender=Me AND Recipient=Them) OR (Sender=Them AND Recipient=Me)
        query = query.filter(
            or_(
                and_(Message.sender_id == user_id, Message.recipient_id == recipient_id),
                and_(Message.sender_id == recipient_id, Message.recipient_id == user_id)
            )
        )
    else:
        # General Chat: Recipient is NULL
        query = query.filter(Message.recipient_id == None)

    messages = query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Populate sender_name flattened field
    for msg in messages:
        msg.sender_name = msg.sender.username if msg.sender else "Unknown"

    return messages
