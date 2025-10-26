# Part 4: Understanding RunConfig

> 📖 **Source Reference**: [`run_config.py`](https://github.com/google/adk-python/blob/main/src/google/adk/agents/run_config.py)

RunConfig is how you configure the behavior of `run_live()` sessions. It unlocks sophisticated capabilities like multimodal interactions, intelligent proactivity, session resumption, and cost controls—all configured declaratively without complex implementation.

> 📘 **For detailed information about audio/video models, architectures, and features**, see [Part 5: Audio and Video in Live API](part5_audio_and_video.md).

## Model Compatibility

Understanding which features are available on which models is crucial for configuring `RunConfig` correctly. ADK's approach to model capabilities is straightforward: when you use `runner.run_live()`, it automatically connects to either the **Gemini Live API** (via Google AI Studio) or **Vertex AI Live API** (via Google Cloud), depending on your environment configuration.

ADK doesn't perform extensive model validation—it relies on the Live API backend to handle feature support. The Live API will return errors if you attempt to use unsupported features on a given model.

**⚠️ Disclaimer:** Model availability, capabilities, and discontinuation dates are subject to change. **Preview models may be discontinued with limited notice.** Always verify model capabilities and preview/discontinuation timelines before deploying to production:

- **Gemini Live API**: Check the [official Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live) and [model deprecation schedule](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions)
- **Vertex AI Live API**: Check the [official Vertex AI Live API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api) and [Vertex AI model versions](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning)

For production deployments, prefer stable model versions over preview models whenever possible.

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

**Note on VAD**: Voice Activity Detection is enabled by default on all Live API models. You only need to configure `realtime_input_config.voice_activity_detection` if you want to disable automatic detection or adjust sensitivity settings. See [Part 5: Audio and Video](part5_audio_and_video.md) for VAD configuration details.

> 💡 **Related Concept**: Voice Activity Detection (VAD) is different from manual activity signals (`ActivityStart`/`ActivityEnd`). VAD automatically detects when users are speaking, while activity signals are manually sent by your application for push-to-talk implementations. See [Part 2: Activity Signals](part2_live_request_queue.md#activity-signals) for details on manual turn control.

**Provisioned Throughput**: A Vertex AI Live API feature that allows you to reserve dedicated capacity for predictable performance and pricing. Only available on Vertex AI (`gemini-live-2.5-flash`), not on Gemini Live API. See [Vertex AI Provisioned Throughput documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput) for details.

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

# ❌ Invalid: Both modalities - results in API error
run_config = RunConfig(
    response_modalities=["TEXT", "AUDIO"],  # ERROR
    streaming_mode=StreamingMode.BIDI
)
# This will cause an error from the Live API:
# "Only one response modality is supported per session"
```

**Key constraints:**

- You must choose either `TEXT` or `AUDIO` at session start. Cannot switch between modalities mid-session
- If you want to receive both audio and text responses from the model, use the Audio Transcript feature which provides text transcripts of the audio output. See [Audio Transcription](part5_audio_and_video.md#audio-transcription) for details
- Response modality only affects model output—you can always send text, voice, or video input regardless of the chosen response modality

**Why this restriction exists**: The Live API models are optimized for either text generation or audio generation, not both simultaneously. This is a fundamental constraint of the underlying model architecture, not an ADK limitation.

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

## Session Management

Building reliable Live API applications requires understanding the fundamental distinction between **connections** (WebSocket transport links) and **sessions** (logical conversation contexts). Unlike traditional request-response APIs, Live API sessions face unique platform-specific constraints: connection timeouts, session duration limits that vary by modality (audio-only vs audio+video), finite context windows, and concurrent session quotas that differ between Gemini Live API and Vertex AI Live API.

Two complementary Live API features address these constraints, with different levels of ADK automation:

**Session Resumption (ADK-managed)**: Overcomes the ~10 minute connection lifetime limit. When enabled in RunConfig, ADK automatically handles all connection lifecycle management by transparently reconnecting when connections close (whether from normal timeouts or unexpected network failures). ADK reconnects seamlessly in the background—developers don't need to write any reconnection logic. The session continues uninterrupted even as ADK cycles through multiple WebSocket connections, preserving full conversation state.

**Context Window Compression (Developer-configured)**: Overcomes both session duration limits (15 minutes for audio-only, 2 minutes for audio+video) and context window limits (token caps). Developers must explicitly configure this feature if they need unlimited session duration. Once configured in RunConfig, the Live API automatically compresses older conversation history when approaching the context window threshold, enabling unlimited session duration regardless of time or conversation length. ADK simply passes this configuration to the Live API without managing the compression itself.

Together, these features enable production-ready voice applications that can sustain extended, reliable interactions across varying network conditions and conversation lengths.

### Live API Connections and Sessions

Understanding the distinction between **connections** and **sessions** in Live API is crucial for building reliable ADK Bidi-streaming applications.

**Connection**: The physical WebSocket link between ADK and the Live API server. This is the network transport layer that carries bidirectional streaming data.

**Session**: The logical conversation context maintained by the Live API, including conversation history, tool call state, and model context. A session can span multiple connections.

| Aspect | Connection | Session |
|--------|-----------|---------|
| **What is it?** | WebSocket network connection | Logical conversation context |
| **Scope** | Transport layer | Application layer |
| **Can span?** | Single network link | Multiple connections via resumption |
| **Failure impact** | Network error or timeout | Lost conversation history |

#### Connection and Session Limits by Platform

Understanding the constraints of each platform is critical for production planning. Gemini Live API and Vertex AI Live API have different limits that affect how long conversations can run and how many users can connect simultaneously. The most important distinction is between **connection lifetime** (how long a single WebSocket connection stays open) and **session lifetime** (how long a logical conversation can continue).

| Constraint Type | Gemini Live API<br>(Google AI Studio) | Vertex AI Live API<br>(Google Cloud) | Notes |
|----------------|---------------------------------------|--------------------------------------|-------|
| **Connection lifetime** | ~10 minutes | Not documented separately | Each Gemini WebSocket connection auto-terminates; ADK reconnects transparently with session resumption |
| **Session Lifetime (Audio-only)** | 15 minutes | 10 minutes | Maximum session duration without context window compression |
| **Session Lifetime (Audio + video)** | 2 minutes | 10 minutes | Gemini has shorter limit for video; Vertex treats all sessions equally |
| **Session resumption token validity** | 2 hours | 24 hours | How long resumption handles remain valid after connection/session ends |
| **Concurrent sessions** | 50 (Tier 1)<br>1,000 (Tier 2+) | Up to 1,000 | Gemini limits vary by API tier; Vertex limit is per Google Cloud project |

> 📖 **Sources**: [Gemini Live API Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide) | [Gemini API Quotas](https://ai.google.dev/gemini-api/docs/quota) | [Vertex AI Streamed Conversations](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api/streamed-conversations)

### ADK's Automatic Reconnection with Session Resumption

By default, the Live API limits connection lifetime to approximately 10 minutes—each WebSocket connection automatically closes after this duration. To overcome this limit and enable longer conversations, ADK uses [Session Resumption](https://ai.google.dev/gemini-api/docs/live#session-resumption), a core feature of the Gemini Live API that transparently migrates a session across multiple connections. When enabled, the Live API generates resumption handles that ADK uses to reconnect to the same session context, preserving the full conversation history and state. This allows sessions to continue seamlessly beyond the 10-minute connection limit, handling connection timeouts, network disruptions, and planned reconnections automatically.

When you enable session resumption in RunConfig, ADK automatically handles connection lifecycle:

```python
run_config = RunConfig(
    session_resumption=SessionResumptionConfig(mode="transparent")
)
```

#### How ADK Manages Session Resumption

While session resumption is a Gemini Live API feature, using it directly requires managing resumption handles, detecting connection closures, and implementing reconnection logic. ADK takes full responsibility for this complexity, automatically utilizing session resumption behind the scenes so developers don't need to write any reconnection code. You simply enable it in RunConfig, and ADK handles everything transparently.

**ADK's automatic management:**

1. **Initial Connection**: ADK establishes a WebSocket connection to Live API
2. **Handle Updates**: Live API periodically sends updated session resumption handles, which ADK caches in InvocationContext
3. **Graceful Connection Close**: When the ~10 minute connection limit is reached, the WebSocket closes gracefully (no exception)
4. **Automatic Reconnection**: ADK's internal loop detects the close and automatically reconnects using the cached handle
5. **Session Continuation**: The same session continues seamlessly with full context preserved

#### Sequence Diagram: Automatic Reconnection

```mermaid
sequenceDiagram
    participant App as Your Application
    participant ADK as ADK (run_live)
    participant WS as WebSocket Connection
    participant API as Gemini Live API
    participant Session as Live Session Context

    Note over App,Session: Initial Connection (with session resumption enabled)

    App->>ADK: runner.run_live(run_config=RunConfig(session_resumption=...))
    ADK->>API: WebSocket connect()
    activate WS
    API->>Session: Create new session
    activate Session

    Note over ADK,API: Bidirectional Streaming (0-10 minutes)

    App->>ADK: send_content(text) / send_realtime(audio)
    ADK->>API: → Content via WebSocket
    API->>Session: Update conversation history
    API-->>ADK: ← Streaming response
    ADK-->>App: ← yield event

    Note over API,Session: Live API sends resumption handle updates
    API-->>ADK: session_resumption_update { new_handle: "abc123" }
    ADK->>ADK: Cache handle in InvocationContext

    Note over WS,API: ~10 minutes elapsed - Connection timeout

    API->>WS: Close WebSocket (graceful close)
    deactivate WS
    Note over Session: Session context preserved (2 hours validity)

    Note over ADK: Graceful close detected - No exception raised
    ADK->>ADK: while True loop continues

    Note over ADK,API: Automatic Reconnection

    ADK->>API: WebSocket connect(session_resumption.handle="abc123")
    activate WS
    API->>Session: Attach to existing session
    API-->>ADK: Session resumed with full context

    Note over ADK,API: Bidirectional Streaming Continues

    App->>ADK: send_content(text) / send_realtime(audio)
    ADK->>API: → Content via WebSocket
    API->>Session: Update conversation history
    API-->>ADK: ← Streaming response
    ADK-->>App: ← yield event

    Note over App,Session: Session continues until duration limit or explicit close

    deactivate WS
    deactivate Session
```

### Context Window Compression

**Problem:** Live API sessions face two critical constraints that limit conversation duration. First, **session duration limits** impose hard time caps: without compression, audio-only sessions are limited to 15 minutes and audio+video sessions to just 2 minutes. Second, **context window limits** restrict conversation length: models have finite token capacities (128k tokens for `gemini-2.5-flash-native-audio-preview-09-2025`, 32k-128k for Vertex AI models). Long conversations—especially extended customer support sessions, tutoring interactions, or multi-hour voice dialogues—will hit either the time limit or the token limit, causing the session to terminate or lose critical conversation history.

**Solution:** [Context window compression](https://ai.google.dev/gemini-api/docs/live-session#context-window-compression) solves both constraints simultaneously. It uses a sliding-window approach to automatically compress or summarize earlier conversation history when the token count reaches a configured threshold. The Live API preserves recent context in full detail while compressing older portions. **Critically, enabling context window compression extends session duration to unlimited time**, removing the 15-minute (audio-only) or 2-minute (audio+video) session limits while also preventing token limit exhaustion. However, there is a trade-off: as the feature summarizes earlier conversation history rather than retaining it all, the detail of past context will be gradually lost over time. The model will have access to compressed summaries of older exchanges, not the full verbatim history.

ADK provides an easy way to configure context window compression through RunConfig. However, developers are responsible for appropriately configuring the compression parameters (`trigger_tokens` and `target_tokens`) based on their specific requirements—model context window size, expected conversation patterns, and quality needs:

```python
from google.genai import types

# For gemini-2.5-flash-native-audio-preview-09-2025 (128k context window)
run_config = RunConfig(
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100000,  # Start compression at ~78% of 128k context
        sliding_window=types.SlidingWindow(
            target_tokens=80000  # Compress to ~62% of context, preserving recent turns
        )
    )
)

# For gemini-live-2.5-flash (32k context window on Vertex AI)
run_config = RunConfig(
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25000,  # Start compression at ~78% of 32k context
        sliding_window=types.SlidingWindow(
            target_tokens=20000  # Compress to ~62% of context
        )
    )
)
```

**Choosing appropriate thresholds:**

- Set `trigger_tokens` to 70-80% of your model's context window to allow headroom
- Set `target_tokens` to 60-70% to provide sufficient compression
- Test with your actual conversation patterns to optimize these values

**How it works:**

When context window compression is enabled:

1. The Live API monitors the total token count of the conversation context
2. When the context reaches the `trigger_tokens` threshold, compression activates
3. Earlier conversation history is compressed or summarized using a sliding window approach
4. Recent context (last `target_tokens` worth) is preserved in full detail
5. **Two critical effects occur simultaneously:**
   - Session duration limits are removed (no more 15-minute/2-minute caps)
   - Token limits are managed (sessions can continue indefinitely regardless of conversation length)

### Best Practices for Session Management

#### Essential: Enable Session Resumption

- ✅ **Always enable session resumption** in RunConfig for production applications
- ✅ This enables ADK to automatically handle Gemini's ~10 minute connection timeouts transparently
- ✅ Sessions continue seamlessly across multiple WebSocket connections without user interruption

```python
run_config = RunConfig(
    response_modalities=["AUDIO"],
    session_resumption=SessionResumptionConfig(mode="transparent")
)
```

#### Enable Context Window Compression for Unlimited Sessions

- ✅ **Enable context window compression** if you need sessions longer than 15 minutes (audio-only) or 2 minutes (audio+video)
- ✅ Once enabled, session duration becomes unlimited—no need to monitor time-based limits
- ✅ Configure `trigger_tokens` and `target_tokens` based on your model's context window
- ✅ Test compression settings with realistic conversation patterns

```python
run_config = RunConfig(
    response_modalities=["AUDIO"],
    session_resumption=SessionResumptionConfig(mode="transparent"),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=100000,
        sliding_window=types.SlidingWindow(target_tokens=80000)
    )
)
```

#### Monitor Session Duration (Without Context Window Compression)

**Only applies if NOT using context window compression:**

- ✅ Focus on **session duration limits**, not connection timeouts (ADK handles those automatically)
- ✅ **Gemini Live API**: Monitor for 15-minute limit (audio-only) or 2-minute limit (audio+video)
- ✅ **Vertex AI Live API**: Monitor for 10-minute session limit
- ✅ Warn users 1-2 minutes before session duration limits
- ✅ Implement graceful session transitions for conversations exceeding session limits

#### Error Handling

With session resumption enabled, ADK handles connection issues automatically through **transparent reconnection**. Based on the official ADK samples, minimal error handling is needed:

**Recommended error handling pattern:**

```python
import logging
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, SessionResumptionConfig
from google.adk.agents.invocation_context import LlmCallsLimitExceededError

