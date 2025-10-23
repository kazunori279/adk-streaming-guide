# Part 5: Understanding Events

ADK's event system is the foundation of real-time streaming interactions. Understanding how events flow through the system, what types of events you'll receive, and how to handle them enables you to build responsive, natural streaming applications.

## Event Emission Pipeline

Events flow through multiple layers before reaching your application:

1. **GeminiLlmConnection**: Generates `LlmResponse` objects
2. **LLM Flow**: Converts to `Event` objects with metadata
3. **Agent**: Passes through with optional state updates
4. **Runner**: Persists to session and yields to caller

Author semantics in live mode:
- Model responses are authored by the current agent (the `Event.author` is the agent name), not the literal string "model".
- Transcription events originating from user audio are authored as `"user"`.

### Event Types and Flags

ADK surfaces model and system signals as `Event` objects with helpful flags:

- `partial`: True for incremental text chunks; a non‑partial merged text event follows turn boundaries.
- `turn_complete`: Signals end of the model's current turn; often where merged text is emitted.
- `interrupted`: Model output was interrupted (e.g., by new user input); the flow flushes accumulated text if any.
- `input_transcription` / `output_transcription`: Streaming transcription events; emitted as stand‑alone events.
- Content parts with `inline_data` (audio) may be yielded for live audio output. By default, Runner does not persist these live audio response events.

Persistence in live mode:
- Runner skips appending model audio events to the session by default; audio persistence is controlled via `RunConfig.save_live_audio` and flushed on control events (e.g., turn completion).

**Troubleshooting:** If no events are arriving, ensure `runner.run_live(...)` is being iterated and the `LiveRequestQueue` is fed. Also verify that `Content` sent via `send_content()` has non-empty `parts`.

## Concurrent Processing Model

Behind the scenes, `run_live()` orchestrates bidirectional streaming through concurrent async tasks. This enables true bidirectional communication where input and output happen simultaneously:

```python
# Simplified internal pattern
async def streaming_session():
    # Input task: Client → Gemini
    input_task = asyncio.create_task(
        send_to_model(llm_connection, live_request_queue)
    )

    # Output task: Gemini → Client
    async for event in receive_from_model(llm_connection):
        yield event  # Real-time event streaming
```

**Sample code (Consuming events – from src/demo/app/bidi_streaming.py):**

> 📖 Source Reference: [src/demo/app/bidi_streaming.py](../src/demo/app/bidi_streaming.py)
> 📖 Source Reference (transport handlers): [src/demo/app/main.py](../src/demo/app/main.py)

```python
# Stream events as JSON strings and forward to client
async for event_json in session.stream_events_as_json():
    await ws.send_text(event_json)
```

## Backpressure and Flow Control

- Producers are not throttled by default: `LiveRequestQueue` is unbounded and accepts messages without blocking.
- Natural backpressure comes from awaits in the send/receive loops and from how quickly you consume `runner.run_live(...)`.
- Practical guidance:
  - Pace audio at the source (short, contiguous chunks) rather than large bursts.
  - Use `ActivityStart()`/`ActivityEnd()` to bound turns and reduce overlap; this is not byte‑rate throttling.
  - If you need hard limits, consider a bounded producer buffer (see Advanced example below).

## Connection Lifecycle

The streaming session follows a well-defined lifecycle using Python's async context manager pattern:

```python
async with llm.connect(llm_request) as llm_connection:
    # Bidirectional streaming session active
    await handle_streaming_conversation()
# Connection automatically closed
```

**Lifecycle Phases:**

1. **Setup**: Create LiveRequestQueue, configure RunConfig
2. **Connect**: Establish GeminiLlmConnection
3. **Stream**: Concurrent input/output processing
4. **Handle Events**: Process streaming events in real-time
5. **Cleanup**: Graceful connection termination

## Relationship with Regular agent.run()

| Feature | `agent.run()` | `agent.run_live()` |
|---------|---------------|-------------------|
| **Input** | Single message | LiveRequestQueue stream |
| **Output** | Final response | Event stream |
| **Timing** | Batch processing | Real-time streaming |
| **Interruption** | Not supported | Full interruption support |
| **Use Case** | Simple Q&A | Interactive conversations |

## Event Types and Handling

When you iterate over `runner.run_live()`, ADK streams `Event` objects that represent different aspects of the conversation. Understanding these events and their flags helps you build responsive, real-time applications.

**Event Types You'll Receive:**

**1. Text Response Events**

The most common event type, containing the model's text responses:

```python
async for event in runner.run_live(...):
    if event.content and event.content.parts:
        if event.content.parts[0].text:
            # Display streaming text to user
            text = event.content.parts[0].text

            # Check if this is partial (more text coming) or complete
            if event.partial:
                # Update UI with partial text (e.g., typing indicator)
                update_streaming_display(text)
            else:
                # Final merged text for this segment
                display_complete_message(text)
```

