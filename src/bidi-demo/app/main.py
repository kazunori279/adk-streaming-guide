"""FastAPI application demonstrating ADK Bidi-streaming with WebSocket."""

import asyncio
import base64
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / ".env")

# ========================================
# Phase 1: Application Initialization (once at startup)
# ========================================

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Define your agent with built-in Google Search tool
agent = Agent(
    name="demo_agent",
    model=os.getenv("DEMO_AGENT_MODEL", "gemini-2.0-flash-exp"),
    tools=[google_search],
    instruction="You are a helpful assistant that can search the web."
)

# Define your session service
session_service = InMemorySessionService()

# Define your runner
runner = Runner(
    app_name="my-streaming-app",
    agent=agent,
    session_service=session_service
)

# ========================================
# HTTP Endpoints
# ========================================

@app.get("/")
async def root():
    """Serve the index.html page."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")

# ========================================
# WebSocket Endpoint
# ========================================

@app.websocket("/ws/{user_id}/{session_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, session_id: str) -> None:
    """WebSocket endpoint for bidirectional streaming with ADK."""
    await websocket.accept()

    # ========================================
    # Phase 2: Session Initialization (once per streaming session)
    # ========================================

    # Create RunConfig
    # Use AUDIO response modality for audio output, or TEXT for text-only mode
    run_config = RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],  # Changed to AUDIO to support voice responses
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig()
    )

    # Get or create session
    session = await session_service.get_session(
        app_name="my-streaming-app",
        user_id=user_id,
        session_id=session_id
    )
    if not session:
        await session_service.create_session(
            app_name="my-streaming-app",
            user_id=user_id,
            session_id=session_id
        )

    # Create LiveRequestQueue
    live_request_queue = LiveRequestQueue()

    # ========================================
    # Phase 3: Active Session (concurrent bidirectional communication)
    # ========================================

    async def upstream_task() -> None:
        """Receives messages from WebSocket and sends to LiveRequestQueue."""
        try:
            while True:
                # Receive message from WebSocket
                data: str = await websocket.receive_text()

                # Try to parse as JSON (for audio messages)
                try:
                    message = json.loads(data)

                    # Handle audio message
                    if message.get("type") == "audio":
                        # Decode base64 audio data
                        audio_data = base64.b64decode(message["data"])

                        # Send as realtime blob
                        audio_blob = types.Blob(
                            mime_type=message.get("mime_type", "audio/pcm;rate=16000"),
                            data=audio_data
                        )
                        live_request_queue.send_realtime(audio_blob)

                    # Handle text message in JSON format
                    elif message.get("type") == "text":
                        content = types.Content(parts=[types.Part(text=message["text"])])
                        live_request_queue.send_content(content)

                except json.JSONDecodeError:
                    # Not JSON, treat as plain text message
                    content = types.Content(parts=[types.Part(text=data)])
                    live_request_queue.send_content(content)

        except WebSocketDisconnect:
            # Client disconnected - signal queue to close
            pass

    async def downstream_task() -> None:
        """Receives Events from run_live() and sends to WebSocket."""
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            # Send event as JSON to WebSocket
            await websocket.send_text(
                event.model_dump_json(exclude_none=True, by_alias=True)
            )

    # Run both tasks concurrently
    try:
        await asyncio.gather(
            upstream_task(),
            downstream_task(),
            return_exceptions=True
        )
    finally:
        # ========================================
        # Phase 4: Session Termination
        # ========================================

        # Always close the queue, even if exceptions occurred
        live_request_queue.close()
