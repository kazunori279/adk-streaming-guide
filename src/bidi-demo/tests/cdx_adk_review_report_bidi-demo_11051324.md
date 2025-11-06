# ADK Bidi‑Streaming Demo (src/bidi-demo) — Consistency & Design Review

Date: 2025-11-05 13:24 UTC
Target: src/bidi-demo
Reviewer: Codex (cdx)
Scope: Consistency with adk-python APIs and recommended design practices

## Summary

The demo cleanly demonstrates ADK’s upstream/downstream pattern over WebSocket with FastAPI. It uses `Runner.run_live()`, `LiveRequestQueue`, and `RunConfig` appropriately, and serializes events with `by_alias=True`. Audio input is streamed via base64 JSON and audio output is surfaced from events. A few small adjustments will make the app more robust and aligned with best practices (graceful shutdown on disconnects, model defaults, mode toggling, and minor logging fixes).

## Verified Consistencies

- `Runner.run_live(...)`: Used as async generator; yields ADK `Event` objects.
- `LiveRequestQueue`: Upstream uses `send_content()` for text and `send_realtime(Blob)` for audio.
- Event serialization: Uses `event.model_dump_json(exclude_none=True, by_alias=True)` for client‑side parsing.
- Transcription logging: Checks `event.input_transcription` and `event.output_transcription` before logging (matches ADK.
- Session service: `InMemorySessionService` used for a demo; fine for local usage.
- Static UI: Frontend connects a per‑session WebSocket and visualizes streaming events.

## Findings and Recommendations

1) Graceful shutdown on disconnects
- Current: Upstream catches `WebSocketDisconnect` and just logs; downstream catches generic exceptions but keeps looping. This can stall `run_live()` when the client disconnects.
- Recommendation:
  - Upstream: On `WebSocketDisconnect`, call `live_request_queue.close()` and return from the task.
  - Downstream: Wrap `websocket.send_text(...)` in a try/except; on error, `live_request_queue.close()` and `break` the loop.

2) Mode handling (TEXT vs AUDIO)
- Current: Server always sets `response_modalities=["AUDIO"]`, even before the user enables audio in the UI. In “text‑only” use, this can cause the model to respond with audio only.
- Recommendation: Pass a mode flag from the client (e.g., query `?mode=audio` or a first message) and set `run_config.response_modalities=["TEXT"]` for text mode, switching to `["AUDIO"]` only when audio is enabled.

3) Model default and Live support
- Current: Default model is `gemini-2.0-flash-exp`. Live/API feature support varies by model.
- Recommendation: Default to a Live‑compatible model known to support your chosen modality (e.g., a Gemini 2.5 Flash variant). Keep the env override but choose a safer default or validate via docs.

4) Session resumption comments
- Current: Code sets `session_resumption=types.SessionResumptionConfig()` with comments about transparent mode.
- Note: ADK uses transparent resumption on reconnect internally when a handle is available. Leaving the config as‑is is fine; prefer concise comment: “Enable session resumption; ADK handles reconnects transparently.”

5) Logging: `event_type` attribute
- Current: `logger.debug(f"[SERVER] Received event: {event.event_type if hasattr(event, 'event_type') else 'unknown'}")`
- Issue: ADK `Event` doesn’t define `event_type`.
- Recommendation: Log salient fields instead (e.g., `author`, `turn_complete`, presence of `content`/transcriptions).

6) Upstream JSON audio vs binary frames (optional)
- Current: Client sends base64 audio in JSON text frames. This is simpler but less efficient.
- Recommendation: For production, consider WebSocket binary frames for audio and JSON for metadata to reduce overhead.

7) Upstream chunking & Activity/VAD
- Current: No explicit VAD config and no manual `ActivityStart/End`; continuous streaming is fine when model VAD is enabled by default.
- Recommendation: If you later implement client‑side VAD, disable automatic VAD with `realtime_input_config=types.RealtimeInputConfig(disabled=True)` and send `ActivityStart/End` signals from the client.

8) InMemorySessionService scope
- Note: Good for demos. For persistence, switch to a database or Vertex AI session service per ADK docs.

## Concrete Patch Suggestions (server‑side excerpts)

Upstream task — close queue on disconnect:

```python
except WebSocketDisconnect:
    logger.debug("WebSocket disconnected in upstream_task")
    live_request_queue.close()
    return
```

Downstream task — close queue and break on send errors:

```python
try:
    await websocket.send_text(event.model_dump_json(exclude_none=True, by_alias=True))
except Exception:
    logger.warning("websocket send failed; closing queue and stopping stream", exc_info=True)
    live_request_queue.close()
    break
```

Mode parameter handling (example):

```python
# Read a mode from query params or a first control message
mode = websocket.query_params.get("mode", "text")
resp_mods = ["AUDIO"] if mode == "audio" else ["TEXT"]
run_config = RunConfig(streaming_mode=StreamingMode.BIDI, response_modalities=resp_mods)
```

