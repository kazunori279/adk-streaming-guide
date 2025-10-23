"""FastAPI-based sample: ADK bidirectional streaming demo.

Demonstrates WebSocket and SSE endpoints for interactive bidirectional streaming.
All ADK streaming API interactions are handled by the bidi_streaming module.

See README.md for setup instructions and usage examples.
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

from . import bidi_streaming


app = FastAPI(title="ADK Bidi-streaming demo app")


@app.get("/")
async def index() -> FileResponse:
    """Serve the main HTML UI from static file."""
    return FileResponse("static/index.html")


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


def _set_credentials(
    use_vertexai: Optional[str],
    api_key: Optional[str],
    gcp_project: Optional[str],
    gcp_location: Optional[str],
) -> dict[str, Optional[str]]:
    """Set environment variables for API credentials and return old values.

    Args:
        use_vertexai: "true" for Vertex AI, "false" for Gemini API
        api_key: Google API key (for Gemini API)
        gcp_project: GCP project ID (for Vertex AI)
        gcp_location: GCP location (for Vertex AI)

    Returns:
        Dictionary of old environment values to restore later
    """
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

    return old_env


def _restore_credentials(old_env: dict[str, Optional[str]]) -> None:
    """Restore original environment variables.

    Args:
        old_env: Dictionary of old environment values from _set_credentials()
    """
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@app.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
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
    resume: bool = False,
):
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
    uid = user_id or bidi_streaming.DEFAULT_USER_ID
    sid = session_id or bidi_streaming.DEFAULT_SESSION_ID
    await bidi_streaming.get_or_create_session(uid, sid)

    # Use model from query param or fallback to default
    selected_model = model or bidi_streaming.DEFAULT_MODEL

    # Set credentials dynamically from request parameters
    old_env = _set_credentials(use_vertexai, api_key, gcp_project, gcp_location)

    try:
        # Create LiveRequestQueue and run config
        live_queue = bidi_streaming.create_live_queue()
        run_config = bidi_streaming.create_run_config(
            text_only=text_only,
            enable_input_transcription=in_transcription,
            enable_output_transcription=out_transcription,
            enable_vad=vad,
            enable_proactivity=proactivity,
            enable_affective=affective,
            enable_session_resumption=resume,
        )

        runner = bidi_streaming.create_runner(selected_model)

        async def forward_events():
            """Stream events from agent to WebSocket client."""
            try:
                async for event in bidi_streaming.stream_agent_events(
                    runner=runner,
                    user_id=uid,
                    session_id=sid,
                    live_queue=live_queue,
                    run_config=run_config,
                ):
                    await ws.send_text(
                        event.model_dump_json(exclude_none=True, by_alias=True)
                    )
            except Exception as e:  # noqa: BLE001 (demo-only logging)
                # Forward exceptions as a final log line (demo purposes)
                await _safe_send(ws, json.dumps({"error": str(e)}))

        async def consume_messages():
            """Consume incoming WebSocket messages and forward to agent."""
            try:
                while True:
                    data = await ws.receive_text()
                    text, is_close = bidi_streaming.parse_text_or_live_request(data)

                    if is_close:
                        break

                    if text:
                        bidi_streaming.send_text_message(live_queue, text)

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
        _restore_credentials(old_env)


async def _safe_send(ws: WebSocket, text: str) -> None:
    """Send text to WebSocket with error handling."""
    try:
        await ws.send_text(text)
    except Exception:
        pass


def _format_sse(data: str) -> str:
    """Format data as SSE message."""
    return f"data: {data}\n\n"


@app.get("/sse")
async def sse_endpoint(
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
    """Interactive SSE endpoint: streams events with support for send and close.

    This endpoint opens an SSE connection and streams events from the agent. Unlike traditional
    SSE which is unidirectional, this implementation supports bidirectional communication through
    companion POST endpoints:
    - POST /sse-send: Send messages to the active session
    - POST /sse-close: Gracefully close the session

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
    uid = user_id or bidi_streaming.DEFAULT_USER_ID
    sid = session_id or bidi_streaming.DEFAULT_SESSION_ID
    await bidi_streaming.get_or_create_session(uid, sid)

    # Use model from query param or fallback to default
    selected_model = model or bidi_streaming.DEFAULT_MODEL

    # Set credentials dynamically from request parameters
    old_env = _set_credentials(use_vertexai, api_key, gcp_project, gcp_location)

    # Create LiveRequestQueue for this SSE connection
    live_queue = bidi_streaming.create_live_queue()

    # Store session for interactive communication via POST endpoints
    bidi_streaming.active_sse_sessions[sid] = live_queue

    run_config = bidi_streaming.create_run_config(
        text_only=text_only,
        enable_input_transcription=in_transcription,
        enable_output_transcription=out_transcription,
        enable_vad=vad,
        enable_proactivity=proactivity,
        enable_affective=affective,
        enable_session_resumption=resume,
    )
    runner = bidi_streaming.create_runner(selected_model)

    def cleanup():
        """Clean up SSE session resources and restore environment."""
        live_queue.close()
        # Remove from active sessions to prevent further POST interactions
        if sid in bidi_streaming.active_sse_sessions:
            del bidi_streaming.active_sse_sessions[sid]
        _restore_credentials(old_env)

    async def event_generator():
        """Generate SSE events from agent."""
        try:
            async for event in bidi_streaming.stream_agent_events(
                runner=runner,
                user_id=uid,
                session_id=sid,
                live_queue=live_queue,
                run_config=run_config,
                initial_message=q,
            ):
                yield _format_sse(event.model_dump_json(exclude_none=True, by_alias=True))
        except Exception as e:  # noqa: BLE001
            yield _format_sse(json.dumps({"error": str(e)}))
        finally:
            cleanup()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/sse-send")
async def sse_send_message(request: Request):
    """Send a message to an active SSE session.

    This endpoint enables bidirectional communication with SSE connections by allowing
    clients to send messages to an active session.

    Request body (JSON):
        session_id: Session ID (defaults to "demo-session")
        message: Text message to send to the agent

    Returns:
        JSON response with status or error message
    """
    try:
        data = await request.json()
        session_id = data.get("session_id", bidi_streaming.DEFAULT_SESSION_ID)
        message = data.get("message", "")

        if not message:
            return {"error": "Message is required"}

        live_queue = bidi_streaming.active_sse_sessions.get(session_id)
        if not live_queue:
            return {"error": "Session not found or not active"}

        # Send message to agent
        bidi_streaming.send_text_message(live_queue, message)

        return {"status": "sent", "message": message}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


@app.post("/sse-close")
async def sse_close_session(request: Request):
    """Close an active SSE session gracefully.

    This endpoint sends a close signal to an active SSE session, triggering graceful
    termination of the agent's streaming. The session will be cleaned up and removed
    from active_sse_sessions.

    Request body (JSON):
        session_id: Session ID (defaults to "demo-session")

    Returns:
        JSON response with status or error message
    """
    try:
        data = await request.json()
        session_id = data.get("session_id", bidi_streaming.DEFAULT_SESSION_ID)

        live_queue = bidi_streaming.active_sse_sessions.get(session_id)
        if not live_queue:
            return {"error": "Session not found or not active"}

        # Send close signal to agent
        bidi_streaming.send_close_signal(live_queue)

        return {"status": "close signal sent"}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}
