"""
FastAPI-based sample: ADK bidirectional streaming (Part 2 demo)

Features demonstrated:
- LiveRequestQueue bridging sync producers → async consumer
- Runner.run_live(...) async generator of Event objects
- RunConfig options: modalities, transcription, VAD
- Minimal HTML UI at "/" and a WebSocket endpoint at "/ws"

Run:
  uvicorn src.part2.streaming_app:app --reload --port 8000

Env:
  export GOOGLE_API_KEY=...           # or use ADC
  export ADK_MODEL_NAME=gemini-2.5-flash
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, PlainTextResponse

from google.adk import Agent, Runner
from google.adk.agents.live_request_queue import LiveRequest, LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types


APP_NAME = "part2-demo"
DEFAULT_USER_ID = "demo-user"
DEFAULT_SESSION_ID = "demo-session"

MODEL = os.getenv("ADK_MODEL_NAME", "gemini-2.5-flash")


def _build_agent() -> Agent:
    return Agent(
        name="demo_assistant",
        model=MODEL,
        instruction=(
            "You are a helpful assistant. Respond concisely and clearly."
        ),
        description="Minimal streaming assistant for Part 2 demo.",
        tools=[],
    )


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


def build_runner() -> Runner:
    return Runner(
        app_name=APP_NAME,
        agent=_build_agent(),
        session_service=SESSION_SERVICE,
    )


def default_run_config(
    *,
    text_only: bool = True,
    enable_input_transcription: bool = False,
    enable_output_transcription: bool = False,
    enable_vad: bool = False,
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
    return rc


app = FastAPI(title="ADK Part 2 Streaming Demo")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    # Minimal inline UI for quick manual testing
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>ADK Streaming Demo</title>
    <style>
      body { font-family: sans-serif; margin: 2rem; }
      #log { white-space: pre-wrap; background: #111; color: #ddd; padding: 1rem; height: 300px; overflow: auto; }
      .row { margin: 0.5rem 0; }
    </style>
  </head>
  <body>
    <h2>ADK Streaming (Part 2)</h2>
    <div class="row">
      <label>WebSocket URL: </label>
      <input id="wsurl" size="60" value="ws://" />
      <button id="connect">Connect</button>
      <button id="disconnect">Disconnect</button>
    </div>
    <div class="row">
      <input id="text" size="60" placeholder="Type a message" />
      <button id="send">Send</button>
      <button id="close">Close (graceful)</button>
    </div>
    <div id="log"></div>
    <script>
      const log = (m) => {
        const el = document.getElementById('log');
        el.textContent += m + "\n";
        el.scrollTop = el.scrollHeight;
      };
      let ws = null;
      document.getElementById('wsurl').value = `ws://${location.host}/ws`;
      document.getElementById('connect').onclick = () => {
        const url = document.getElementById('wsurl').value;
        ws = new WebSocket(url);
        ws.onopen = () => log('WS open');
        ws.onclose = () => log('WS closed');
        ws.onerror = (e) => log('WS error');
        ws.onmessage = (ev) => log(ev.data);
      };
      document.getElementById('disconnect').onclick = () => {
        if (ws) ws.close();
      };
      document.getElementById('send').onclick = () => {
        const t = document.getElementById('text').value;
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(t);
        document.getElementById('text').value = '';
      };
      document.getElementById('close').onclick = () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(JSON.stringify({ close: true }));
      };
    </script>
  </body>
</html>
"""


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz() -> str:
    return "ok"


@app.websocket("/ws")
async def ws_handler(ws: WebSocket,
                    user_id: Optional[str] = None,
                    session_id: Optional[str] = None,
                    text_only: bool = True,
                    in_transcription: bool = False,
                    out_transcription: bool = False,
                    vad: bool = False):
    await ws.accept()

    # Determine identity and ensure session exists
    uid = user_id or DEFAULT_USER_ID
    sid = session_id or DEFAULT_SESSION_ID
    await ensure_session(uid, sid)

    # Build per-connection queue and run config
    live_queue = LiveRequestQueue()
    rc = default_run_config(
        text_only=text_only,
        enable_input_transcription=in_transcription,
        enable_output_transcription=out_transcription,
        enable_vad=vad,
    )

    runner = build_runner()

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


async def safe_ws_send(ws: WebSocket, text: str) -> None:
    try:
        await ws.send_text(text)
    except Exception:
        pass

