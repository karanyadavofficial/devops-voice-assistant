from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()


@app.get("/")
def home():
    return {"message": "DevOps Voice Assistant is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test")
def test_page():
    return FileResponse("static/test.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Echo: {message}")
    except WebSocketDisconnect:
        print("Client disconnected")