**Key Event Flags:**
- `event.partial`: `True` for incremental text chunks during streaming; `False` for complete merged text
- `event.turn_complete`: `True` when the model has finished its complete response
- `event.interrupted`: `True` when user interrupted the model's response

**2. Audio Events**

When `response_modalities` includes `"AUDIO"`, you'll receive audio data:

```python
async for event in runner.run_live(...):
    if event.content and event.content.parts:
        if event.content.parts[0].inline_data:
            # Stream audio to client for playback
            audio_data = event.content.parts[0].inline_data.data
            await play_audio(audio_data)
```

**3. Transcription Events**

When transcription is enabled in `RunConfig`, you receive transcriptions as separate events:

```python
async for event in runner.run_live(...):
    # User's spoken words (when input_audio_transcription enabled)
    if event.input_transcription:
        display_user_transcription(event.input_transcription)

    # Model's spoken words (when output_audio_transcription enabled)
    if event.output_transcription:
        display_model_transcription(event.output_transcription)
```

These enable accessibility features and conversation logging without separate transcription services.

**4. Tool Call Events**

When the model requests tool execution:

```python
async for event in runner.run_live(...):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_call:
                # Model is requesting a tool execution
                tool_name = part.function_call.name
                tool_args = part.function_call.args
                # ADK handles execution automatically
```

ADK processes tool calls automatically—you typically don't need to handle these directly unless implementing custom tool execution logic.

## Handling Interruptions and Turn Completion

Two critical event flags enable natural, human-like conversation flow in your application: `interrupted` and `turn_complete`. Understanding how to handle these flags is essential for building responsive streaming UIs.

### Interruption Handling

When users send new input while the model is still generating a response (common in voice conversations), you'll receive an event with `interrupted=True`:

```python
async for event in runner.run_live(...):
    if event.interrupted:
        # User interrupted the model's response
        # Stop displaying partial text, clear typing indicators
        stop_streaming_display()

        # Optionally: show interruption in UI
        show_user_interruption_indicator()
```

**Practical example:**

```
Model: "The weather in San Francisco is currently..."
User: [interrupts] "Actually, I meant San Diego"
→ event.interrupted=True received
→ Your app: stop rendering model response, clear UI
→ Model processes new input
Model: "The weather in San Diego is..."
```

**When to use interruption handling:**

- **Voice conversations**: Stop audio playback immediately when user starts speaking
- **Clear UI state**: Remove typing indicators and partial text displays
- **Conversation logging**: Mark which responses were interrupted (incomplete)
- **User feedback**: Show visual indication that interruption was recognized

### Turn Completion Handling

When the model finishes its complete response, you'll receive an event with `turn_complete=True`:

```python
async for event in runner.run_live(...):
    if event.turn_complete:
        # Model has finished its turn
        # Update UI to show "ready for input" state
        enable_user_input()
        hide_typing_indicator()

        # Mark conversation boundary in logs
        log_turn_boundary()
```

**Event Flag Combinations:**

Understanding how `turn_complete` and `interrupted` combine helps you handle all conversation states:

| Scenario | turn_complete | interrupted | Your App Should |
|----------|---------------|-------------|-----------------|
| Normal completion | True | False | Enable input, show "ready" state |
| User interrupted mid-response | False | True | Stop display, clear partial content |
| Interrupted at end | True | True | Same as normal completion (turn is done) |
| Mid-response (partial text) | False | False | Continue displaying streaming text |

**Practical Application:**

```python
async for event in runner.run_live(...):
    # Handle streaming text
    if event.content and event.content.parts and event.content.parts[0].text:
        if event.partial:
            # Show typing indicator, update partial text
            update_streaming_text(event.content.parts[0].text)
        else:
            # Display complete text chunk
            display_text(event.content.parts[0].text)

    # Handle interruption
    if event.interrupted:
        stop_audio_playback()
        clear_streaming_indicators()

    # Handle turn completion
    if event.turn_complete:
        # Model is done - enable user input
        show_input_ready_state()
        enable_microphone()
        # The loop will wait for next user input before continuing
```

**Common Use Cases:**

- **UI state management**: Show/hide "ready for input" indicators, typing animations, microphone states
- **Audio playback control**: Know when to stop rendering audio chunks from the model
- **Conversation logging**: Mark clear boundaries between turns for history/analytics
- **Streaming optimization**: Stop buffering when turn is complete

## Serializing Events to JSON

ADK `Event` objects are Pydantic models, which means they come with powerful serialization capabilities. The `model_dump_json()` method is particularly useful for streaming events over network protocols like WebSockets or Server-Sent Events (SSE).

### Using event.model_dump_json()

The `model_dump_json()` method serializes an `Event` object to a JSON string:

