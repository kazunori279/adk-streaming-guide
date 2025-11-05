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

The demo is on the right track and consistent with ADK’s streaming architecture. Implementing the graceful shutdown, aligning response modality with UI mode, tightening logging, and (optionally) improving transport efficiency will make it more robust and production‑lean.

