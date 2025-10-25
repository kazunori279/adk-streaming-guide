# Part 4: Understanding RunConfig

> 📖 **Source Reference**: [`run_config.py`](https://github.com/google/adk-python/blob/main/src/google/adk/agents/run_config.py)

RunConfig is how you configure the behavior of `run_live()` sessions. It unlocks sophisticated capabilities like multimodal interactions, intelligent proactivity, session resumption, and cost controls—all configured declaratively without complex implementation.

> 📘 **For detailed information about audio/video models, architectures, and features**, see [Part 5: Audio and Video in Live API](part5_audio_and_video.md).

## Model Compatibility

Understanding which features are available on which models is crucial for configuring `RunConfig` correctly. ADK's approach to model capabilities is straightforward: when you use `runner.run_live()`, it automatically connects to either the **Gemini Live API** (via Google AI Studio) or **Vertex AI Live API** (via Google Cloud), depending on your environment configuration.

ADK doesn't perform extensive model validation—it relies on the Live API backend to handle feature support. The Live API will return errors if you attempt to use unsupported features on a given model.

**⚠️ Disclaimer:** Model availability, capabilities, and discontinuation dates are subject to change. Always verify model capabilities and preview/discontinuation timelines before deploying to production:

- **Gemini Live API**: Check the [official Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live)
- **Vertex AI Live API**: Check the [official Vertex AI Live API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

### Feature Support Matrix

Different Live API models support different feature sets when used with ADK. Understanding these differences helps you choose the right model for your use case:

**Model Naming Convention:**

- **Gemini API** (via Google AI Studio): Uses model IDs like `gemini-2.5-flash-native-audio-preview-09-2025`
- **Vertex AI** (via Google Cloud): Uses model IDs like `gemini-live-2.5-flash`

| Feature | Gemini: `gemini-2.5-flash-native-audio-preview-09-2025` | Gemini: `gemini-live-2.5-flash-preview`<br>Vertex: `gemini-live-2.5-flash` | Gemini: `gemini-2.0-flash-live-001` | RunConfig parameters |
|---------|:---:|:---:|:---:|:---:|
| **Audio input/output** | ✅ | ✅ | ✅ | `response_modalities=["AUDIO"]` |
| **Audio transcription** | ✅ | ✅ | ✅ | `input_audio_transcription`, `output_audio_transcription` |
| **Voice Activity Detection (VAD)** | ✅ | ✅ | ✅ | `realtime_input_config.voice_activity_detection` |
| **Bidirectional streaming** | ✅ | ✅ | ✅ | `runner.run_live()` |
| **Emotion-aware dialogue** | ✅ | ❌ | ❌ | `enable_affective_dialog=True` |
| **Proactive audio response** | ✅ | ❌ | ❌ | `proactivity=ProactivityConfig(enabled=True)` |
| **Session resumption** | ✅ | ✅ | ✅ | `session_resumption=SessionResumptionConfig(mode="transparent")` |
| **Function calling** | ✅ | ✅ | ✅ | Define tools on `Agent` |
| **Built-in tools** (Search, Code Execution) | ✅ | ✅ | ✅ | ADK tool definitions |
| **Context window** | 128k tokens | 32k-128k tokens (Vertex configurable) | 32k tokens | Model property |
| **Provisioned Throughput** | ❌ | ✅ | ❌ | Google Cloud feature |

### Session Limits and Constraints

Live API models have session duration limits that vary by platform and modality:

| Constraint Type | Gemini Live API<br>(via Google AI Studio) | Vertex AI Live API<br>(via Google Cloud) | Notes |
|----------------|-------------------------------------------|------------------------------------------|-------|
| **Audio-only sessions** | 15 minutes | 15 minutes | Includes text + audio interactions |
| **Audio + video sessions** | 2 minutes | 2 minutes | Significantly shorter due to video processing overhead |
| **Connection lifetime** | ~10 minutes | N/A | WebSocket connection auto-terminates (Gemini only) |
| **Concurrent sessions** | N/A | Up to 1,000 | Per Google Cloud project (Vertex only) |
| **Session resumption window** | 2 hours | 24 hours | Resumption tokens validity period after session termination |

## Response Modalities

Response modalities control how the model generates output—as text or audio. Both Gemini Live API and Vertex AI Live API have the same restriction: only one response modality per session.

### Configuration

```python
# ✅ Valid: Text-only responses
run_config = RunConfig(
    response_modalities=["TEXT"],
    streaming_mode=StreamingMode.BIDI
)

# ✅ Valid: Audio-only responses
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI
)

# ❌ Invalid: Both modalities - results in config error
run_config = RunConfig(
    response_modalities=["TEXT", "AUDIO"],  # ERROR
    streaming_mode=StreamingMode.BIDI
)
```

**Key constraints:**

- You must choose either `TEXT` or `AUDIO` at session start
- Cannot switch between modalities mid-session

## StreamingMode: BIDI or SSE

**This guide focuses on `StreamingMode.BIDI`**, which is required for real-time audio/video interactions and Live API features. However, it's worth understanding the difference between BIDI mode and the legacy SSE mode to choose the right approach for your use case.

ADK supports two distinct streaming modes that control **how ADK communicates with the Gemini API**. These modes are independent of your application's client-facing architecture (you can build WebSocket servers, REST APIs, or any other architecture with either mode).

### Understanding the Terminology

**Important:** `StreamingMode.BIDI` and `StreamingMode.SSE` refer to the **ADK-to-Gemini API communication protocol**, not your server's client-facing protocol:

- `StreamingMode.BIDI`: ADK uses WebSocket to connect to Gemini Live API
- `StreamingMode.SSE`: ADK uses HTTP streaming to connect to Gemini API

Your application can use either mode regardless of whether you're building a WebSocket server, SSE server, REST API, or any other architecture for your clients.

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

# BIDI streaming for real-time audio/video
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"]  # Supports audio/video modalities
)

# SSE streaming for text-based interactions
run_config = RunConfig(
    streaming_mode=StreamingMode.SSE,
    response_modalities=["TEXT"]  # Text-only modality
)
```

### Protocol and Implementation Differences

**StreamingMode.BIDI - Bidirectional WebSocket Communication:**

```mermaid
sequenceDiagram
    participant App as Your Application
    participant ADK as ADK
    participant Queue as LiveRequestQueue
    participant Gemini as Gemini Live API

    Note over ADK,Gemini: Protocol: WebSocket

    App->>ADK: runner.run_live(run_config)
    ADK->>Gemini: live.connect() - WebSocket
    activate Gemini

    Note over ADK,Queue: Can send while receiving

    App->>Queue: send_content(text)
    Queue->>Gemini: → Content (via WebSocket)
    App->>Queue: send_realtime(audio)
    Queue->>Gemini: → Audio blob (via WebSocket)

    Gemini-->>ADK: ← Partial response (partial=True)
    ADK-->>App: ← Event: partial text/audio
    Gemini-->>ADK: ← Partial response (partial=True)
    ADK-->>App: ← Event: partial text/audio

    App->>Queue: send_content(interrupt)
    Queue->>Gemini: → New content

    Gemini-->>ADK: ← turn_complete=True
    ADK-->>App: ← Event: turn complete

    deactivate Gemini

    Note over ADK,Gemini: Turn Detection: turn_complete flag
```

**StreamingMode.SSE - Unidirectional HTTP Streaming:**

```mermaid
sequenceDiagram
    participant App as Your Application
    participant ADK as ADK
    participant Gemini as Gemini API

    Note over ADK,Gemini: Protocol: HTTP

    App->>ADK: runner.run(run_config)
    ADK->>Gemini: generate_content_stream() - HTTP
    activate Gemini

    Note over ADK,Gemini: Request sent completely, then stream response

    Gemini-->>ADK: ← Partial chunk (partial=True)
    ADK-->>App: ← Event: partial text
    Gemini-->>ADK: ← Partial chunk (partial=True)
    ADK-->>App: ← Event: partial text
    Gemini-->>ADK: ← Partial chunk (partial=True)
    ADK-->>App: ← Event: partial text

    Gemini-->>ADK: ← Final chunk (finish_reason=STOP)
    ADK-->>App: ← Event: complete response

    deactivate Gemini

    Note over ADK,Gemini: Turn Detection: finish_reason
```

### When to Use Each Mode

**Use BIDI when:**

- Building voice/video applications with real-time interaction
- Need bidirectional communication (send while receiving)
- Require Live API features (audio transcription, VAD, proactivity, affective dialog)
- Supporting interruptions and natural turn-taking
- Implementing live streaming tools or real-time data feeds

**Use SSE when:**

- Building text-based chat applications
- Standard request/response interaction pattern
- Using Gemini 1.5 models (Pro, Flash)
- Simpler deployment without WebSocket requirements
- Need larger context windows (up to 2M tokens)

### Standard Gemini Models (1.5 series) accessed via SSE

For comparison, standard Gemini 1.5 models accessed via SSE streaming have different capabilities:

**Models:**

- `gemini-1.5-pro`
- `gemini-1.5-flash`

**Supported:**

- ✅ Text input/output (`response_modalities=["TEXT"]`)
- ✅ SSE streaming (`StreamingMode.SSE`)
- ✅ Function calling with automatic execution
- ✅ Large context windows (up to 2M tokens for 1.5-pro)

**Not Supported:**

- ❌ Live audio features (audio I/O, transcription, VAD)
- ❌ Bidirectional streaming via `run_live()`
- ❌ Proactivity and affective dialog
- ❌ Video input

## Context Window Compression

**Problem:** Live API models have finite context windows (128k tokens for `gemini-2.5-flash-native-audio-preview-09-2025`, 32k-128k for Vertex AI models). Long conversations—especially extended customer support sessions, tutoring interactions, or multi-hour voice dialogues—will eventually exceed these limits, causing the session to fail or lose critical conversation history.

**Solution:** Context window compression uses a sliding-window approach to automatically compress or summarize earlier conversation history when the token count reaches a configured threshold. The Live API preserves recent context in full detail while compressing older portions, allowing sessions to continue indefinitely without hitting context limits.

Enable sliding-window compression to extend session duration beyond connection limits:

```python
from google.genai import types

run_config = RunConfig(
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=1000,  # Start compression after this many tokens
        sliding_window=types.SlidingWindow(
            target_tokens=500  # Target size after compression
        )
    )
)
```

**How it works:**

When context window compression is enabled:

1. The Live API monitors the total token count of the conversation context
2. When the context reaches the `trigger_tokens` threshold, compression activates
3. Earlier conversation history is compressed or summarized using a sliding window approach
4. Recent context (last `target_tokens` worth) is preserved in full detail
5. This allows sessions to continue beyond normal context window limits

This is critical for long-running conversations that would otherwise exceed the model's context window limits (128k tokens for `gemini-2.5-flash-native-audio-preview-09-2025`, 32k-128k for Vertex AI models).

Context window compression is a Live API feature that works automatically once configured. ADK passes this configuration to the underlying Live API, which handles the compression transparently.

**Use cases:**

- Extended customer service conversations
- Long tutoring or educational sessions
- Multi-hour voice interactions
- Any scenario where conversation history exceeds model context limits

## Session Resumption

**Problem:** WebSocket connections can drop unexpectedly due to network instability, server maintenance, or the Live API's connection timeout limits (~10 minutes for Gemini Live API). Without resumption capability, any disconnection would force users to restart their entire conversation from scratch, losing all accumulated context and state.

**Solution:** Session resumption provides a mechanism to transparently reconnect to an ongoing session using a resumption handle. The Live API maintains the conversation state server-side, allowing ADK to seamlessly reattach to the same session after a disconnection—preserving the full conversation history, tool call state, and model context.

Enable transparent reconnection without losing conversation context:

```python
run_config = RunConfig(
    session_resumption=SessionResumptionConfig(
        mode="transparent"  # Only mode currently supported
    )
)
```

**How it works:**

When session resumption is enabled:

1. Gemini Live API provides a `live_session_resumption_handle` in session updates
2. ADK stores this handle in InvocationContext
3. If the WebSocket connection drops, ADK can reconnect using the handle
4. The model resumes from exactly where it left off—no context loss

This is critical for production deployments where network reliability varies and long conversations should survive temporary disconnections.

**Use cases:** Production deployments where network reliability varies, long-running customer service conversations, extended tutoring sessions, mobile applications with intermittent connectivity, and any scenario where conversation continuity is critical to user experience.

Advanced: Example reconnection flow (conceptual):

```python
attempt = 1
while True:
    try:
        # If available, attach InvocationContext.live_session_resumption_handle
        # to llm_request.live_connect_config.session_resumption.handle
        async with llm.connect(llm_request) as conn:
            # Start concurrent send/receive tasks
            await handle_stream(conn)
        break  # Clean close
    except ConnectionClosed:
        attempt += 1
        # Retry with updated handle provided by model updates
        continue
