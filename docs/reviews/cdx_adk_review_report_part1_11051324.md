# ADK Bidi-streaming Guide — Part 1 Review (Consistency with adk-python)

Date: 2025-11-05 13:24 UTC
Target: docs/part1_intro.md
Reviewer: Codex (cdx)
Scope: Technical correctness vs adk-python main (src/google/adk/*), API fidelity, example accuracy, and style conformance per STYLES.md

## Summary

Overall, Part 1 accurately describes ADK’s bidirectional streaming architecture and maps well to the actual ADK Python implementation. The core concepts (LiveRequestQueue, Runner.run_live(), async generator flow, event model, transcription, VAD, proactivity, session resumption) are consistent with the codebase. The FastAPI upstream/downstream pattern is aligned with how Runner.run_live is intended to be used.

Action items are mostly around tightening example code, a couple of link/wording corrections, and some documentation style fixes. No fundamental architectural mismatches were found.

## Verified Consistencies (adk-python)

- Live queue: google.adk.agents.live_request_queue.LiveRequestQueue and LiveRequest with content/blob/activity_start/activity_end/close are implemented as documented.
- Streaming entrypoint: google.adk.runners.Runner.run_live(user_id, session_id, live_request_queue, run_config) returns an async generator of Event, as shown in the example.
- Event model: google.adk.events.event.Event extends LlmResponse with camelCase aliases for JSON via model_dump_json(by_alias=True), as used in the example.
- LLM flow: google.adk.flows.llm_flows.base_llm_flow.BaseLlmFlow.run_live orchestrates send/receive, handles interruptions, turn_complete, function calls, and emits transcription events.
- Transcription and VAD knobs: RunConfig maps to LiveConnectConfig fields in _BasicLlmRequestProcessor (output/input transcription, realtime_input_config/VAD, proactivity, affective dialog, session resumption, context window compression).
- Session resumption: live_session_resumption_update is received and InvocationContext.live_session_resumption_handle is updated; reconnect path reuses the handle.
- Agent alias: google.adk.agents exposes Agent as an alias of LlmAgent; the “Agent vs LlmAgent” note is correct.
- FastAPI dependency and CLI: fastapi/starlette/uvicorn are required dependencies; the ADK CLI has a web server (google.adk.cli.adk_web_server).

## Issues and Fixes

1) Missing import in FastAPI example
- Issue: tools=[google_search] is used without import.
- Fix: add from google.adk.tools import google_search near other imports.

2) Model identifier looks unstable/speculative
- Issue: model="gemini-2.5-flash-native-audio-preview-09-2025" may not be a stable public name.
- Recommendation: prefer a known generally-available identifier, e.g. "gemini-2.5-flash". If the example needs audio, keep response_modalities=["AUDIO"] (default is AUDIO for live), or show both TEXT and AUDIO usage explicitly.

3) Link mis-target for session services
- Issue: “ADK Session Services documentation” points to googleapis.github.io/python-genai/... which is the GenAI SDK docs, not ADK session services.
- Fix: link to ADK docs, e.g. https://google.github.io/adk-docs/sessions/ and specific service pages (DatabaseSessionService, VertexAiSessionService) if available.

4) Over-broad wording on WebSocket management
- Issue: One paragraph implies ADK “abstracts away WebSocket management”. ADK manages the model-side Live API connection; application still manages client WebSockets.
- Fix: clarify that ADK handles LLM-side streaming connection and protocol translation; app code handles client WebSocket/SSE endpoints.

5) Upstream disconnect handling
- Issue: upstream_task swallows WebSocketDisconnect and relies on final cleanup to close the LiveRequestQueue. Downstream may attempt websocket.send after disconnect.
- Fix: in upstream_task, on WebSocketDisconnect: call live_request_queue.close() (idempotent) and cancel downstream or let downstream detect closure. Also, in downstream_task, guard sends or catch exceptions (noted later in “Production considerations” but worth tightening sample).

6) Show activity signals and audio usage
- Opportunity: Example only shows text messages. ADK supports ActivityStart/End and audio via send_realtime(types.Blob).
- Suggestion: Add a short snippet demonstrating sending ActivityStart/End and an audio chunk, plus how to set run_config.realtime_input_config and input/output transcription configs.

7) Section header casing vs STYLES.md
- Issue: Headers use Title Case (e.g., “Key Characteristics”, “FastAPI Application Example”). Style guide calls for sentence case for headers.
- Fix: convert to sentence case, e.g., “Key characteristics”, “FastAPI application example”, “Real-world applications”, etc.

8) Cross-file references
- Check: “Part 5: Proactivity and Affective Dialog” is referenced from the Live features bulleted list while proactivity knobs are in RunConfig (Part 4). If Part 5 is “Audio and video”, ensure cross-references point to the actual sections where proactivity/affective dialog are documented (likely in part4_run_config.md, and optionally mentioned in part5).
- Fix: adjust “Learn more” links to the correct target anchors.

9) SSE mention is high level only
- Suggestion: include a minimal SSE example (run_config.streaming_mode=StreamingMode.SSE) or link to the SSE section in Part 3, so readers see both bidi and one-way streaming patterns.

## Concrete Edit Suggestions (ready-to-apply)

- Imports (FastAPI example):
  - Add: from google.adk.tools import google_search
- Model (FastAPI example):
  - Replace model string with a stable, public model (e.g., "gemini-2.5-flash"). Optionally add a comment on AUDIO vs TEXT response_modalities.
- WebSocket cleanup (FastAPI example):
  - In upstream_task, on WebSocketDisconnect: call live_request_queue.close().
  - In downstream_task, catch RuntimeError/ConnectionClosed when sending, break the loop, and close the queue.
- Clarify scope of WebSocket management:
  - Reword the line that ADK abstracts away WebSocket management to specify “LLM-side streaming connection” management.
- Link corrections:
  - Replace “ADK Session Services documentation” link with https://google.github.io/adk-docs/sessions/.
- Add optional snippet (activity signals and audio):
  - live_request_queue.send_activity_start(); live_request_queue.send_realtime(types.Blob(...)); live_request_queue.send_activity_end().
  - Show run_config.input_audio_transcription/output_audio_transcription and realtime_input_config usage.
- Header casing:
  - Normalize all section/subsection titles to sentence case per STYLES.md.

## Example Patch (FastAPI snippet only)

```diff
 from fastapi import FastAPI, WebSocket, WebSocketDisconnect
 from google.adk.agents import Agent
 from google.adk.runners import Runner
 from google.adk.agents.run_config import RunConfig, StreamingMode
 from google.adk.agents.live_request_queue import LiveRequestQueue
 from google.adk.sessions import InMemorySessionService
+from google.adk.tools import google_search
 from google.genai import types
@@
-agent = Agent(
-    model="gemini-2.5-flash-native-audio-preview-09-2025",
-    tools=[google_search],
-    instruction="You are a helpful assistant that can search the web."
-)
+agent = Agent(
+    model="gemini-2.5-flash",  # Use a stable model name
+    tools=[google_search],
+    instruction="You are a helpful assistant that can search the web."
+)
@@
     async def upstream_task() -> None:
         """Receives messages from WebSocket and sends to LiveRequestQueue."""
         try:
             while True:
                 # Receive text message from WebSocket
                 data: str = await websocket.receive_text()
@@
                 live_request_queue.send_content(content)
         except WebSocketDisconnect:
-            # Client disconnected - signal queue to close
-            pass
+            # Client disconnected — close the queue to stop downstream
+            live_request_queue.close()
@@
     async def downstream_task() -> None:
         """Receives Events from run_live() and sends to WebSocket."""
-        async for event in runner.run_live(
+        async for event in runner.run_live(
             user_id=user_id,
             session_id=session_id,
             live_request_queue=live_request_queue,
             run_config=run_config
-        ):
-            # Send event as JSON to WebSocket
-            await websocket.send_text(
-                event.model_dump_json(exclude_none=True, by_alias=True)
-            )
+        ):
+            try:
+                # Send event as JSON to WebSocket
+                await websocket.send_text(
+                    event.model_dump_json(exclude_none=True, by_alias=True)
+                )
+            except Exception:
+                # Socket closed — stop streaming and close the queue
+                live_request_queue.close()
+                break
```

Optional: Show activity signals and audio

```python
# Mark the start/end of user speech explicitly (optional if VAD is enabled)
live_request_queue.send_activity_start()
# Send an audio chunk (PCM/WAV/MP3 etc.)
live_request_queue.send_realtime(types.Blob(data=audio_bytes, mime_type="audio/wav"))
live_request_queue.send_activity_end()

# Configure transcription/VAD and proactivity if desired
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    realtime_input_config=types.RealtimeInputConfig(voice_activity_detection=True),
    proactivity=types.ProactivityConfig(enabled=True),
)
```

## Notes

- Runner.run_live defaults response_modalities to ["AUDIO"] for live; the example sets TEXT. Both are valid; clarify intent in the text.
- Session ID generation behavior in InMemorySessionService matches the “auto-generate when None/empty” description.
- The Live reconnection loop uses a resumption handle when provided by the server. Wording should reflect that ADK manages model-side reconnection/resumption; client WS reconnection remains app responsibility.

## Conclusion

Part 1 is in strong shape and maps cleanly to adk-python internals. Applying the fixes above will improve example correctness, clarify responsibilities (client WS vs model Live connection), and align styling and links with the project’s documented standards.

