"""FastAPI application demonstrating ADK Bidi-streaming with WebSocket."""

import asyncio
import base64
import json
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    logger.debug(f"WebSocket connection request: user_id={user_id}, session_id={session_id}")
    await websocket.accept()
    logger.debug(f"WebSocket connection accepted")

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
        # Note: session_resumption removed for Gemini API compatibility
    )
    logger.debug(f"RunConfig created: {run_config}")

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
        logger.debug("upstream_task started")
        try:
            while True:
                # Receive message from WebSocket
                data: str = await websocket.receive_text()
                logger.debug(f"upstream_task received: {data[:100]}...")

                # Try to parse as JSON (for audio messages)
                try:
                    message = json.loads(data)

                    # Handle audio message
                    if message.get("type") == "audio":
                        # Decode base64 audio data
                        audio_data = base64.b64decode(message["data"])
                        logger.debug(f"Sending audio chunk: {len(audio_data)} bytes")

                        # Send as realtime blob
                        audio_blob = types.Blob(
                            mime_type=message.get("mime_type", "audio/pcm;rate=16000"),
                            data=audio_data
                        )
                        live_request_queue.send_realtime(audio_blob)

                    # Handle text message in JSON format
                    elif message.get("type") == "text":
                        logger.debug(f"Sending text content: {message['text']}")
                        content = types.Content(parts=[types.Part(text=message["text"])])
                        live_request_queue.send_content(content)

                except json.JSONDecodeError:
                    # Not JSON, treat as plain text message
                    logger.debug(f"Sending plain text content: {data}")
                    content = types.Content(parts=[types.Part(text=data)])
                    live_request_queue.send_content(content)

        except WebSocketDisconnect:
            # Client disconnected - signal queue to close
            logger.debug("WebSocket disconnected in upstream_task")
            pass

    async def downstream_task() -> None:
        """Receives Events from run_live() and sends to WebSocket."""
        logger.debug("downstream_task started, calling runner.run_live()")
        try:
            logger.debug(f"Starting run_live with user_id={user_id}, session_id={session_id}")
            async for event in runner.run_live(
                user_id=user_id,
                session_id=session_id,
                live_request_queue=live_request_queue,
                run_config=run_config
            ):
                # Debug logging
                logger.debug(f"[SERVER] Received event: {event.event_type if hasattr(event, 'event_type') else 'unknown'}")
                if hasattr(event, 'input_transcription') and event.input_transcription:
                    logger.info(f"[SERVER] Input transcription: {event.input_transcription.text}")
                if hasattr(event, 'output_transcription') and event.output_transcription:
                    logger.info(f"[SERVER] Output transcription: {event.output_transcription.text}")

                # Send event as JSON to WebSocket
                logger.debug(f"Sending event to client")
                await websocket.send_text(
                    event.model_dump_json(exclude_none=True, by_alias=True)
                )
            logger.debug("run_live() generator completed")
        except Exception as e:
            logger.error(f"[SERVER ERROR] downstream_task exception: {e}", exc_info=True)

    # Run both tasks concurrently
    try:
        logger.debug("Starting asyncio.gather for upstream and downstream tasks")
        results = await asyncio.gather(
            upstream_task(),
            downstream_task(),
            return_exceptions=True
        )
        logger.debug(f"asyncio.gather completed with results: {results}")
    finally:
        # ========================================
        # Phase 4: Session Termination
        # ========================================

        # Always close the queue, even if exceptions occurred
        logger.debug("Closing live_request_queue")
        live_request_queue.close()
