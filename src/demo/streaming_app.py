"""
FastAPI-based sample: ADK bidirectional streaming (Part 2 demo)

Features demonstrated:
- LiveRequestQueue bridging sync producers → async consumer
- Runner.run_live(...) async generator of Event objects
- RunConfig options: modalities, transcription, VAD
- Minimal HTML UI at "/" and a WebSocket endpoint at "/ws"
- Credentials provided via UI (no environment variables required)

Run:
  uvicorn streaming_app:app --reload --port 8000

The web UI at http://localhost:8000 allows you to:
- Choose backend: Gemini API (Google AI Studio) or Vertex AI (Google Cloud)
- Enter credentials directly in the browser
- Select Live-capable models
- Configure RunConfig options (transcription, VAD, proactivity, etc.)

Model selection:
  You can set a default model via environment variable (optional):
  export ADK_MODEL_NAME=gemini-2.0-flash-live-001

  Or select from the dropdown in the UI.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

# Prefer a Live-capable default to avoid bidi errors
# See docs for alternatives (e.g., native audio preview models)
MODEL = os.getenv("ADK_MODEL_NAME", "gemini-2.0-flash-live-001")

# Startup hint if model likely won't support bidi/live
def _warn_if_non_live_model(model_name: str) -> None:
    name = (model_name or "").lower()
    looks_live = any(s in name for s in ["-live-", ":live:", "gemini-live", "native-audio", "flash-live-001"])
    if not looks_live:
        print(
            f"[Part 2 Demo] Warning: ADK_MODEL_NAME='{model_name}' may not support Live/bidi streaming. "
            "Prefer models like 'gemini-2.0-flash-live-001' (Gemini API) or 'gemini-live-2.5-flash-preview' (Vertex AI)."
        )

_warn_if_non_live_model(MODEL)


# Simple in-memory session service for demo use
SESSION_SERVICE = InMemorySessionService()


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
    await ws.accept()

    # Determine identity and ensure session exists
    uid = user_id or DEFAULT_USER_ID
    sid = session_id or DEFAULT_SESSION_ID
    await ensure_session(uid, sid)

    # Use model from query param or fallback to env var
    selected_model = model or MODEL

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
            try:
                while True:
                    data = await ws.receive_text()
                    # Try parsing full LiveRequest; fallback to plain text Content
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
    """Simple SSE endpoint: streams events; optional initial message via `q`.

    For interactive back-and-forth streaming, prefer the WebSocket endpoint.
    """
    uid = user_id or DEFAULT_USER_ID
    sid = session_id or DEFAULT_SESSION_ID
    await ensure_session(uid, sid)

    # Use model from query param or fallback to env var
    selected_model = model or MODEL

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
            # Restore original environment variables
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    return StreamingResponse(event_gen(), media_type="text/event-stream")
