# ADK Bidi-streaming Guide — Part 3 Review (Consistency with adk-python)

Date: 2025-11-05 13:24 UTC
Target: docs/part3_run_live.md
Reviewer: Codex (cdx)
Scope: Technical correctness vs adk-python main (src/google/adk/*), API fidelity, example accuracy, and style conformance per STYLES.md

## Summary

Part 3 effectively explains `run_live()` event handling and matches ADK’s implementation in most areas: method signature, event streaming, tool execution, sequential agent completion, and session resumption. Suggested edits focus on clarifying memory characteristics, qualifying “pause” behavior for long-running tools, improving serialization guidance, fixing a minor artifact service example, and avoiding brittle line-number references.

## Verified Consistencies (adk-python)

- Signature and flow: `Runner.run_live(user_id, session_id, live_request_queue, run_config)` yields `Event` as an async generator; `session` parameter is deprecated. Source: google.adk.runners.
- Event pipeline: BaseLlmFlow `run_live` establishes a live connection, sends history, forwards upstream queue data, and yields events from `receive()`. Source: google.adk.flows.llm_flows.base_llm_flow.
- Event flags and content: `partial`, `turn_complete`, `interrupted`, transcriptions (`input_transcription`, `output_transcription`) map 1:1 with `LlmResponse` and are surfaced via `Event`. Source: google.adk.models.llm_response, google.adk.events.event.
- Tool execution: Function calls are detected and executed automatically; results are emitted as function response events. Calls are parallelized with `asyncio.gather`. Source: google.adk.flows.llm_flows.functions.
- Streaming tools: Tools with a `LiveRequestQueue` parameter get an injected queue; ADK inspects tool signatures and tracks `ActiveStreamingTool`. Source: google.adk.runners (inspection/injection), google.adk.agents.active_streaming_tool.
- SequentialAgent live completion: ADK injects a `task_completed()` tool per sub-agent to signal completion and transition. Source: google.adk.agents.sequential_agent.
- Session resumption: Live resumption handle is captured and reused; transparent resumption supported. Source: base_llm_flow.run_live and gemini_llm_connection.

## Issues and Fixes

1) “Memory usage stays constant” claim is too strong
- Issue: `run_live()` itself does not buffer, but sessions append events; depending on session service (e.g., in-memory), process memory can grow with conversation length.
- Fix: Reword to “`run_live()` streams events without internal buffering; overall memory depends on your session persistence implementation.”

2) Long-running tools “pause” wording
- Issue: States that ADK pauses the conversation until long-running tool completes.
- Code: Pause logic (`should_pause_invocation`) applies to resumable async flow; `run_live()` continues streaming and marks long-running tool IDs on events.
- Fix: Qualify: “In resumable async flows, ADK can pause after long-running calls. In live flows, events continue; use `long_running_tool_ids` to reflect pending operations.”

3) Serialization guidance should include aliases
- Issue: Examples use `event.model_dump_json(exclude_none=True)` only.
- Code: Event uses camelCase aliases; clients typically expect camelCase.
- Fix: Recommend `by_alias=True` in examples (e.g., `model_dump_json(exclude_none=True, by_alias=True)`).

4) Artifact service example uses non-existent API
- Issue: Example calls `context.artifact_service.save(data)`.
- Code: BaseArtifactService defines `save_artifact(app_name, user_id, filename, artifact, session_id, custom_metadata)`.
- Fix: Replace with a minimal `save_artifact(...)` example or remove to avoid confusion.

5) Line-number references in docs
- Issue: Mentions exact lines in `runners.py` and `functions.py`.
- Risk: Line numbers drift frequently.
- Fix: Remove line numbers; reference modules/functions by name.

6) Clarify author semantics
- Issue: Noted implicitly, but helpful to state: when the model emits user transcriptions, author is `"user"`; otherwise author is the agent’s name (not `'model'`).
- Fix: Add a note in the event handling section.

7) Session resumption scope
- Issue: “Error recovery: session resumption” is accurate but could mention the supported mode.
- Fix: Add: “ADK supports transparent session resumption; enable via `RunConfig.session_resumption`.”

8) Diagram parameter completeness
- Issue: Mermaid shows `runner.run_live(queue, config)`.
- Fix: Consider labeling with `user_id/session_id` to reflect required identity inputs, e.g., `run_live(user_id, session_id, queue, config)`.

## Concrete Edit Suggestions (ready-to-apply)

- Streaming characteristics:
  - Change “no buffering, memory stays constant” to: “Events are streamed without internal buffering. Overall memory depends on session persistence (e.g., in-memory vs database).”

- Long-running tools:
  - Update text to: “In resumable async flows, ADK pauses after long‑running calls. In live flows, streaming continues; `long_running_tool_ids` indicate pending operations and clients can display appropriate UI.”

- Serialization examples:
  - Use `event.model_dump_json(exclude_none=True, by_alias=True)` in all network send examples.

- Artifact service snippet:
  - Replace with:
    ```python
    await context.artifact_service.save_artifact(
        app_name=context.session.app_name,
        user_id=context.session.user_id,
        session_id=context.session.id,
        filename="result.bin",
        artifact=types.Part(inline_data=types.Blob(mime_type=mime, data=data)),
    )
    ```

- Remove line numbers in code references; keep module/function references only.

- Event author note:
  - Add: “Transcription events have author `user`; model responses/events use the agent’s name as `author`.”

- Session resumption:
  - Add: “Only transparent resumption is supported currently; configure via `RunConfig.session_resumption`.”

- Diagram label:
  - Replace `runner.run_live(queue, config)` with `runner.run_live(user_id, session_id, queue, config)`.

## Cross-checks with Code

- `Runner.run_live` defaults `response_modalities` to `['AUDIO']` when unset; docs can optionally mention this to avoid confusion when expecting audio.
- In `base_llm_flow.run_live`, transfer-to-agent triggers closing the current connection and then continues with the new agent (handled in `_postprocess_live`); docs align with transparent multi-agent streaming.
- Function calls are merged and executed in parallel; `merge_parallel_function_response_events` composes multiple responses correctly.

## Fixes Applied

Date: 2025-11-05

### Issue 1: Memory usage claim (FIXED ✅)
**Location**: Line 13 in `docs/part3_run_live.md`

Changed:
```
Memory usage stays constant regardless of conversation length
```

To:
```
Events are streamed without internal buffering. Overall memory depends on
session persistence (e.g., in-memory vs database)
```

### Issue 2: Long-running tools pause behavior (FIXED ✅)
**Location**: Line 814 in `docs/part3_run_live.md`

Changed:
```
Mark them with `is_long_running=True`, and ADK will pause the conversation
until the tool completes.
```

To:
```
Mark them with `is_long_running=True`. In resumable async flows, ADK can pause
after long-running calls. In live flows, streaming continues; `long_running_tool_ids`
indicate pending operations and clients can display appropriate UI.
```

### Issue 3: Serialization guidance (FIXED ✅)
**Locations**: Lines 640, 680, 683, 688, 693, 743, 750 in `docs/part3_run_live.md`

Added `by_alias=True` to all `model_dump_json()` examples:
- Basic example: `event.model_dump_json(by_alias=True)`
- Serialization options: All examples now include `by_alias=True`
- Audio transmission optimization: Both examples updated

This ensures camelCase field names for JavaScript/TypeScript clients.

### Issue 4: Artifact service example (FIXED ✅)
**Location**: Lines 936-942 in `docs/part3_run_live.md`

Changed:
```python
artifact_id = context.artifact_service.save(data)
```

To:
```python
await context.artifact_service.save_artifact(
    app_name=context.session.app_name,
    user_id=context.session.user_id,
    session_id=context.session.id,
    filename="result.bin",
    artifact=types.Part(inline_data=types.Blob(mime_type="application/octet-stream", data=data)),
)
```

Now uses the correct `save_artifact()` API with all required parameters.

### Issue 6: Author semantics (FIXED ✅)
**Location**: Line 138 in `docs/part3_run_live.md`

Added note in Key Fields section:
```
📝 **Author Semantics**: Transcription events have author `"user"`; model
responses/events use the agent's name as `author` (not `"model"`). See Event
Authorship for details.
```

### Issue 7: Session resumption scope (FIXED ✅)
**Location**: Line 84 in `docs/part3_run_live.md`

Changed:
```
Error Recovery: Session resumption (if enabled) handles transient failures
```

To:
```
Error Recovery: ADK supports transparent session resumption; enable via
`RunConfig.session_resumption` to handle transient failures
```

### Issue 8: Diagram parameter completeness (FIXED ✅)
**Location**: Line 46 in `docs/part3_run_live.md`

Changed:
```
runner.run_live(queue, config)
```

To:
```
runner.run_live(user_id, session_id, queue, config)
```

Mermaid diagram now shows all required identity parameters.

### Remaining Issues

Issue 5: Line-number references - Not fixed (requires broader decision on reference style)

## Conclusion

Part 3 is technically solid and consistent with adk-python. The edits above improve precision around memory/pause behavior, event serialization, and small examples, while avoiding brittle references.