logger = logging.getLogger(__name__)

async def run_live_session(
    runner: Runner,
    user_id: str,
    session_id: str,
    run_config: RunConfig
):
    """
    Run live session with session resumption.

    Session resumption automatically handles:
    - Normal ~10 minute connection timeouts
    - Temporary network interruptions
    - Transparent reconnection with context preservation

    You only need to handle:
    - LlmCallsLimitExceededError (cost control limit)
    """
    try:
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            run_config=run_config
        ):
            # Process events
            if event.server_content:
                logger.debug(f"Received: {event.server_content}")

        logger.info("Session completed successfully")

    except LlmCallsLimitExceededError as e:
        # Cost control limit reached - this is intentional
        logger.error(
            f"LLM calls limit exceeded: {e}. "
            "Check for infinite loops or increase max_llm_calls."
        )
        raise

    except Exception as e:
        # Catch-all for unexpected errors during streaming
        logger.error(f"Unexpected error in live session: {e}", exc_info=True)
        raise

# Usage
async def main():
    from google.adk.agents.llm_agent import LlmAgent

    agent = LlmAgent(
        name="my_agent",
        model="gemini-2.5-flash-native-audio-preview-09-2025"
    )
    runner = Runner(agent=agent)

    # Enable session resumption for automatic reconnection
    run_config = RunConfig(
        response_modalities=["AUDIO"],
        session_resumption=SessionResumptionConfig(mode="transparent"),
        max_llm_calls=500  # Cost protection
    )

    try:
        await run_live_session(runner, "user123", "session456", run_config)
    except LlmCallsLimitExceededError:
        logger.error("Session terminated: cost limit reached")
        # Investigate agent logic for infinite loops
    except Exception as e:
        logger.error(f"Session failed: {e}")
        # Handle or report the error appropriately

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**What session resumption handles automatically (no application code needed):**

