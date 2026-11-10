import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing. Add it to your .env file.")

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-live-preview")

client = genai.Client(api_key=API_KEY, http_options=types.HttpOptions(api_version="v1beta"))

LIVE_CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": (
        "You are a friendly DevOps voice assistant. "
        "Keep your answers short and clear, like a helpful colleague."
    ),
}

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return {"message": "DevOps Voice Assistant is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/voice")
def voice_page():
    return FileResponse("static/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Browser connected")

    try:
        async with client.aio.live.connect(model=MODEL, config=LIVE_CONFIG) as session:
            print("Gemini session started")

            async def browser_to_gemini():
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        break
                    data = message.get("bytes")
                    if data:
                        await session.send_realtime_input(
                            audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                        )

            async def gemini_to_browser():
                while True:
                    async for response in session.receive():
                        content = response.server_content
                        if content and content.model_turn:
                            for part in content.model_turn.parts:
                                if part.inline_data and part.inline_data.data:
                                    await websocket.send_bytes(part.inline_data.data)

            tasks = [
                asyncio.create_task(browser_to_gemini()),
                asyncio.create_task(gemini_to_browser()),
            ]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()  # re-raises any error so we can see it

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        print("Browser disconnected")
