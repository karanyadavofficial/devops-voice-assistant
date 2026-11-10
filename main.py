from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serves files from the static/ folder at /static/...
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return {"message": "DevOps Voice Assistant is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test")
def test_page():
    return FileResponse("static/test.html")


@app.get("/voice")
def voice_page():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    while True:
        message = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            print("Client disconnected")
            break
        if message.get("bytes") is not None:
            # Audio chunk: echo it straight back
            await websocket.send_bytes(message["bytes"])
        elif message.get("text") is not None:
            await websocket.send_text(f"Echo: {message['text']}")