- ✅ Normal ~10 minute connection timeout
- ✅ Temporary network interruptions
- ✅ WebSocket connection drops
- ✅ Transparent reconnection with conversation context preserved
- ✅ Session resumption handle caching and management

**Error handling strategy:**

| Error Type | When to Handle | Recommended Action |
|------------|----------------|-------------------|
| `LlmCallsLimitExceededError` | Always catch explicitly | Log and investigate for infinite agent loops |
| `Exception` (catch-all) | For logging/debugging | Log unexpected errors; useful for production monitoring |

**Key insights:**

1. **Session resumption provides transparent reconnection** - ADK internally manages reconnection when connections are interrupted. No application-level retry logic is needed.

2. **Minimal error handling needed** - The official ADK samples use a simple pattern: handle `LlmCallsLimitExceededError` explicitly, and optionally add a catch-all `Exception` for logging unexpected errors.

3. **`LlmCallsLimitExceededError` is your cost safety net** - This is the primary error to handle explicitly. It prevents runaway costs from infinite agent loops.

4. **Unexpected exceptions are rare** - With session resumption enabled, connection-related exceptions should be handled automatically. If you see frequent unexpected exceptions, investigate your infrastructure or model configuration.

#### Don't

- ❌ Assume you need to manually handle Gemini's ~10 minute connection timeout (ADK does this automatically)
- ❌ Let sessions hit duration limits without warning users (if NOT using context window compression)
- ❌ Disable session resumption in production applications
- ❌ Forget to enable context window compression if you need sessions longer than 15 minutes (audio-only) or 2 minutes (audio+video)
- ❌ **Without context window compression on Gemini Live API**: Use video when not needed (limits session to 2 minutes instead of 15)
- ❌ Ignore platform-specific session duration limits in production planning (unless using context window compression)
- ❌ Confuse connection lifetime with session duration

