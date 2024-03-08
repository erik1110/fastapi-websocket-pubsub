import os
import logging
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect
from app.websocket.socketManager import WebSocketManager

import json
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPI app")
templates = Jinja2Templates(directory="app/templates")

app = FastAPI()

# Adding the CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = WebSocketManager()

@app.get("/", response_class=HTMLResponse)
async def read_main(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/api/v1/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: int):
    print("process_id:", os.getpid())
    await socket_manager.add_user_to_room(room_id, websocket)
    message = {
        "user_id": user_id,
        "room_id": room_id,
        "message": f"User {user_id} connected to room - {room_id}"
    }
    await socket_manager.broadcast_to_room(room_id, json.dumps(message))
    try:
        while True:
            data = await websocket.receive_text()
            message = {
                "user_id": user_id,
                "room_id": room_id,
                "message": data
            }
            await socket_manager.broadcast_to_room(room_id, json.dumps(message))

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_room(room_id, websocket)

        message = {
            "user_id": user_id,
            "room_id": room_id,
            "message": f"User {user_id} disconnected from room - {room_id}"
        }
        await socket_manager.broadcast_to_room(room_id, json.dumps(message))

@app.get("/api1")
async def api1():
    logger.info("Processing API1 request")
    return {"message": "API1 response", "process_id": os.getpid()}

@app.get("/api2")
async def api2():
    logger.info("Processing API2 request")
    return {"message": "API2 response", "process_id": os.getpid()}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, reload=True)