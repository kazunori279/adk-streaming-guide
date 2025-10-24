# Part 5: How to Use Audio and Video

> 📖 **Source Reference**: Live API models support multimodal interactions via [Gemini Live API](https://ai.google.dev/gemini-api/docs/live) and [Vertex AI Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

This section covers audio and video capabilities in ADK's Live API integration, including supported models, audio architectures, specifications, and best practices for implementing voice and video features.

**⚠️ Disclaimer:** Model availability, capabilities, and discontinuation dates are subject to change. The information in this section represents a snapshot at the time of writing. For the most current model information, feature support, and availability:

- **Gemini Live API**: Check the [official Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live)
- **Vertex AI Live API**: Check the [official Vertex AI Live API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

Always verify model capabilities and preview/discontinuation timelines before deploying to production.

## How to Use Audio

These specifications apply universally to all Live API models on both Gemini Live API and Vertex AI Live API platforms.

- **Input audio**: 16-bit PCM, 16kHz, mono (`audio/pcm;rate=16000`)
- **Output audio**: 16-bit PCM, 24kHz, mono

**How Audio Works:**

Audio is exchanged with the Live API via `LiveRequestQueue` using PCM (Pulse Code Modulation) format:

**Sending Audio Input:**

```python
from google.genai.types import Blob

# Send audio data to the model
live_request_queue.send_realtime(
    Blob(data=audio_bytes, mime_type="audio/pcm")
)
```

**Receiving Audio Output:**

```python
async for event in live_events:
    # Extract the first Part from event content
    part = event.content and event.content.parts and event.content.parts[0]

    # Check if it's audio output
    if part and part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
        audio_data = part.inline_data.data
        # Process audio_data (e.g., play back, save to file)
```

For complete audio streaming examples, see the [Custom Audio Streaming app documentation](https://google.github.io/adk-docs/streaming/custom-streaming-ws/).

## How to Use Video

Unlike audio, which has two distinct processing architectures (Native Audio and Half-Cascade), **video does not have separate architectural variants** in the Live API. Video is processed through a straightforward frame-by-frame image processing approach:

- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 frame per second (1 FPS)
- **Resolution**: 768x768 pixels (recommended)

**How Video Works:**

- **Frame-Based Processing**: Video input is sent as sequential JPEG image frames at 1 frame per second
- **Standalone Image Processing**: Each frame is processed independently as a static image, not as a continuous video stream
- **No Special Pipeline**: There is no dedicated "video architecture" or processing pipeline—frames are handled using the same image understanding capabilities as static image input

Video frames are sent to ADK via `LiveRequestQueue` using the same `send_realtime()` method as audio, but with `image/jpeg` MIME type:

```python
from google.genai.types import Blob

# Send a video frame (JPEG image) to ADK
live_request_queue.send_realtime(
    Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
)
```

For implementing custom video streaming tools that process video frames, see the [Streaming Tools documentation](https://google.github.io/adk-docs/streaming/streaming-tools/).

**Session Duration Constraints:**

- **Audio-only sessions**: 15 minutes maximum
- **Audio + video sessions**: 2 minutes maximum (significantly shorter due to video processing overhead)

For complete video streaming tool examples, see the [Streaming Tools documentation](https://google.github.io/adk-docs/streaming/streaming-tools/).

## Model Compatibilities

The Live API is available through two platforms—Gemini Live API (Google AI Studio) and Vertex AI Live API (Google Cloud)—each offering different models with distinct audio processing architectures. This section covers the available models, their audio architecture types (Native Audio vs. Half-Cascade), and platform-specific features to help you choose the right model and platform for your use case.

### Understanding Audio Architectures

Both the Gemini Live API and Vertex AI Live API support two distinct audio generation architectures, each optimized for different use cases:

- **Native Audio**: A fully integrated end-to-end audio architecture where the model processes audio input and generates audio output directly, without intermediate text conversion. This approach enables more natural speech patterns, emotion awareness, and context-aware audio generation but currently has limited tool use support.

- **Half-Cascade (Cascaded)**: A hybrid architecture that combines native audio input processing with text-to-speech (TTS) output generation. Audio input is processed natively, but responses are first generated as text then converted to speech. This separation provides better reliability and more robust tool execution in production environments.


### Gemini Live API Models (Google AI Studio)

The [Gemini Live API](https://ai.google.dev/gemini-api/docs/live) accessed via Google AI Studio offers the following models:

**1. Native Audio Architecture**

Model: [`gemini-2.5-flash-native-audio-preview-09-2025`](https://ai.google.dev/gemini-api/docs/live)

**2. Half-Cascade Audio Architecture**

Models:

- [`gemini-live-2.5-flash-preview`](https://ai.google.dev/gemini-api/docs/live) (recommended for production)
- [`gemini-2.0-flash-live-001`](https://ai.google.dev/gemini-api/docs/live)

### Vertex AI Live API Models (Google Cloud)

The [Vertex AI Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api) provides enterprise-grade access with additional Google Cloud features.

**Half-Cascade Architecture**

Model: [`gemini-live-2.5-flash`](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api) (Private GA - Production Ready)

Optimized for production reliability:

- **Enhanced reliability and stability** for enterprise deployments
- **Supports all core Live API features**
- **Context window**: 32k tokens (configurable 5k-128k)
- **Best for**: Production applications requiring enterprise SLAs

**Vertex AI-Specific Features:**

- **Provisioned Throughput**: Reserved capacity for predictable performance
- **Up to 1,000 concurrent sessions** per Google Cloud project
- **24-hour session resumption window** (vs. 2 hours for Gemini API)
- **Enhanced monitoring and logging** via Google Cloud Console
- **Integration with Google Cloud services**: IAM, Cloud Logging, Cloud Monitoring
- **Enterprise support and SLAs**
- **Regional deployment options** for data residency requirements

**Billing Differences:**

- Usage tracked via Google Cloud project billing
- Proactive audio: Input audio tokens charged while listening; output audio tokens only charged when model responds
- Provisioned Throughput available for cost predictability

**When to Use Vertex AI Live API:**

- Production deployments requiring enterprise SLAs
- Applications needing >100 concurrent sessions
- Compliance requirements for data residency
- Integration with existing Google Cloud infrastructure
- Cost management via Google Cloud billing controls
- Access to Provisioned Throughput for guaranteed capacity

## Audio Transcription

Enable automatic transcription of audio streams without external services:

```python
run_config = RunConfig(
    # Transcribe user's spoken input
    input_audio_transcription=AudioTranscriptionConfig(enabled=True),

    # Transcribe model's spoken output
    output_audio_transcription=AudioTranscriptionConfig(enabled=True)
)
```

**Use cases:**

- **Accessibility**: Provide captions for hearing-impaired users
- **Logging**: Store text transcripts of voice conversations
- **Analytics**: Analyze conversation content without audio processing
- **Debugging**: Verify what the model heard vs. what it generated

The transcriptions are delivered through the same streaming event pipeline as `input_transcription` and `output_transcription` fields in LlmResponse objects.

**Troubleshooting:** If audio is not being transcribed, ensure `input_audio_transcription` (and/or `output_audio_transcription`) is enabled in `RunConfig`, and confirm audio MIME type and chunking are correct (`audio/pcm`, short contiguous chunks).

## Voice Activity Detection (VAD)

Configure real-time detection of when users are actively speaking:

```python
run_config = RunConfig(
    realtime_input_config=RealtimeInputConfig(
        voice_activity_detection=VoiceActivityDetectionConfig(enabled=True)
    )
)
```

**How it works:**

When VAD is enabled, Gemini Live API automatically analyzes incoming audio streams to detect:

- Speech start (user begins speaking)
- Speech end (user finishes speaking)
- Silence periods (pauses between words)

This enables the model to intelligently respond:

- Wait for natural pauses before responding
- Avoid interrupting mid-sentence
- Detect when the user has finished their thought

VAD is crucial for natural voice interactions, eliminating the need for "push-to-talk" buttons or manual turn-taking.

## Proactivity and Affective Dialog

Enable the model to be proactive and emotionally aware:

```python
run_config = RunConfig(
    # Model can initiate responses without explicit prompts
    proactivity=ProactivityConfig(enabled=True),

    # Model detects and adapts to user emotions
    enable_affective_dialog=True
)
```

**Proactivity:**

When enabled, the model can:

- Offer suggestions without being asked
- Provide follow-up information proactively
- Ignore irrelevant or off-topic input
- Anticipate user needs based on context

**Affective Dialog:**

The model analyzes emotional cues in voice tone and content to:

- Detect user emotions (frustrated, happy, confused, etc.)
- Adapt response style and tone accordingly
- Provide empathetic responses in customer service scenarios
- Adjust formality based on detected sentiment

## Live Audio Best Practices

- Prefer PCM audio (`mime_type="audio/pcm"`) with consistent sample rate across chunks.
- Send short, contiguous chunks (e.g., tens to hundreds of milliseconds) to reduce latency and preserve continuity.
- Use `send_activity_start()` when the user begins speaking and `send_activity_end()` when they finish to help the model time its responses.
- If `input_audio_transcription` is not enabled, ADK may use its own transcription path; enable it in `RunConfig` for end‑to‑end model transcription.
- For multimodal output, enable both `TEXT` and `AUDIO` in `response_modalities` (Vertex AI only; Gemini Live API supports only one modality per session).