## Conclusion

The demo is on the right track and consistent with ADK's streaming architecture. Implementing the graceful shutdown, aligning response modality with UI mode, tightening logging, and (optionally) improving transport efficiency will make it more robust and production‑lean.

---

## Fixes Applied (2025-11-06)

All recommendations have been implemented with an alternative architectural approach for issue 1.

### 1) Graceful shutdown on disconnects ✅

**Approach taken**: Instead of duplicating `close()` calls in multiple exception handlers, implemented a centralized cleanup pattern:

```python
async def upstream_task():
    # No try/except - let exceptions propagate
    while True:
        message = await websocket.receive()
        # ... handle messages ...

async def downstream_task():
    # No try/except - let exceptions propagate
    async for event in runner.run_live(...):
        # ... handle events ...

# Centralized exception handling
try:
    await asyncio.gather(upstream_task(), downstream_task())
except WebSocketDisconnect:
    logger.debug("Client disconnected normally")
except Exception as e:
    logger.error(f"Unexpected error in streaming tasks: {e}", exc_info=True)
finally:
    # Always close the queue
    live_request_queue.close()
```

**Benefits**:
- Single `close()` call in finally clause (DRY principle)
- `asyncio.gather()` automatically cancels other task on first exception
- Simpler code with centralized error handling
- Finally clause guarantees cleanup regardless of exception type

### 2) Mode handling (TEXT vs AUDIO) ✅

**Server-side** (main.py:83-86):
```python
mode = websocket.query_params.get("mode", "text").lower()
response_modalities = ["AUDIO"] if mode == "audio" else ["TEXT"]
```

**Client-side** (app.js:15-19):
```javascript
function getWebSocketUrl() {
  const mode = is_audio ? "audio" : "text";
  return "ws://" + window.location.host + "/ws/" + userId + "/" + sessionId + "?mode=" + mode;
}
```

**Result**: Initial connection uses `?mode=text` → TEXT responses. After "Start Audio" clicked, reconnects with `?mode=audio` → AUDIO responses.

### 3) Model default and Live support ✅

Updated default model to Live API recommended model with platform-specific guidance:

```python
# Default models for Live API with native audio support:
# - Gemini Live API: gemini-2.5-flash-native-audio-preview-09-2025
# - Vertex AI Live API: gemini-live-2.5-flash-preview-native-audio-09-2025
agent = Agent(
    name="demo_agent",
    model=os.getenv("DEMO_AGENT_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
    ...
)
```

**Benefits**: Native audio support, 128k context, thinking capabilities, verified Live API compatibility.

### 4) Session resumption comments ✅

Simplified to concise, accurate comment:

```python
# Enable session resumption; ADK handles reconnects transparently
session_resumption=types.SessionResumptionConfig()
```

### 5) Logging: `event_type` attribute ✅

Replaced non-existent `event_type` with actual event JSON:

**Before**:
```python
logger.debug(f"[SERVER] Received event: {event.event_type if hasattr(event, 'event_type') else 'unknown'}")
```

**After**:
```python
event_json = event.model_dump_json(exclude_none=True, by_alias=True)
logger.debug(f"[SERVER] Event: {event_json}")
await websocket.send_text(event_json)
```

**Benefits**: Logs complete event data, no duplication, shows exactly what client receives.

**Documentation fix**: Updated docs/part3_run_live.md to remove incorrect reference to `event_type` field.

### 6) Upstream JSON audio vs binary frames ✅

Implemented WebSocket binary frames for audio streaming:

**Server-side** (main.py:122-153):
```python
message = await websocket.receive()

if "bytes" in message:
    audio_data = message["bytes"]  # Binary frame
    audio_blob = types.Blob(mime_type="audio/pcm;rate=16000", data=audio_data)
    live_request_queue.send_realtime(audio_blob)

elif "text" in message:
    json_message = json.loads(message["text"])  # JSON frame
    # ... handle text content ...
```

**Client-side** (app.js:646-650):
```javascript
function audioRecorderHandler(pcmData) {
  if (websocket && websocket.readyState === WebSocket.OPEN && is_audio) {
    websocket.send(pcmData);  // Send as binary frame
  }
}
```

**Benefits**: ~33% smaller payload (no base64), faster performance, production-ready pattern.

**Cleanup**: Removed unused `base64` import from server and `arrayBufferToBase64()` function from client.

### 7) Upstream chunking & Activity/VAD ℹ️

No changes required. Current implementation uses model's automatic VAD, which is appropriate for this demo. Comment added to guide future enhancements if client-side VAD is needed.

### 8) InMemorySessionService scope ℹ️

No changes required. Appropriate for demo purposes. Production guidance remains in documentation.

---