```

## Cost and Safety Controls

**Problem:** During development or in production, buggy tools or infinite agent loops can trigger excessive LLM API calls, leading to unexpected costs and quota exhaustion. Additionally, debugging voice interactions and maintaining compliance records requires persisting audio streams, which isn't enabled by default.

**Solution:** ADK provides built-in safeguards through `max_llm_calls` to cap the number of LLM invocations per session, preventing runaway costs. The `save_live_audio` option allows developers to persist audio streams to the session and artifact services for debugging, compliance auditing, and quality assurance purposes.

Protect against runaway costs and ensure conversation boundaries:

```python
run_config = RunConfig(
    # Limit total LLM calls per invocation
    max_llm_calls=500,  # Default: 500, 0 or negative = unlimited

    # Save audio artifacts for debugging/compliance
    save_live_audio=True  # Default: False
)
```

**max_llm_calls:**

Enforced by InvocationContext's `_invocation_cost_manager`, which increments a counter on each LLM call and raises `LlmCallsLimitExceededError` when the limit is exceeded. This prevents:

- Infinite loops in agent workflows
- Runaway costs from buggy tools
- Excessive API usage in development

**save_live_audio:**

When enabled, ADK persists audio streams to:

- **Session service**: Conversation history includes audio references
- **Artifact service**: Audio files stored with unique IDs

**Use cases:** Development and testing environments where you want to prevent accidental cost overruns, production systems with strict budget constraints, regulated industries requiring audio conversation records (healthcare, financial services), debugging voice assistant behavior, and collecting training data for model improvement. Also useful for:

- Debugging voice interaction issues
- Compliance and audit trails
- Training data collection
- Quality assurance

## Compositional Function Calling (Experimental)

**Problem:** Complex real-world tasks often require orchestrating multiple tools together—fetching data from several sources in parallel, chaining outputs from one tool as inputs to another, or conditionally executing tools based on intermediate results. Standard function calling handles tools independently and sequentially, making multi-step workflows inefficient.

**Solution:** Compositional Function Calling (CFC) enables the model to intelligently orchestrate multiple tools in sophisticated patterns. The model can call multiple tools simultaneously in parallel, chain tool results as inputs to subsequent calls, and execute conditional logic based on tool outputs—all within a single model turn. This transforms how agents handle complex, multi-step reasoning and data gathering tasks.

Enable advanced function calling patterns:

```python
run_config = RunConfig(
    support_cfc=True,  # Compositional Function Calling
    streaming_mode=StreamingMode.SSE
)
```

**⚠️ Warning:** This feature is experimental.

**How CFC works with streaming modes:**

When `support_cfc=True`, ADK always uses the **Live API backend** (WebSocket connection) regardless of the `streaming_mode` setting. The `streaming_mode` parameter controls how responses are streamed to your application:

- `StreamingMode.SSE`: Yields partial responses incrementally (SSE-like behavior)
- `StreamingMode.BIDI`: Yields events in bidirectional streaming style

**Important:** Even with `streaming_mode=StreamingMode.SSE`, CFC connects to the Live API via WebSocket—the SSE setting only affects the response streaming interface at the application level.

**ADK Validation:**

CFC is the **only explicitly validated feature** in ADK. When you enable `support_cfc=True`, ADK enforces these requirements:

- Model name must start with `gemini-2*` (validated in `runners.py:1060-1066`)
- Automatically injects `BuiltInCodeExecutor` if not already configured

**Supported models:**

- ✅ `gemini-2.5-flash-native-audio-preview-09-2025` (Gemini Live API)
- ✅ `gemini-2.0-flash-live-001` (Gemini Live API)
- ✅ Other `gemini-2*` models via Live API

**CFC capabilities:**

- **Parallel execution**: Call multiple independent tools simultaneously (e.g., `get_weather()` for multiple cities at once)
- **Function chaining**: Use output from one function as input to another (e.g., call `get_current_location()`, then use that result in `get_weather(location)`)
- **Conditional execution**: Execute tools based on intermediate results from other tools

**Use cases:** Data aggregation workflows that fetch information from multiple APIs simultaneously, complex research tasks that require conditional exploration based on intermediate findings, multi-step analysis pipelines where one tool's output feeds into another, and any scenario requiring sophisticated tool coordination beyond simple sequential execution.

**Examples and documentation:**

- **Official Gemini documentation**: [Function Calling guide](https://ai.google.dev/gemini-api/docs/function-calling) - Detailed explanation of compositional and parallel function calling
- **ADK parallel functions example**: [`parallel_functions/agent.py`](https://github.com/google/adk-python/blob/main/contributing/samples/parallel_functions/agent.py) - Complete working example with async tools optimized for parallel execution
- **Performance guide**: [Increase tool performance with parallel execution](https://google.github.io/adk-docs/tools/performance/) - Best practices for building parallel-ready tools

**Note:** While ADK automatically runs async tools in parallel starting from version 1.10.0, CFC provides the model with enhanced capabilities to intelligently orchestrate complex multi-tool workflows including chaining and conditional logic—capabilities that go beyond simple parallel execution.
