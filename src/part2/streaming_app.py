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
  export ADK_MODEL_NAME=gemini-2.0-flash-exp
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
    # Enhanced UI with verbose state tracking and error display
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>ADK Streaming Demo</title>
    <style>
      body { font-family: sans-serif; margin: 2rem; background: #f5f5f5; }
      .container { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
      h2 { margin-top: 0; color: #333; }
      #status {
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-weight: bold;
        display: inline-block;
      }
      #status.disconnected { background: #fee; color: #c00; }
      #status.connecting { background: #ffe; color: #880; }
      #status.connected { background: #efe; color: #080; }
      #stats {
        display: inline-block;
        margin-left: 1rem;
        color: #666;
        font-size: 0.9em;
      }
      #log {
        white-space: pre-wrap;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        height: 400px;
        overflow: auto;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.85em;
        line-height: 1.4;
      }
      .row { margin: 0.75rem 0; }
      .row label { display: inline-block; width: 120px; font-weight: 500; }
      input[type="text"] {
        padding: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 0.9em;
      }
      button {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        background: #4CAF50;
        color: white;
        cursor: pointer;
        font-weight: 500;
        margin-right: 0.5rem;
      }
      button:hover { background: #45a049; }
      button:disabled { background: #ccc; cursor: not-allowed; }
      #disconnect, #close { background: #f44336; }
      #disconnect:hover, #close:hover { background: #da190b; }
      .log-info { color: #4EC9B0; }
      .log-error { color: #f48771; font-weight: bold; }
      .log-sent { color: #ce9178; }
      .log-partial { color: #9cdcfe; }
      .log-complete { color: #c586c0; }
      .log-turn-complete { color: #dcdcaa; font-weight: bold; }
    </style>
  </head>
  <body>
    <div class="container">
      <h2>ADK Streaming (Part 2)</h2>
      <div>
        <span id="status" class="disconnected">● Disconnected</span>
        <span id="stats">Messages: <span id="msg-count">0</span> | Events: <span id="event-count">0</span></span>
      </div>
      <div class="row">
        <label>WebSocket URL:</label>
        <input id="wsurl" type="text" size="50" value="ws://" />
        <button id="connect">Connect</button>
        <button id="disconnect" disabled>Disconnect</button>
      </div>
      <div class="row">
        <label>Message:</label>
        <input id="text" type="text" size="50" placeholder="Type a message..." />
        <button id="send" disabled>Send</button>
        <button id="close" disabled>Close (graceful)</button>
      </div>
      <div class="row">
        <button id="clear-log">Clear Log</button>
      </div>
      <div id="log"></div>
    </div>
    <script>
      let ws = null;
      let msgCount = 0;
      let eventCount = 0;

      const statusEl = document.getElementById('status');
      const connectBtn = document.getElementById('connect');
      const disconnectBtn = document.getElementById('disconnect');
      const sendBtn = document.getElementById('send');
      const closeBtn = document.getElementById('close');
      const textInput = document.getElementById('text');

      const updateStatus = (state, text) => {
        statusEl.className = state;
        statusEl.textContent = text;
      };

      const updateButtons = (connected) => {
        connectBtn.disabled = connected;
        disconnectBtn.disabled = !connected;
        sendBtn.disabled = !connected;
        closeBtn.disabled = !connected;
      };

      const log = (message, className = '') => {
        const el = document.getElementById('log');
        const line = document.createElement('div');
        if (className) line.className = className;
        line.textContent = message;
        el.appendChild(line);
        el.scrollTop = el.scrollHeight;
      };

      const logInfo = (msg) => log(`[INFO] ${msg}`, 'log-info');
      const logError = (msg) => log(`[ERROR] ${msg}`, 'log-error');
      const logSent = (msg) => log(`[SENT] ${msg}`, 'log-sent');

      document.getElementById('wsurl').value = `ws://${location.host}/ws`;

      document.getElementById('connect').onclick = () => {
        const url = document.getElementById('wsurl').value;
        updateStatus('connecting', '● Connecting...');
        logInfo(`Connecting to ${url}`);

        try {
          ws = new WebSocket(url);

          ws.onopen = () => {
            updateStatus('connected', '● Connected');
            updateButtons(true);
            logInfo('WebSocket connection established');
          };

          ws.onclose = (event) => {
            updateStatus('disconnected', '● Disconnected');
            updateButtons(false);
            if (event.wasClean) {
              logInfo(`Connection closed cleanly (code=${event.code}, reason=${event.reason || 'none'})`);
            } else {
              logError(`Connection died (code=${event.code})`);
            }
          };

          ws.onerror = (error) => {
            logError('WebSocket error occurred');
            console.error('WebSocket error:', error);
          };

          ws.onmessage = (event) => {
            eventCount++;
            document.getElementById('event-count').textContent = eventCount;

            try {
              const data = JSON.parse(event.data);

              // Check for error messages
              if (data.error) {
                logError(`Server error: ${data.error}`);
                return;
              }

              // Detect event type and log accordingly
              if (data.turnComplete) {
                log(`[TURN COMPLETE] invocationId=${data.invocationId}`, 'log-turn-complete');
              } else if (data.partial) {
                const text = data.content?.parts?.[0]?.text || '';
                log(`[PARTIAL] ${text}`, 'log-partial');
              } else if (data.content?.role === 'model') {
                const text = data.content?.parts?.[0]?.text || '';
                log(`[COMPLETE] ${text}`, 'log-complete');
              } else {
                log(event.data);
              }
            } catch (e) {
              // Not JSON or parsing failed
              log(event.data);
            }
          };
        } catch (error) {
          logError(`Failed to create WebSocket: ${error.message}`);
          updateStatus('disconnected', '● Disconnected');
          updateButtons(false);
        }
      };

      document.getElementById('disconnect').onclick = () => {
        if (ws) {
          logInfo('Disconnecting...');
          ws.close();
        }
      };

      document.getElementById('send').onclick = () => {
        const text = textInput.value.trim();
        if (!text) return;
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          logError('Cannot send: WebSocket not connected');
          return;
        }

        ws.send(text);
        msgCount++;
        document.getElementById('msg-count').textContent = msgCount;
        logSent(text);
        textInput.value = '';
      };

      textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          document.getElementById('send').click();
        }
      });

      document.getElementById('close').onclick = () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          logError('Cannot close: WebSocket not connected');
          return;
        }
        logInfo('Sending graceful close signal');
        ws.send(JSON.stringify({ close: true }));
      };

      document.getElementById('clear-log').onclick = () => {
        document.getElementById('log').innerHTML = '';
        msgCount = 0;
        eventCount = 0;
        document.getElementById('msg-count').textContent = '0';
        document.getElementById('event-count').textContent = '0';
        logInfo('Log cleared');
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

