"""
FastAPI-based sample: ADK bidirectional streaming (Part 2 demo)

Features demonstrated:
- LiveRequestQueue bridging sync producers → async consumer
- Runner.run_live(...) async generator of Event objects
- RunConfig options: modalities, transcription, VAD, proactivity, affective dialog, session resumption
- Interactive HTML UI at "/" with WebSocket ("/ws") and SSE ("/sse") endpoints
- Interactive SSE support with POST endpoints ("/sse-send", "/sse-close")
- Credentials provided via UI (no environment variables required)
- Mutual exclusivity: WebSocket and SSE cannot be active simultaneously

Run:
  uvicorn streaming_app:app --reload --port 8000

The web UI at http://localhost:8000 allows you to:
- Choose backend: Gemini API (Google AI Studio) or Vertex AI (Google Cloud)
- Enter credentials directly in the browser
- Select Live-capable models from the dropdown
- Choose connection type: WebSocket or SSE (mutually exclusive)
- Configure RunConfig options (transcription, VAD, proactivity, affective dialog, session resumption)
- Use LiveRequestQueue controls: send_content() and close() with both WebSocket and SSE
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

from google.adk import Runner
from google.adk.agents.live_request_queue import LiveRequest, LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agent.agent import create_streaming_agent


APP_NAME = "part2-demo"
DEFAULT_USER_ID = "demo-user"
DEFAULT_SESSION_ID = "demo-session"

# Default model for fallback when not specified in UI
# Prefer a Live-capable model to avoid bidi errors
DEFAULT_MODEL = "gemini-2.0-flash-live-001"


# Simple in-memory session service for demo use
SESSION_SERVICE = InMemorySessionService()

# Active SSE sessions: Maps session_id to LiveRequestQueue for interactive SSE communication.
# This allows POST endpoints (/sse-send, /sse-close) to send messages to active SSE sessions.
active_sse_sessions: dict[str, LiveRequestQueue] = {}


async def ensure_session(user_id: str, session_id: str) -> None:
    sess = await SESSION_SERVICE.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not sess:
        await SESSION_SERVICE.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )


def build_runner(model: str) -> Runner:
    return Runner(
        app_name=APP_NAME,
        agent=create_streaming_agent(model),
        session_service=SESSION_SERVICE,
    )


def default_run_config(
    *,
    text_only: bool = True,
    enable_input_transcription: bool = False,
    enable_output_transcription: bool = False,
    enable_vad: bool = False,
    enable_proactivity: bool = False,
    enable_affective: bool = False,
    enable_session_resumption: bool = False,
) -> RunConfig:
    response_modalities = ["TEXT"] if text_only else ["TEXT", "AUDIO"]
    rc = RunConfig(
        response_modalities=response_modalities,
        streaming_mode=StreamingMode.BIDI,
    )
    if enable_input_transcription:
        rc.input_audio_transcription = types.AudioTranscriptionConfig(enabled=True)
    if enable_output_transcription:
        rc.output_audio_transcription = types.AudioTranscriptionConfig(enabled=True)
    if enable_vad:
        rc.realtime_input_config = types.RealtimeInputConfig(
            voice_activity_detection=types.VoiceActivityDetectionConfig(enabled=True)
        )
    if enable_affective:
        rc.enable_affective_dialog = True
    if enable_proactivity:
        rc.proactivity = types.ProactivityConfig()
    if enable_session_resumption:
        rc.session_resumption = types.SessionResumptionConfig(transparent=True)
    return rc


app = FastAPI(title="ADK Bidi-streaming demo app")


@app.get("/")
async def index() -> FileResponse:
    """Serve the main HTML UI from static file."""
    return FileResponse("static/index.html")



@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


@app.websocket("/ws")
async def ws_handler(ws: WebSocket,
                    model: Optional[str] = None,
                    use_vertexai: Optional[str] = None,
                    api_key: Optional[str] = None,
                    gcp_project: Optional[str] = None,
                    gcp_location: Optional[str] = None,
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    text_only: bool = True,
                    in_transcription: bool = False,
                    out_transcription: bool = False,
                    vad: bool = False,
                    proactivity: bool = False,
                    affective: bool = False,
                    resume: bool = False):
    """WebSocket endpoint for real-time bidirectional streaming.

    Establishes a WebSocket connection for real-time communication with the agent.
    Messages can be sent as plain text (converted to Content) or as JSON matching
    LiveRequest format (for close signals and other control messages).

    Note: WebSocket and SSE connections are mutually exclusive in the UI.

    Query parameters:
        model: Model name to use (defaults to DEFAULT_MODEL)
        use_vertexai: "true" for Vertex AI, "false" for Gemini API
        api_key: Google API key (for Gemini API)
        gcp_project: GCP project ID (for Vertex AI)
        gcp_location: GCP location (for Vertex AI)
        text_only: Enable text-only mode (default: True)
        in_transcription: Enable input audio transcription
        out_transcription: Enable output audio transcription
        vad: Enable voice activity detection
        proactivity: Enable proactive responses
        affective: Enable affective dialog
        resume: Enable session resumption
    """
    await ws.accept()

    # Determine identity and ensure session exists
    uid = user_id or DEFAULT_USER_ID
    sid = session_id or DEFAULT_SESSION_ID
    await ensure_session(uid, sid)

    # Use model from query param or fallback to default
    selected_model = model or DEFAULT_MODEL

    # Set credentials dynamically from request parameters
    import os
    old_env = {}
    try:
        if use_vertexai is not None:
            old_env['GOOGLE_GENAI_USE_VERTEXAI'] = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')
            os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = use_vertexai.upper()

        if use_vertexai == 'true':
            # Vertex AI credentials
            if gcp_project:
                old_env['GOOGLE_CLOUD_PROJECT'] = os.environ.get('GOOGLE_CLOUD_PROJECT')
                os.environ['GOOGLE_CLOUD_PROJECT'] = gcp_project
            if gcp_location:
                old_env['GOOGLE_CLOUD_LOCATION'] = os.environ.get('GOOGLE_CLOUD_LOCATION')
                os.environ['GOOGLE_CLOUD_LOCATION'] = gcp_location
        else:
            # Gemini API credentials
            if api_key:
                old_env['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')
                os.environ['GOOGLE_API_KEY'] = api_key

        # Build per-connection queue and run config
        live_queue = LiveRequestQueue()
        rc = default_run_config(
            text_only=text_only,
            enable_input_transcription=in_transcription,
            enable_output_transcription=out_transcription,
            enable_vad=vad,
            enable_proactivity=proactivity,
            enable_affective=affective,
            enable_session_resumption=resume,
        )

        runner = build_runner(selected_model)

        async def forward_events():
            """Stream events from agent's run_live() to WebSocket client."""
            try:
                async for event in runner.run_live(
                    user_id=uid,
                    session_id=sid,
                    live_request_queue=live_queue,
                    run_config=rc,
                ):
                    await ws.send_text(
                        event.model_dump_json(exclude_none=True, by_alias=True)
                    )
            except Exception as e:  # noqa: BLE001 (demo-only logging)
                # Forward exceptions as a final log line (demo purposes)
                await safe_ws_send(ws, json.dumps({"error": str(e)}))

        async def consume_messages():
            """Consume incoming WebSocket messages and forward to LiveRequestQueue."""
            try:
                while True:
                    data = await ws.receive_text()
                    # Try parsing as full LiveRequest (for close signals, etc.); fallback to plain text
                    try:
                        req = LiveRequest.model_validate_json(data)
                        live_queue.send(req)
                        if req.close:
                            break
                        continue
                    except Exception:
                        pass

                    # Treat as a simple text turn
                    content = types.Content(parts=[types.Part(text=data)])
                    live_queue.send_content(content)
            except WebSocketDisconnect:
                pass
            finally:
                # Graceful termination signal for the session
                live_queue.close()

        forward_task = asyncio.create_task(forward_events())
        consumer_task = asyncio.create_task(consume_messages())

        # Keep the handler alive until one side completes
        done, pending = await asyncio.wait(
            {forward_task, consumer_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for t in pending:
            t.cancel()

    finally:
        # Restore original environment variables
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


async def safe_ws_send(ws: WebSocket, text: str) -> None:
    try:
        await ws.send_text(text)
    except Exception:
        pass


def _sse_format(data: str) -> str:
    return f"data: {data}\n\n"


@app.get("/sse")
async def sse(
    model: Optional[str] = None,
    use_vertexai: Optional[str] = None,
    api_key: Optional[str] = None,
    gcp_project: Optional[str] = None,
    gcp_location: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    q: Optional[str] = None,
    text_only: bool = True,
    in_transcription: bool = False,
    out_transcription: bool = False,
    vad: bool = False,
    proactivity: bool = False,
    affective: bool = False,
    resume: bool = False,
):
    """Interactive SSE endpoint: streams events with support for send_content() and close().

    This endpoint opens an SSE connection and streams events from the agent. Unlike traditional
    SSE which is unidirectional, this implementation supports bidirectional communication through
    companion POST endpoints:
    - POST /sse-send: Send messages to the active session via LiveRequestQueue.send_content()
    - POST /sse-close: Gracefully close the session via LiveRequestQueue.close()

    The LiveRequestQueue is stored in active_sse_sessions during the connection lifecycle,
    enabling interactive communication similar to WebSocket but using standard HTTP.

    Query parameters:
        q: Optional initial message to send when connection opens
        model: Model name to use (defaults to DEFAULT_MODEL)
        use_vertexai: "true" for Vertex AI, "false" for Gemini API
        api_key: Google API key (for Gemini API)
        gcp_project: GCP project ID (for Vertex AI)
        gcp_location: GCP location (for Vertex AI)
        text_only: Enable text-only mode (default: True)
        in_transcription: Enable input audio transcription
        out_transcription: Enable output audio transcription
        vad: Enable voice activity detection
        proactivity: Enable proactive responses
        affective: Enable affective dialog
        resume: Enable session resumption
    """
    uid = user_id or DEFAULT_USER_ID
    sid = session_id or DEFAULT_SESSION_ID
    await ensure_session(uid, sid)

    # Use model from query param or fallback to default
    selected_model = model or DEFAULT_MODEL

    # Set credentials dynamically from request parameters
    import os
    old_env = {}
    if use_vertexai is not None:
        old_env['GOOGLE_GENAI_USE_VERTEXAI'] = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')
        os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = use_vertexai.upper()

    if use_vertexai == 'true':
        # Vertex AI credentials
        if gcp_project:
            old_env['GOOGLE_CLOUD_PROJECT'] = os.environ.get('GOOGLE_CLOUD_PROJECT')
            os.environ['GOOGLE_CLOUD_PROJECT'] = gcp_project
        if gcp_location:
            old_env['GOOGLE_CLOUD_LOCATION'] = os.environ.get('GOOGLE_CLOUD_LOCATION')
            os.environ['GOOGLE_CLOUD_LOCATION'] = gcp_location
    else:
        # Gemini API credentials
        if api_key:
            old_env['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')
            os.environ['GOOGLE_API_KEY'] = api_key

    # Create LiveRequestQueue for this SSE connection
    live_queue = LiveRequestQueue()

    # Store session for interactive communication via POST endpoints
    # This enables /sse-send and /sse-close to interact with this session
    active_sse_sessions[sid] = live_queue

    rc = default_run_config(
        text_only=text_only,
        enable_input_transcription=in_transcription,
        enable_output_transcription=out_transcription,
        enable_vad=vad,
        enable_proactivity=proactivity,
        enable_affective=affective,
        enable_session_resumption=resume,
    )
    runner = build_runner(selected_model)

    def cleanup():
        """Clean up SSE session resources and restore environment."""
        live_queue.close()
        # Remove from active sessions to prevent further POST interactions
        if sid in active_sse_sessions:
            del active_sse_sessions[sid]
        # Restore original environment variables
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    async def event_gen():
        try:
            if q:
                content = types.Content(parts=[types.Part(text=q)])
                live_queue.send_content(content)
            async for event in runner.run_live(
                user_id=uid,
                session_id=sid,
                live_request_queue=live_queue,
                run_config=rc,
            ):
                yield _sse_format(event.model_dump_json(exclude_none=True, by_alias=True))
        except Exception as e:  # noqa: BLE001
            yield _sse_format(json.dumps({"error": str(e)}))
        finally:
            cleanup()

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/sse-send")
async def sse_send(request: Request):
    """Send a message to an active SSE session via LiveRequestQueue.send_content().

    This endpoint enables bidirectional communication with SSE connections by allowing
    clients to send messages to an active session. The message is delivered through the
    LiveRequestQueue associated with the session.

    Request body (JSON):
        session_id: Session ID (defaults to "demo-session")
        message: Text message to send to the agent

    Returns:
        JSON response with status or error message
    """
    try:
        data = await request.json()
        session_id = data.get("session_id", DEFAULT_SESSION_ID)
        message = data.get("message", "")

        if not message:
            return {"error": "Message is required"}

        live_queue = active_sse_sessions.get(session_id)
        if not live_queue:
            return {"error": "Session not found or not active"}

        # Send message to agent
        content = types.Content(parts=[types.Part(text=message)])
        live_queue.send_content(content)

        return {"status": "sent", "message": message}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


@app.post("/sse-close")
async def sse_close(request: Request):
    """Close an active SSE session gracefully via LiveRequestQueue.close().

    This endpoint sends a close signal to an active SSE session, triggering graceful
    termination of the agent's run_live() generator. The session will be cleaned up
    and removed from active_sse_sessions.

    Request body (JSON):
        session_id: Session ID (defaults to "demo-session")

    Returns:
        JSON response with status or error message
    """
    try:
        data = await request.json()
        session_id = data.get("session_id", DEFAULT_SESSION_ID)

        live_queue = active_sse_sessions.get(session_id)
        if not live_queue:
            return {"error": "Session not found or not active"}

        # Send close signal to agent
        live_queue.send(LiveRequest(close=True))

        return {"status": "close signal sent"}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
