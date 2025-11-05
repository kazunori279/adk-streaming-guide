# ADK Bidi-streaming Guide — Part 2 Review (Consistency with adk-python)

Date: 2025-11-05 13:24 UTC
Target: docs/part2_live_request_queue.md
Reviewer: Codex (cdx)
Scope: Technical correctness vs adk-python main (src/google/adk/*), API fidelity, example accuracy, and style conformance per STYLES.md

## Summary

Part 2 accurately presents LiveRequestQueue as the upstream channel and largely matches the implementation in adk-python. Method names, message envelope fields, and lifecycle semantics (activity signals, close) align with the code. Recommendations focus on clarifying thread-safety boundaries, tempering claims about image/video, correcting a diagram omission, and tightening a couple of statements for precision.

## Verified Consistencies (adk-python)

- API surface: LiveRequestQueue methods `send_content`, `send_realtime`, `send_activity_start`, `send_activity_end`, `close`, and `send` exist with the described behavior (google.adk.agents.live_request_queue).
- LiveRequest fields: `content`, `blob`, `activity_start`, `activity_end`, `close` as documented. Convenience methods construct one-field requests.
- Close semantics: When a `LiveRequest(close=True)` is dequeued, BaseLlmFlow closes the LLM connection and returns from the sender loop.
- Activity signals: Mapped to Gemini Live API via `send_realtime(ActivityStart/ActivityEnd)` in the model connection.
- Ordering: FIFO queue behavior from asyncio.Queue is preserved; no internal coalescing.
- Run loop integration: Runner.run_live consumes from LiveRequestQueue while BaseLlmFlow orchestrates model send/receive and event streaming.

## Issues and Fixes

1) Mutual exclusivity wording is too strong
- Issue: States `content` and `blob` are mutually exclusive and Live API will reject requests with both set.
- Code: BaseLlmFlow sends realtime input (blob/activity) first, then content if present, as two frames on the same connection. There’s no explicit ADK-side rejection; model behavior may accept both in sequence.
- Fix: Rephrase to recommend sending one field per LiveRequest for clarity, but note that ADK will transmit both if provided (as separate frames). Prefer the convenience methods to avoid mixing.

2) Image/video streaming claim
- Issue: “streaming audio/image/video via send_realtime()”.
- Code: Input path is generic `types.Blob`, but ADK’s built-in processing and caching explicitly target audio; output-side caching has a TODO to support video. Claiming full image/video streaming may overpromise.
- Fix: Reword to “audio (and other binary blobs, model-dependent)”, and add a note that video/image handling may be model- and app-specific; ADK currently focuses on audio for transcription and caching.

3) Thread-safety phrasing vs summary
- Issue: The summary and closing sections call the interface “thread-safe”, while later sections correctly warn that asyncio.Queue is not thread-safe and show `loop.call_soon_threadsafe()`.
- Fix: Change wording to “safe within the owning event loop thread; for cross-thread access use loop.call_soon_threadsafe()”. Avoid calling the interface “thread-safe” without qualification.

4) Cross-thread example — loop ownership nuance
- Issue: The example uses `asyncio.get_event_loop()` but doesn’t emphasize that you must schedule onto the loop that owns the queue.
- Code: LiveRequestQueue creates an asyncio.Queue on the current thread’s event loop in its constructor. Cross-thread `.put_nowait()` isn’t safe.
- Fix: Add a short note: create LiveRequestQueue on the main async loop and keep a reference to that loop; use that loop in `call_soon_threadsafe()`.

5) Diagram omission: send_activity_end()
- Issue: Mermaid “LiveRequestQueue Methods” shows send_activity_start but not send_activity_end.
- Fix: Add `send_activity_end` in the methods panel with ActivityEnd.

6) Duplicate sentence
- Issue: The sentence “For production applications, prefer keeping all LiveRequestQueue operations within async functions on the same event loop thread.” appears twice.
- Fix: Remove the duplicate.

7) Backpressure suggestion uses a private attribute
- Issue: Suggests checking `live_request_queue._queue.qsize()`.
- Code: `_queue` is an internal attribute. While it works, it’s private.
- Fix: Add a caution that `_queue` is internal and may change; treat it as a pragmatic workaround until a public accessor exists.

## Concrete Edit Suggestions (ready-to-apply)

- Mutual exclusivity paragraph:
  - Replace “mutually exclusive… backend will reject” with: “Do not mix `content` and `blob` in the same LiveRequest. ADK will forward both sequentially if you do, but it’s clearer and safer to send them as separate requests. Prefer `send_content()` or `send_realtime()` to avoid mixing.”

- Image/video wording:
  - Change “audio/image/video” to “audio (and other binary blobs, model-dependent)”. Add a note: “ADK’s built-in transcription and caching focus on audio; video/image handling depends on your model and app code.”

- Thread-safety wording:
  - In the Summary and Summary (end), replace “thread-safe interface” with “an interface safe on one event loop; use `loop.call_soon_threadsafe()` for cross-thread producers.”
  - In cross-thread section, explicitly say: “Create LiveRequestQueue on the main loop and pass that loop into background threads; schedule with `loop.call_soon_threadsafe()`.”

- Mermaid diagram:
  - Add another method box: `send_activity_end` → ActivityEnd, and an arrow to `activity_start/end` in the container.

- Remove duplicate sentence in the cross-thread section.

- Backpressure note:
  - Append: “Note: `_queue` is an internal attribute and may change in future releases; use with caution.”

## Cross-checks with Code

- Methods/fields and names align with google.adk.agents.live_request_queue.LiveRequestQueue and LiveRequest.
- BaseLlmFlow._send_to_model sends ActivityStart/End, then Blob, and then Content (if present) per request dequeued.
- BaseLlmFlow caches input/output audio and integrates transcription events; video is not yet handled in output caching.
- Runner.run_live defaults response_modalities to ["AUDIO"] for live when not provided in RunConfig.

## Conclusion

Part 2 is accurate on the essentials. Updating the highlighted sections will better reflect actual behavior (especially mutual exclusivity and media claims), prevent confusion around thread-safety, and fix small clarity issues.