```python
async for event in runner.run_live(...):
    # Serialize event to JSON string
    event_json = event.model_dump_json()

    # Send to WebSocket client
    await websocket.send_text(event_json)

    # Or send via SSE
    yield f"data: {event_json}\n\n"
```

**What gets serialized:**

- All event metadata (author, event_type, timestamp)
- Content (text, audio data, function calls)
- Event flags (partial, turn_complete, interrupted)
- Transcription data (input_transcription, output_transcription)
- Tool execution information

### Serialization Options

Pydantic's `model_dump_json()` supports several useful parameters:

```python
# Exclude None values for smaller payloads
event_json = event.model_dump_json(exclude_none=True)

# Custom exclusions (e.g., skip large binary audio)
event_json = event.model_dump_json(
    exclude={'content': {'parts': {'__all__': {'inline_data'}}}}
)

# Include only specific fields
event_json = event.model_dump_json(
    include={'content', 'author', 'turn_complete', 'interrupted'}
)

# Pretty-printed JSON (for debugging)
event_json = event.model_dump_json(indent=2)
```

### Selective Serialization

When streaming to clients, you often want to customize what gets sent. Here's a common pattern:

```python
async def stream_events_to_client(runner, websocket):
    async for event in runner.run_live(...):
        # Handle audio separately (too large for JSON)
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("audio/"):
                    # Send binary audio via separate message
                    await websocket.send_bytes(part.inline_data.data)

                    # Send event metadata without audio
                    event_json = event.model_dump_json(
                        exclude={'content': {'parts': {'__all__': {'inline_data'}}}}
                    )
                    await websocket.send_text(event_json)
                    continue

        # For non-audio events, send everything
        event_json = event.model_dump_json(exclude_none=True)
        await websocket.send_text(event_json)
```

### Deserializing on the Client

On the client side (JavaScript/TypeScript), parse the JSON back to objects:

```javascript
websocket.onmessage = (message) => {
    const event = JSON.parse(message.data);

    // Access event properties
    if (event.turn_complete) {
        console.log("Model finished turn");
    }

    if (event.content?.parts?.[0]?.text) {
        displayText(event.content.parts[0].text);
    }

    if (event.interrupted) {
        stopStreamingDisplay();
    }
};
```

### Practical Pattern: using StreamingSession Helper

This guide's demo application provides a `StreamingSession` class that wraps the serialization pattern:

> 📖 Source Reference:
> - [src/demo/app/bidi_streaming.py:50-98](../src/demo/app/bidi_streaming.py) (implementation)

```python
class StreamingSession:
    async def stream_events_as_json(self) -> AsyncGenerator[str, None]:
        """Stream events from the agent as JSON strings."""
        async for event in self._runner.run_live(
            user_id=self.user_id,
            session_id=self.session_id,
            live_request_queue=self._live_request_queue,
            run_config=self._run_config,
        ):
            yield event.model_dump_json(exclude_none=True, by_alias=True)
```

> 📖 Source Reference:
> - [src/demo/app/main.py:142,244](../src/demo/app/main.py) (usage in WebSocket and SSE handlers)

```python
# Use the demo app's StreamingSession helper
async for event_json in session.stream_events_as_json():
    await ws.send_text(event_json)
```

This helper pattern:

- Encapsulates the `runner.run_live()` setup
- Applies consistent serialization settings (`exclude_none=True`, `by_alias=True`)
- Reduces boilerplate in your transport handlers
- Can be customized for your application's needs



### Performance Considerations

**When to use `model_dump_json()`:**

- ✅ Streaming events over network (WebSocket, SSE)
- ✅ Logging/persistence to JSON files
- ✅ Debugging and inspection
- ✅ Integration with JSON-based APIs

**When NOT to use it:**

- ❌ In-memory processing (use event objects directly)
- ❌ High-frequency events where serialization overhead matters
- ❌ When you only need a few fields (extract them directly instead)

**Optimization tip for binary data:**

Base64-encoded binary audio in JSON significantly increases payload size. For production applications:

```python
async for event in runner.run_live(...):
    # Check for binary audio
    has_audio = (
        event.content and
        event.content.parts and
        any(p.inline_data for p in event.content.parts)
    )

    if has_audio:
        # Send audio via binary WebSocket frame
        for part in event.content.parts:
            if part.inline_data:
                await websocket.send_bytes(part.inline_data.data)

        # Send metadata only (much smaller)
        metadata_json = event.model_dump_json(
            exclude={'content': {'parts': {'__all__': {'inline_data'}}}}
        )
        await websocket.send_text(metadata_json)
    else:
        # Text-only events can be sent as JSON
        await websocket.send_text(event.model_dump_json(exclude_none=True))
```

This approach reduces bandwidth by ~75% for audio-heavy streams while maintaining full event metadata.