## Concurrent sessions and quota management

**Problem:** Production voice applications typically serve multiple users simultaneously, each requiring their own Live API session. However, both Gemini Live API and Vertex AI Live API impose strict concurrent session limits that vary by platform and pricing tier. Without proper quota planning and session management, applications can hit these limits quickly, causing connection failures for new users or degraded service quality during peak usage.

**Solution:** Understand platform-specific quotas, design your architecture to stay within concurrent session limits, implement session pooling or queueing strategies when needed, and monitor quota usage proactively. ADK handles individual session lifecycle automatically, but developers must architect their applications to manage multiple concurrent users within quota constraints.

### Understanding Concurrent Session Quotas

Both platforms limit how many Live API sessions can run simultaneously, but the limits and mechanisms differ significantly:

**Gemini Live API (Google AI Studio) - Tier-based quotas:**

| Tier | Concurrent Sessions | TPM (Tokens Per Minute) | Access |
|------|---------------------|-------------------------|--------|
| **Free Tier** | Limited* | 1,000,000 | Free API key |
| **Tier 1** | 50 | 4,000,000 | Pay-as-you-go |
| **Tier 2** | 1,000 | 10,000,000 | Higher usage tier |
| **Tier 3** | 1,000 | 10,000,000 | Higher usage tier |

