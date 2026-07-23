import json
from jose import JWTError, jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.config import settings

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])

CONNECTED_CLIENTS: dict[int, WebSocket] = {}


async def broadcast_event(event_type: str, data: dict, target_user_ids: list[int] = None):
    message = json.dumps({"event": event_type, "data": data}, default=str)
    disconnected = []
    for user_id, ws in CONNECTED_CLIENTS.items():
        if target_user_ids and user_id not in target_user_ids:
            continue
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(user_id)
    for uid in disconnected:
        CONNECTED_CLIENTS.pop(uid, None)


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    CONNECTED_CLIENTS[user_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        CONNECTED_CLIENTS.pop(user_id, None)
