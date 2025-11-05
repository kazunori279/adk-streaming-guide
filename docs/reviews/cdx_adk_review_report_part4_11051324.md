# ADK Bidi-streaming Guide — Part 4 Review (Consistency with adk-python)

Date: 2025-11-05 13:24 UTC
Target: docs/part4_run_config.md
Reviewer: Codex (cdx)
Scope: Technical correctness vs adk-python main (src/google/adk/*), API fidelity, example accuracy, and style conformance per STYLES.md

## Summary

Part 4 explains RunConfig and platform behavior well. The majority aligns with adk-python: response modalities defaulting, BIDI vs SSE mapping, transcription/VAD/proactivity wiring, session resumption, and context window compression. Recommended edits clarify where behavior is product‑level vs code‑enforced, add missing CFC coverage, and tighten a few statements (e.g., max_llm_calls scope, Live multi‑agent defaults, save_live_audio scope).

## Verified Consistencies (adk-python)

- Defaults: In `Runner._new_invocation_context_for_live`, response_modalities defaults to `["AUDIO"]` when unset for live; in multi‑agent live, ADK ensures input/output transcription defaults. Source: google.adk.runners.
- Mapping to LiveConnectConfig: `_BasicLlmRequestProcessor` copies fields from RunConfig (`speech_config`, `response_modalities`, `input/output_audio_transcription`, `realtime_input_config`, `enable_affective_dialog`, `proactivity`, `session_resumption`, `context_window_compression`). Source: google.adk.flows.llm_flows.basic.
- BIDI vs SSE endpoints: Live uses `llm.connect()` (websocket); SSE uses `llm.generate_content_async()` (HTTP). Source: google.adk.flows.llm_flows.base_llm_flow.
- Session resumption: ADK captures `live_session_resumption_update` and reconnects using a saved handle (transparent resumption). Source: base_llm_flow.run_live and gemini_llm_connection.
- save_live_audio: Audio cache and flush on control events; persistence into session/artifact services. Source: base_llm_flow + AudioCacheManager.

## Issues and Fixes

1) Missing coverage: Compositional Function Calling (CFC)
- Issue: Part 4 doesn’t mention `RunConfig.support_cfc`.
- Code: When `support_cfc=True`, ADK invokes the Live path even if `streaming_mode=SSE` because only Live supports CFC. Source: base_llm_flow._call_llm_async.
- Fix: Add a CFC section: “Set `support_cfc=True` (experimental). For SSE requests, ADK internally uses Live to enable CFC. Some models may not support CFC; ADK will raise if unsupported.”

2) max_llm_calls scope
- Issue: States “per run_live() invocation”.
- Code: Enforcement occurs when making standard LLM calls via `generate_content_async()` (SSE/async flows). Live sessions (`run_live`) do not currently increment this counter.
- Fix: Reword to: “Applies to non‑Live LLM calls (SSE / run_async). Live streaming sessions are not governed by this limit.” Optionally note alternative safeguards for live.

3) Session resumption mode phrasing
- Issue: Suggests not specifying transparent mode; code sets transparent mode on reconnect.
- Fix: Clarify: “ADK uses transparent session resumption under the hood during reconnect. Enable via `RunConfig.session_resumption`.”

4) Live multi‑agent defaults
- Enhancement: Mention that for live multi‑agent, ADK enables transcription defaults (input/output) when needed for agent transfer.

5) save_live_audio scope
- Enhancement: Note “currently only audio is persisted” per implementation; video persistence is not yet handled.

6) Terminology: client vs LLM connection
- Enhancement: Where stating “ADK handles reconnection,” clarify it handles the LLM Live connection; client WebSocket/SSE reconnection remains app responsibility.

7) Platform durations and “unlimited”
- Suggestion: Mark session duration claims (e.g., “unlimited with context window compression”) as platform behavior subject to official limits; ADK wires the configs but doesn’t enforce durations itself.

## Concrete Edit Suggestions (ready-to-apply)

- Add a subsection “Compositional function calling (experimental)” under StreamingMode or a new advanced section:
  - “Set `support_cfc=True` to enable CFC. For SSE mode, ADK routes through Live internally because only Live supports CFC.”

- Update max_llm_calls text:
  - “This limit applies to standard LLM calls (`generate_content_async`) in SSE/async flows. Live (`run_live`) sessions are not currently counted by this limiter.”

- Session resumption wording:
  - “ADK uses transparent resumption on reconnect when enabled via `RunConfig.session_resumption`.”

- Live multi‑agent note:
  - Add: “For live multi‑agent, ADK sets default input/output transcription to support agent transfer when needed.”

- save_live_audio note:
  - Add: “Currently only audio is persisted; video is not yet stored by default.”

- Clarify reconnection scope:
  - “ADK manages the model‑side Live connection; your app manages client WS/SSE reconnection.”

- Add a brief caution on platform durations:
  - “Context window compression and session durations are platform features; verify current limits in official docs.”

## Cross-checks with Code

- `RunConfig` fields match `run_config.py` and are appropriately mapped by the basic processor.
- `Runner._new_invocation_context_for_live` sets response/transcription defaults in live multi‑agent scenarios.
- `support_cfc` path in `_call_llm_async` uses Live under SSE for CFC.
- Audio persistence and control‑event flushes are implemented; video persistence is not.

## Conclusion

Part 4 is largely consistent with adk-python. Adding CFC coverage, clarifying `max_llm_calls` scope, noting live multi‑agent transcription defaults, and tightening language around resumption, persistence, and platform limits will make this section precise and production‑ready.

