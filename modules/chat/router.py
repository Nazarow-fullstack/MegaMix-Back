from typing import List, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from sqlalchemy.orm import Session
import json
import shutil
import pathlib
import uuid
from pydantic import ValidationError

from db_config import get_db
from modules.auth.dependencies import get_current_active_user
from modules.auth.models import User
from modules.auth.service import get_current_user_from_token 

from . import service, schemas
from .manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    # 1. Авторизация по токену из URL (Query Parameter)
    # Используем сервисную функцию, которая декодирует JWT и ищет пользователя в БД
    user = get_current_user_from_token(db, token)
    if not user:
        # 4003: Forbidden (Authenticated but not authorized, or token invalid)
        print("WS: Authentication failed. closing connection.")
        await websocket.close(code=4003)
        return

    # 2. Подключение
    await manager.connect(websocket, user.id)
    
    try:
        while True:
            # 3. Слушаем сообщения от клиента
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                print(f"WS: Received invalid JSON from user {user.id}")
                await websocket.send_json({"error": "Invalid JSON format"})
                continue
            except ValueError: 
                 # Starlette/FastAPI raises ValueError for invalid JSON sometimes
                 print(f"WS: Value Error (Invalid JSON) from user {user.id}")
                 continue

            # 4. Валидация и Сохранение в БД
            try:
                # Ensure msg_type is uppercase
                raw_msg_type = data.get("msg_type", "TEXT")
                if isinstance(raw_msg_type, str):
                    raw_msg_type = raw_msg_type.upper()
                
                message_data = schemas.MessageCreate(
                    content=data.get("content"),
                    msg_type=raw_msg_type,
                    recipient_id=data.get("recipient_id")
                )
                saved_message = service.create_message(db, message_data, user.id)
            except ValidationError as e:
                print(f"WS: Validation Error: {e}")
                await websocket.send_json({"error": "Validation Error", "details": str(e)})
                continue
            except Exception as e:
                print(f"WS: Error saving message: {e}")
                await websocket.send_json({"error": "Failed to process message"})
                continue
            
            # Подготавливаем ответ (Преобразуем в dict для JSON-сериализации)
            response_payload = schemas.MessageRead.model_validate(saved_message).model_dump(mode='json')
            response_payload['sender_name'] = user.username # Принудительно добавляем имя

            # 5. Отправляем
            if message_data.recipient_id:
                # Личное сообщение: Отправителю и Получателю
                await manager.send_personal_message(response_payload, message_data.recipient_id)
                
                # Отправляем себе копию (если это не я сам себе пишу)
                if message_data.recipient_id != user.id:
                    await manager.send_personal_message(response_payload, user.id)
            else:
                # Общий чат: Всем
                await manager.broadcast(response_payload)

    except WebSocketDisconnect:
        manager.disconnect(user.id)
    except Exception as e:
        print(f"WS Endpoint Critical Error: {e}")
        # Пытаемся отключить пользователя, если соединение еще живо
        manager.disconnect(user.id)

@router.get("/history", response_model=List[schemas.MessageRead])
def read_history(
    recipient_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получить историю сообщений.
    Если recipient_id не указан -> возвращает Общий чат.
    """
    return service.get_chat_history(db, current_user.id, recipient_id)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    # Create static/uploads directory if not exists
    upload_dir = pathlib.Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = pathlib.Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
        
    # Return URL
    return {"url": f"/static/uploads/{unique_filename}"}