*Free tier concurrent session limits are not explicitly documented but are significantly lower than paid tiers.

> 📖 **Source**: [Gemini API Quotas](https://ai.google.dev/gemini-api/docs/quota)

**Vertex AI Live API (Google Cloud) - Project-based quotas:**

| Resource Type | Limit | Scope |
|---------------|-------|-------|
| **Concurrent live bidirectional connections** | 10 per minute | Per project, per region |
| **Maximum concurrent sessions** | Up to 1,000 | Per project |
| **Session creation/deletion/update** | 100 per minute | Per project, per region |

> 📖 **Source**: [Vertex AI Live API Streamed Conversations](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api/streamed-conversations) | [Vertex AI Quotas](https://cloud.google.com/vertex-ai/generative-ai/docs/quotas)

**Requesting a quota increase:**

To request an increase for Live API concurrent sessions, navigate to the [Quotas page](https://console.cloud.google.com/iam-admin/quotas) in the Google Cloud Console. Filter for the quota named **"Bidi generate content concurrent requests"** to find quota values for each project, region and base model, and submit a quota increase request. You'll need the Quota Administrator role (`roles/servicemanagement.quotaAdmin`) to make the request. See [View and manage quotas](https://cloud.google.com/docs/quotas/view-manage) for detailed instructions.

![Quota value on Cloud Console](assets/adk-streaming-guide-quota-console.png)

**Key differences:**

1. **Gemini Live API**: Concurrent session limits scale dramatically with API tier (50 → 1,000 sessions). Best for applications with unpredictable or rapidly scaling user bases willing to pay for higher tiers.

2. **Vertex AI Live API**: Rate-limited by connection establishment rate (10/min) but supports up to 1,000 total concurrent sessions. Best for enterprise applications with gradual scaling patterns and existing Google Cloud infrastructure. Additionally, you can request quota increases to prepare for production deployments with higher concurrency requirements.

### Architectural Patterns for Managing Quotas

Once you understand your concurrent session quotas, the next challenge is architecting your application to operate effectively within those limits. The right approach depends on your expected user concurrency, scaling requirements, and tolerance for queueing. This section presents two architectural patterns—from simple direct mapping for low-concurrency applications to session pooling with queueing for applications that may exceed quota limits during peak usage. Choose the pattern that matches your current scale and design it to evolve as your user base grows.

#### Pattern 1: Direct mapping (simple applications)

For small-scale applications where concurrent users will never exceed quota limits:

**The idea:** Create a dedicated Live API session for each connected user with a simple 1:1 mapping. When a user connects, immediately start a `run_live()` session for them. When they disconnect, the session ends. This pattern has no quota management logic—it assumes your total concurrent users will always stay below your quota limits. It's the simplest possible architecture and works well for prototypes, development environments, and small-scale applications with predictable user loads.

```python
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, SessionResumptionConfig

# Simple 1:1 mapping - one session per user
async def handle_user_connection(user_id: str, agent: Agent):
    runner = Runner(agent=agent)

    run_config = RunConfig(
        response_modalities=["AUDIO"],
        session_resumption=SessionResumptionConfig(mode="transparent")
    )

    async for event in runner.run_live(
        user_id=user_id,
        session_id=f"session-{user_id}",
        run_config=run_config
    ):
        # Stream events to user
        yield event
```

**✅ Use when:**

- Total concurrent users < 50 (Gemini Tier 1) or < 1,000 (Vertex AI)
- Simple architecture requirements
- Development and testing environments

**❌ Avoid when:**

- User base can exceed quota limits
- Need predictable scaling behavior
- Production applications with unknown peak loads

#### Pattern 2: Session pooling with queueing

For applications that may exceed concurrent session limits during peak usage:

**The idea:** Track the number of active Live API sessions and enforce your quota limit at the application level. When a new user tries to connect, check if you have available session slots. If slots are available, start a session immediately. If you've reached your quota limit, place the user in a waiting queue and notify them they're waiting for an available slot. As sessions end, automatically process the queue to start sessions for waiting users. This provides graceful degradation—users wait briefly during peak times rather than experiencing hard connection failures.

```python
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig

@dataclass
class SessionPool:
    max_sessions: int  # Set based on your quota tier
    active_sessions: Dict[str, asyncio.Task]
    waiting_queue: asyncio.Queue

    def __init__(self, max_sessions: int):
        self.max_sessions = max_sessions
        self.active_sessions = {}
        self.waiting_queue = asyncio.Queue()

    async def acquire_session(self, user_id: str) -> bool:
        """Attempt to start a new session or queue the request"""
        if len(self.active_sessions) < self.max_sessions:
            # Slot available - start session immediately
            return True
        else:
            # At capacity - queue the request
            await self.waiting_queue.put(user_id)
            return False

    def release_session(self, user_id: str):
        """Release a session and process queue"""
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]

            # Check if anyone is waiting
            if not self.waiting_queue.empty():
                # Notify waiting user that a slot is available
                asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        """Process waiting queue when slots become available"""
        if self.waiting_queue.empty():
            return

        waiting_user = await self.waiting_queue.get()
        # Notify application to start session for waiting_user
        # (Implementation depends on your architecture)

# Usage example
session_pool = SessionPool(max_sessions=50)  # Gemini Tier 1 limit

async def handle_user_with_pooling(user_id: str, agent: Agent):
    # Check if we can start a session
    can_start = await session_pool.acquire_session(user_id)

    if not can_start:
        # User is queued - notify them
        yield {"status": "queued", "message": "Waiting for available session slot"}
        # Wait for slot to become available
        # (Implementation depends on your queueing strategy)
        return

    try:
        runner = Runner(agent=agent)
        run_config = RunConfig(
            response_modalities=["AUDIO"],
            session_resumption=SessionResumptionConfig(mode="transparent")
        )

        # Track active session
        session_pool.active_sessions[user_id] = asyncio.current_task()

        async for event in runner.run_live(
            user_id=user_id,
            session_id=f"session-{user_id}",
            run_config=run_config
        ):
            yield event

    finally:
        # Always release session when done
        session_pool.release_session(user_id)
```

**✅ Use when:**

- Peak concurrent users may exceed quota limits
- Can tolerate queueing some users during peak times
- Want graceful degradation rather than hard failures

## Cost and Safety Controls

**Problem:** During development or in production, buggy tools or infinite agent loops can trigger excessive LLM API calls, leading to unexpected costs and quota exhaustion. Additionally, debugging voice interactions and maintaining compliance records requires persisting audio streams, which isn't enabled by default.

**Solution:** ADK provides built-in safeguards through `max_llm_calls` to cap the number of LLM invocations per session, preventing runaway costs. The `save_live_audio` option allows developers to persist audio streams to the session and artifact services for debugging, compliance auditing, and quality assurance purposes.

Protect against runaway costs and ensure conversation boundaries:

```python
run_config = RunConfig(
    # Limit total LLM calls per invocation
    max_llm_calls=500,  # Default: 500 (prevents runaway loops)
                        # 0 or negative = unlimited (use with caution)

    # Save audio artifacts for debugging/compliance
    save_live_audio=True  # Default: False
)
```

**max_llm_calls:**

Enforced by InvocationContext's `_invocation_cost_manager`, which increments a counter on each LLM call and raises `LlmCallsLimitExceededError` when the limit is exceeded. This prevents:

- Infinite loops in agent workflows
- Runaway costs from buggy tools
- Excessive API usage in development

**Why 500 is the default**: In typical conversational agents with tool use, 500 LLM calls represents 100-250 conversation turns (depending on tool complexity). This is sufficient for most legitimate use cases while protecting against infinite loops caused by:

- Tool execution errors that retry indefinitely
- Poorly designed agent logic that enters recursive loops
- Malicious inputs designed to exhaust API quotas

**save_live_audio:**

When enabled, ADK persists audio streams to:

- **Session service**: Conversation history includes audio references
- **Artifact service**: Audio files stored with unique IDs

**Use cases:** Development and testing environments where you want to prevent accidental cost overruns, production systems with strict budget constraints, regulated industries requiring audio conversation records (healthcare, financial services), debugging voice assistant behavior, and collecting training data for model improvement. Also useful for:

- Debugging voice interaction issues
- Compliance and audit trails
- Training data collection
- Quality assurance

**Storage considerations:**

Enabling `save_live_audio=True` has significant storage implications:

- **Audio file sizes**: At 16kHz PCM, audio input generates ~1.92 MB per minute
- **Session storage**: Audio is stored in both session service and artifact service
- **Retention policy**: Check your artifact service configuration for retention periods
- **Cost impact**: Storage costs can accumulate quickly for high-volume voice applications

**Best practices:**

- Enable only when needed (debugging, compliance, training)
- Implement retention policies to auto-delete old audio artifacts
- Consider sampling (e.g., save 10% of sessions for quality monitoring)
- Use compression if supported by your artifact service

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

When you enable `support_cfc=True`, ADK's behavior changes significantly:

1. **Backend Protocol**: ADK always connects to the Live API using WebSocket protocol (regardless of `streaming_mode`)
2. **Application Interface**: The `streaming_mode` parameter controls how ADK streams responses to your application code:
   - `StreamingMode.SSE`: Mimics SSE behavior in your async generator (request-response style)
   - `StreamingMode.BIDI`: Provides full bidirectional streaming capabilities

**Why this matters**: Even if you set `streaming_mode=StreamingMode.SSE`, CFC requires the Live API backend. The "SSE" setting only affects how events are yielded to your application—the underlying connection to Google's API is always WebSocket when CFC is enabled.

**Typical usage**: Most CFC use cases should use `StreamingMode.SSE` since CFC is primarily designed for text-based interactions with sophisticated multi-step tool orchestration, not real-time audio/video streaming.

**ADK Validation:**

CFC is the **only RunConfig feature with model validation** in ADK. When you enable `support_cfc=True`, ADK enforces these requirements at session initialization:

- **Model compatibility check**: Model name must start with `gemini-2*` (validated in `runners.py:1060-1066`)
  - ✅ Allowed: `gemini-2.5-flash-native-audio-preview-09-2025`, `gemini-2.0-flash-live-001`
  - ❌ Rejected: `gemini-1.5-pro`, `gemini-1.5-flash`
- **Code executor injection**: Automatically adds `BuiltInCodeExecutor` if not configured (required for parallel execution safety)

**Why only CFC is validated**: Other RunConfig features (VAD, transcription, proactivity) are validated by the Live API backend itself. ADK passes these configurations through without validation, relying on the API to return errors for unsupported features. CFC is validated in ADK because it requires specific model capabilities and code execution setup that can be checked before making API calls.

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
