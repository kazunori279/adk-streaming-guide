# ADK Bidi-streaming Guide — Part 5 Review (Consistency with adk-python)

Date: 2025-11-05 13:24 UTC
Target: docs/part5_audio_and_video.md
Reviewer: Codex (cdx)
Scope: Technical correctness vs adk-python main (src/google/adk/*), API fidelity, example accuracy, and style conformance per STYLES.md

## Summary

Part 5 is broadly accurate on audio usage and maps to ADK’s behavior for sending audio blobs, receiving audio inline_data, and transcription/VAD/proactivity wiring via RunConfig. Key edits should clarify defaults (VAD/transcription), scope image/video to input, avoid brittle model identifiers, and fix a cross-reference.

## Verified Consistencies (adk-python)

- Audio input path: `LiveRequestQueue.send_realtime(types.Blob)` forwards to the Live connection; ADK does no transcoding. Source: base_llm_flow._send_to_model.
- Audio output path: Events include audio via inline_data; ADK caches output audio (when enabled) and yields events. Source: base_llm_flow._receive_from_model.
- Transcription: Input/output transcription events (`event.input_transcription`, `event.output_transcription`) are surfaced as separate fields. Source: gemini_llm_connection.receive + TranscriptionManager.
- VAD/activity: ADK passes through `ActivityStart/End` and supports `realtime_input_config` for VAD configuration. Source: base_llm_flow._send_to_model and basic processor.
- Proactivity/affective dialog: RunConfig fields (`proactivity`, `enable_affective_dialog`) are copied to Live connect config; behavior is model-dependent. Source: _BasicLlmRequestProcessor.

## Issues and Fixes

1) “VAD enabled by default” phrasing
- Issue: The doc states VAD is enabled by default and needs no config.
- Code: ADK does not set VAD; defaults are governed by the Live API. ADK only forwards `realtime_input_config` if provided.
- Fix: Reword to: “VAD behavior is model-defined. Configure with `realtime_input_config`. Use `ActivityStart/End` when you explicitly disable VAD or implement client-side VAD.”

2) “Transcription enabled by default” phrasing
- Issue: Section says transcription is enabled by default in RunConfig.
- Code: Defaults are not globally enabled. In live multi-agent flows ADK ensures transcription defaults for agent transfer; otherwise you must set RunConfig `input_audio_transcription`/`output_audio_transcription` yourself.
- Fix: Reword: “Enable transcription via RunConfig. ADK enables input/output transcription by default only in live multi-agent scenarios to support agent transfer.” Provide explicit enable/disable examples.

3) Image/video scope
- Issue: Wording suggests general image/video streaming. ADK’s built-ins focus on audio. Input `Blob` supports images/video, but output handling/caching is audio-only and there’s no built-in video output from models.
- Fix: Clarify: “Image/video are supported as input blobs; output handling and persistence are currently audio-focused. Any video/image postprocessing is application-specific.”

4) Model identifiers in proactivity note
- Issue: Uses preview model names (e.g., gemini-2.5-flash-native-audio-preview-09-2025).
- Risk: Names drift; increases maintenance.
- Fix: Replace with guidance: “Native audio models on Gemini Live support proactivity/affective dialog; half-cascade models typically do not. Verify current availability in official docs.”

5) Cross-reference to Part 4 “Feature Support Matrix”
- Issue: Part 5 links to Part 4’s “Feature Support Matrix”; Part 4 has no such section/anchor.
- Fix: Update link to a valid section in Part 4 (e.g., StreamingMode, session resumption, or remove the reference), or add the matrix in Part 4.

6) Buffering/coalescing phrasing
- Issue: “LiveRequestQueue buffers chunks and sends them efficiently.”
- Code: ADK enqueues and forwards each request; there is no coalescing/batching.
- Fix: Optionally clarify: “ADK forwards each chunk promptly; upstream should pace chunk sizes/rates.”

7) Output sample rate statement
- Issue: Declares 24kHz as output rate.
- Note: This follows Live API docs, but is platform-defined. ADK passes through bytes.
- Fix: Qualify with “per current Live API docs; verify model-specific formats.”

## Concrete Edit Suggestions (ready-to-apply)

- VAD default wording:
  - Replace “VAD is enabled by default…no configuration needed” with: “VAD defaults are determined by the Live API and model. Configure via `types.RealtimeInputConfig`. Use manual `ActivityStart/End` when you disable VAD or implement client-side VAD.”

- Transcription defaults:
  - Replace “Transcription is enabled by default in RunConfig” with: “Enable transcription explicitly via RunConfig. ADK auto-enables input/output transcription only for live multi-agent to support agent transfer.”

- Image/video scope:
  - Add note: “ADK currently persists and caches audio only; image/video output handling is app-specific.”

- Proactivity models:
  - Replace preview model names with generic guidance and link to official docs.

- Part 4 link:
  - Change the reference to a valid section or remove the link.

- Buffering phrasing:
  - Optional: “ADK forwards each chunk; there is no coalescing. Choose chunk sizes to meet latency/bandwidth goals.”

- Output sample rate:
  - Add: “Output sample rate is per model/platform documentation.”

## Cross-checks with Code

- `_send_to_model` forwards `ActivityStart/End`, audio blobs, and content; no format conversion.
- `_receive_from_model` surfaces audio inline_data and transcription events; caches audio only.
- `_BasicLlmRequestProcessor` maps RunConfig to Live connect config (transcription, VAD, proactivity, affective dialog).
- `Runner._new_invocation_context_for_live` sets transcription defaults only for live multi-agent scenarios.

## Conclusion

Part 5 is solid on audio usage and event handling. Tightening defaults (VAD/transcription), scoping image/video, and avoiding brittle model names/cross-refs will make it fully consistent with adk-python and resilient to SDK/model evolution.

