from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Active connections: userid -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"WS: User {user_id} connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"WS: User {user_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except RuntimeError as e:
                # Socket might be closed/changed state
                print(f"WS Error sending to {user_id}: {e}")
                self.disconnect(user_id)
            except Exception as e:
                 print(f"WS Error sending to {user_id}: {e}")

    async def broadcast(self, message: dict):
        # Используем list(keys) для итерации, чтобы избежать ошибки изменения словаря во время итерации
        # если вдруг socket отвалится и вызовет disconnect
        for user_id in list(self.active_connections.keys()):
            websocket = self.active_connections.get(user_id)
            if websocket:
                try:
                    await websocket.send_json(message)
                except RuntimeError:
                    self.disconnect(user_id)
                except Exception as e:
                    print(f"WS Error broadcasting to {user_id}: {e}")

manager = ConnectionManager()
