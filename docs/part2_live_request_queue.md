# Part 2: Unified Message Processing with LiveRequestQueue

ADK's event handling architecture centers around a unified message model that eliminates the complexity of handling different data types separately. Instead of building custom protocols for text, audio, and control messages, ADK provides a single `LiveRequest` container:

> 📖 **Source Reference**: [`live_request_queue.py`](https://github.com/google/adk-python/blob/main/src/google/adk/agents/live_request_queue.py)

```python
class LiveRequest(BaseModel):
    content: Optional[Content] = None           # Text-based content and structured data
    blob: Optional[Blob] = None                 # Audio/video data and binary streams
    activity_start: Optional[ActivityStart] = None  # Signal start of user activity
    activity_end: Optional[ActivityEnd] = None      # Signal end of user activity
    close: bool = False                         # Graceful connection termination signal
```

This streamlined design handles every streaming scenario you'll encounter. The mutually exclusive `content` and `blob` fields handle different data types, the `activity_start` and `activity_end` fields enable activity signaling, and the `close` flag provides graceful termination semantics. This design eliminates the complexity of managing multiple message types while maintaining clear separation of concerns.

While you can create `LiveRequest` objects directly, `LiveRequestQueue` provides convenience methods that handle the creation internally:

**Text Content:**

Text content represents the primary mode of structured communication between users and AI agents. This includes not just simple text messages, but also rich content with metadata, function call responses, and contextual information. The `Content` object uses a `parts` array structure that allows for complex message composition while maintaining semantic clarity.

```python
# Convenience method (recommended)
text_content = Content(parts=[Part(text="Hello, streaming world!")])
live_request_queue.send_content(text_content)

# Equivalent to creating LiveRequest manually:
# live_request_queue.send(
#     LiveRequest(content=Content(parts=[Part(text="Hello, streaming world!")]))
# )
```

**Audio/Video Blobs:**

Binary data streams—primarily audio and video—flow through the `Blob` type, which handles the real-time transmission of multimedia content. Unlike text content that gets processed turn-by-turn, blobs are designed for continuous streaming scenarios where data arrives in chunks. The base64 encoding ensures safe transmission while the MIME type helps the model understand the content format.

```python
# Convenience method (recommended)
audio_blob = Blob(
    mime_type="audio/pcm",
    data=base64.b64encode(audio_data).decode()
)
live_request_queue.send_realtime(audio_blob)

# Equivalent to creating LiveRequest manually:
# live_request_queue.send(
#     LiveRequest(blob=Blob(mime_type="audio/pcm", data=encoded_audio))
# )
```

**Activity Signals:**

Activity signals provide a sophisticated mechanism for communicating user engagement state to the AI model. `ActivityStart` signals indicate when a user begins providing input (like starting to speak or type), while `ActivityEnd` marks the completion of that input. These signals enable the model to understand natural conversation boundaries and make intelligent decisions about when to respond or when to wait for more input.

```python
# Convenience methods (recommended)
live_request_queue.send_activity_start()
live_request_queue.send_activity_end()

# Equivalent to creating LiveRequest manually:
# live_request_queue.send(LiveRequest(activity_start=ActivityStart()))
# live_request_queue.send(LiveRequest(activity_end=ActivityEnd()))
```

**Control Signals:**

The `close` signal provides graceful termination semantics for streaming sessions. It signals the system to cleanly close the model connection and end the bidirectional stream. Note: audio/transcript caches are flushed on control events (for example, turn completion), not by `close()` itself.

```python
# Convenience method (recommended)
live_request_queue.close()

# Equivalent to creating LiveRequest manually:
# live_request_queue.send(LiveRequest(close=True))
```

**Sample code (message parsing – from src/demo/app/bidi_streaming.py):**

> 📖 Source Reference: [src/demo/app/bidi_streaming.py](../src/demo/app/bidi_streaming.py)
> 📖 Source Reference (transport handlers): [src/demo/app/main.py](../src/demo/app/main.py)

The helper parses either full `LiveRequest` JSON (activity, blob, close) or plain text:

```python
# Parse incoming WebSocket/SSE message
text, is_close = parse_message(data)
if is_close:
    # Graceful termination
    session.close()
elif text:
    # Treat plain text as a discrete turn
    session.send_text(text)
```

## send_content() vs send_realtime() Methods

When using `LiveRequestQueue`, you'll use two different methods to send data to the model, each optimized for different types of communication. Understanding when to use each method is crucial for building efficient streaming applications.

### send_content(): Structured Turn-Based Communication

The `send_content()` method handles structured, turn-complete messages that represent discrete conversation turns:

**What it sends:**

- **Regular conversation messages**: User text input that starts a new turn
- **Function call responses**: Results from tool executions that the model requested
- **Structured metadata**: Context information embedded in Content objects

**Example usage:**

```python
# Send user message
content = Content(parts=[Part(text="Hello, AI assistant!")])
live_request_queue.send_content(content)

# Send function response
function_response = FunctionResponse(
    name="get_weather",
    response={"temperature": 72, "condition": "sunny"}
)
content = Content(parts=[Part(function_response=function_response)])
live_request_queue.send_content(content)
```

**Key characteristic**: This signals a complete turn to the model, triggering immediate response generation.

**Important:** When sending function responses, ensure the `Content` contains only function responses in its parts (no mixed text), or the responses may be ignored by the model.

### send_realtime(): Continuous Streaming Data

The `send_realtime()` method handles continuous, real-time data streams that don't follow turn-based semantics:

**What it sends:**

- **Audio chunks**: PCM-encoded audio data for voice input
- **Video frames**: Binary video data for multimodal processing
- **Activity signals**: ActivityStart/ActivityEnd markers for user engagement tracking

**Example usage:**

```python
# Send audio chunk (20ms of PCM audio)
audio_blob = Blob(
    mime_type="audio/pcm;rate=16000",
    data=base64.b64encode(audio_chunk).decode()
)
live_request_queue.send_realtime(audio_blob)

# Signal user activity
live_request_queue.send_activity_start()
# ... stream audio chunks ...
live_request_queue.send_activity_end()
```

**Key characteristic**: Real-time data flows continuously without turn boundaries. The model can start responding before receiving all input (e.g., interrupting during speech), enabling natural conversation flow.

**When to use which:**

| Scenario | Method | Reason |
|----------|--------|--------|
| Text chat message | `send_content()` | Discrete, turn-complete communication |
| Tool execution result | `send_content()` | Structured function response data |
| Voice input streaming | `send_realtime()` | Continuous audio data |
| User started speaking | `send_activity_start()` | Activity signal (convenience method) |
| Video frame | `send_realtime()` | Binary streaming data |

## Async Queue Management

One of the most powerful aspects of `LiveRequestQueue` is how it seamlessly bridges synchronous and asynchronous programming models. The queue's design recognizes a fundamental reality of streaming applications: message production often happens in synchronous contexts (like HTTP request handlers or UI event callbacks), while message consumption happens in async contexts (like the streaming event loop).

The producer side uses non-blocking operations that return immediately, allowing your application to queue messages without waiting for processing. This prevents UI freezes and keeps your application responsive even under heavy load. The consumer side, however, uses async/await patterns that integrate naturally with Python's asyncio ecosystem, enabling efficient concurrent processing without the complexity of threading.

```python
# Producer (non-blocking)
live_request_queue.send_content(content)

# Consumer (async)
request = await live_request_queue.get()
```

This asymmetric design—sync producers, async consumers—is what makes `LiveRequestQueue` so practical for real-world applications. You can send messages from anywhere in your codebase without worrying about async contexts, while ADK's internal machinery handles them efficiently through async processing.

## Concurrency Notes

`LiveRequestQueue` is designed for typical streaming scenarios:

- **Same event loop**: Call `send_content()`, `send_realtime()`, `send_activity_*()`, or `close()` freely without extra coordination
- **Cross-thread usage**: For advanced scenarios requiring cross-thread enqueueing, schedule enqueues via `loop.call_soon_threadsafe(queue.put_nowait, ...)` or send a validated `LiveRequest` via a loop-bound method
- **Message ordering**: ADK processes messages sequentially in FIFO order
- **Unbounded by default**: Messages are not dropped or coalesced; see Backpressure and Flow Control for bounded-buffer patterns if needed

**Sample code (streaming orchestration – from src/demo/app/bidi_streaming.py):**

> 📖 Source Reference: [src/demo/app/bidi_streaming.py](../src/demo/app/bidi_streaming.py)
> 📖 Source Reference (transport handlers): [src/demo/app/main.py](../src/demo/app/main.py)

Create a per-connection `StreamingSession` that wraps `LiveRequestQueue` and `Runner.run_live(...)`:

```python
session = StreamingSession(params)

async def forward_events():
    async for event_json in session.stream_events_as_json():
        await ws.send_text(event_json)

async def consume_messages():
    data = await ws.receive_text()
    text, is_close = parse_message(data)
    if is_close:
        session.close()
    elif text:
        session.send_text(text)

forward_task = asyncio.create_task(forward_events())
consumer_task = asyncio.create_task(consume_messages())
await asyncio.wait({forward_task, consumer_task}, return_when=asyncio.FIRST_COMPLETED)
```

<!-- Example block removed: local Part 2 sample files have been removed. -->
