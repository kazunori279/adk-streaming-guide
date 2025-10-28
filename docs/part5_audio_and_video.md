# Part 5: How to Use Audio and Video

> 📖 **Source Reference**: Live API models support multimodal interactions via [Gemini Live API](https://ai.google.dev/gemini-api/docs/live) and [Vertex AI Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

This section covers audio and video capabilities in ADK's Live API integration, including supported models, audio architectures, specifications, and best practices for implementing voice and video features.

!!! warning "Model Availability Disclaimer"

    Model availability, capabilities, and discontinuation dates are subject to change. The information in this section represents a snapshot at the time of writing. For the most current model information, feature support, and availability:

    - **Gemini Live API**: Check the [official Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live)
    - **Vertex AI Live API**: Check the [official Vertex AI Live API documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

    Always verify model capabilities and preview/discontinuation timelines before deploying to production.

## How to Use Audio

These specifications apply universally to all Live API models on both Gemini Live API and Vertex AI Live API platforms.

- **Input audio**: 16-bit PCM, 16kHz, mono (`audio/pcm;rate=16000`)
- **Output audio**: 16-bit PCM, 24kHz, mono

> 📖 **Source**: [Gemini Live API - Audio formats](https://ai.google.dev/gemini-api/docs/live-guide)
>
> The Live API uses different sample rates for input (16kHz) and output (24kHz). The higher output rate provides better audio quality and more natural-sounding speech synthesis. When receiving audio output, you'll need to configure your audio playback system for 24kHz sample rate.

!!! note "Platform Compatibility: Audio Specifications"

    These audio specifications apply **uniformly across both platforms**:
    - ✅ **Gemini Live API**: 16-bit PCM at 16kHz input, 24kHz output
    - ✅ **Vertex AI Live API**: 16-bit PCM at 16kHz input, 24kHz output

    There are **no platform-specific differences** in audio format requirements, sample rates, or encoding. The same audio processing code works identically on both platforms.

### Audio Processing Flow in ADK

Understanding how audio moves through the system helps you implement efficient streaming:

**Input Flow**: Your App → `send_realtime(Blob)` → `LiveRequestQueue` → `run_live()` → Live API → Model
**Output Flow**: Model → Live API → `run_live()` events → Your App → Audio Playback

**Sending Audio Input:**

```python
from google.genai.types import Blob

# Send audio data to the model
live_request_queue.send_realtime(
    Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
)
```

**Receiving Audio Output:**

When `response_modalities=["AUDIO"]` is configured, the model returns audio data in the event stream as `inline_data` parts.

> ⚠️ **Important**: The Live API wire protocol transmits audio data as base64-encoded strings, but **the underlying SDK automatically decodes it**. When you access `part.inline_data.data`, you receive ready-to-use bytes—no manual base64 decoding needed.

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

# Configure for audio output
run_config = RunConfig(
    response_modalities=["AUDIO"],  # Required for audio responses
    streaming_mode=StreamingMode.BIDI
)

# Receiving Audio Output from the model
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_request_queue,
    run_config=run_config
):
    # Check if event contains audio output
    if event.content and event.content.parts:
        for part in event.content.parts:
            # Check if this part contains audio data
            if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                # ADK has already decoded the base64 audio data
                # part.inline_data.data contains raw PCM bytes ready for playback
                audio_bytes = part.inline_data.data

                # Process audio (e.g., stream to client, play back, save to file)
                await stream_audio_to_client(audio_bytes)

                # Or save to file
                # with open("output.pcm", "ab") as f:
                #     f.write(audio_bytes)
```

**Best Practices**:

1. **Chunked Streaming**: Send audio in small chunks for low latency. Choose chunk size based on your latency requirements:
   - **Ultra-low latency** (real-time conversation): 10-20ms chunks (~320-640 bytes @ 16kHz)
   - **Balanced** (recommended): 50-100ms chunks (~1600-3200 bytes @ 16kHz)
   - **Lower overhead**: 100-200ms chunks (~3200-6400 bytes @ 16kHz)

   Use consistent chunk sizes throughout the session for optimal performance. Example: 100ms @ 16kHz = 16000 samples/sec × 0.1 sec × 2 bytes/sample = 3200 bytes.
2. **Automatic Buffering**: ADK's `LiveRequestQueue` buffers chunks and sends them efficiently. Don't wait for model responses before sending next chunks.
3. **Continuous Processing**: The model processes audio continuously, not turn-by-turn. With automatic VAD enabled (the default), just stream continuously and let the API detect speech.
4. **Activity Signals**: Use `send_activity_start()` / `send_activity_end()` only when you explicitly disable VAD for manual turn-taking control. VAD is enabled by default, so activity signals are not needed for most applications.

For complete audio streaming examples, see:
- [Custom Audio Streaming app documentation](https://google.github.io/adk-docs/streaming/custom-streaming-ws/) (official ADK docs)
- [Demo Application](../src/demo/README.md) (working implementation in this repository)

## How to Use Video

Rather than typical video streaming using HLS, mp4, or H.264, video in ADK Bidi-streaming is processed through a straightforward frame-by-frame image processing approach.

!!! note "Platform Compatibility: Video Specifications"

    Video format specifications are **platform-agnostic**:
    - ✅ **Gemini Live API**: JPEG format, 1 FPS, 768x768 resolution
    - ✅ **Vertex AI Live API**: JPEG format, 1 FPS, 768x768 resolution

    **Platform-specific difference**:
    - ⚠️ **Session duration limits differ** when using video (see below)

**Video Specifications:**

- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 frame per second (1 FPS) recommended maximum
- **Resolution**: 768x768 pixels (recommended)

**Performance Characteristics**:

The 1 FPS (frame per second) recommended maximum reflects the current design focus:
- Live API video is optimized for **periodic visual context**, not real-time video analysis
- Each frame is treated as a high-quality image input (768x768 recommended)
- Processing overhead: Image understanding is computationally intensive

> ⚠️ **Important**: When using video, be aware of platform-specific session duration limits:
> - **Gemini Live API**: 2 minutes maximum for audio+video sessions (vs 15 minutes for audio-only)
> - **Vertex AI Live API**: 10 minutes for all sessions
>
> **When to enable Context Window Compression:**
> - ✅ **Enable if** you need sessions longer than these limits (enables unlimited duration)
> - ❌ **Don't enable if** all your sessions will be under the limits (simpler configuration)
>
> For sessions longer than these limits, enable [Context Window Compression](part4_run_config.md#context-window-compression) which removes time-based session duration limits. See [Part 4: Session Management](part4_run_config.md#session-management) for details and configuration examples.

**Typical Use Cases**:
- Security camera monitoring (periodic frame analysis)
- Document/whiteboard sharing in tutoring sessions
- Product inspection workflows
- Accessibility features (describing visual scenes periodically)

**Not Suitable For**:
- **Real-time video action recognition** - 1 FPS is too slow to capture rapid movements or actions
- **High-frame-rate video analysis** - API is optimized for periodic sampling, not continuous video processing
- **Video streaming applications requiring smooth playback** - API processes discrete frames as images, not temporal video streams
- **Live sports analysis or motion tracking** - Insufficient temporal resolution for fast-moving subjects

**Why these limitations exist**: The Live API's video capability is designed for **visual context**, not video processing. Each frame is treated as a high-quality image input (similar to sending photos), not as part of a temporal video sequence. For video analysis use cases requiring higher frame rates or temporal understanding, consider using the Gemini API's video understanding capabilities via `uploadFile()` instead.

Video frames are sent to ADK via `LiveRequestQueue` using the same `send_realtime()` method as audio, but with `image/jpeg` MIME type.

**Basic Usage**:

```python
from google.genai.types import Blob

# Send a video frame (JPEG image) to ADK
live_request_queue.send_realtime(
    Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
)
```

**Complete Example: Capture and Stream Video from Webcam**

```python
import cv2
import asyncio
import logging
from google.genai.types import Blob

logger = logging.getLogger(__name__)

async def stream_video_frames(live_request_queue):
    """Capture and stream video frames at recommended 1 FPS."""
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Failed to open webcam")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to capture frame")
                break

            # Resize to recommended resolution (768x768)
            frame = cv2.resize(frame, (768, 768))

            # Encode as JPEG
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            if not success:
                logger.warning("Failed to encode frame as JPEG")
                continue

            jpeg_frame_bytes = jpeg_buffer.tobytes()

            # Send to Live API
            live_request_queue.send_realtime(
                Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
            )

            # Respect 1 FPS recommendation
            await asyncio.sleep(1.0)
    except Exception as e:
        logger.error(f"Error in video streaming: {e}")
    finally:
        cap.release()
```

For implementing custom video streaming tools that process video frames, see the [Streaming Tools documentation](https://google.github.io/adk-docs/streaming/streaming-tools/).

## Model Compatibility for Audio

Different Live API models have different audio architecture and feature support. For comprehensive model compatibility information, see [Part 4: Model Compatibility](part4_run_config.md#model-compatibility).

### Understanding Audio Architectures

Both the Gemini Live API and Vertex AI Live API support two distinct audio generation architectures, each optimized for different use cases:

- **Native Audio**: A fully integrated end-to-end audio architecture where the model processes audio input and generates audio output directly, without intermediate text conversion. This approach enables more natural speech patterns, emotion awareness, and context-aware audio generation but currently has limited tool use support.

- **Half-Cascade (Cascaded)**: A hybrid architecture that combines native audio input processing with text-to-speech (TTS) output generation. Audio input is processed natively, but responses are first generated as text then converted to speech. This separation provides better reliability and more robust tool execution in production environments.

#### Why Audio Architectures Matter

When selecting a Live API model, you're choosing not just capabilities but also the underlying audio processing architecture. This choice affects:

- **Response naturalness**: Native audio produces more human-like speech with natural prosody
- **Tool execution reliability**: Half-Cascade provides more predictable tool call behavior
- **Latency characteristics**: Different architectures have different processing overhead
- **Use case suitability**: Voice assistants vs. customer service vs. tutoring

**How to choose**:
- **Native Audio** (`gemini-2.5-flash-native-audio-preview-09-2025`): Choose for natural conversational AI where speech quality matters most. Note: Limited tool use support currently.
- **Half-Cascade** (`gemini-live-2.5-flash-preview`, `gemini-2.0-flash-live-001`): Choose for production applications requiring robust tool execution and reliability.

| Model | Platform | Audio Architecture | Video Support | Best For |
|-------|----------|-------------------|---------------|----------|
| `gemini-2.5-flash-native-audio-preview-09-2025` | Gemini Live API | Native Audio | ✅ | Natural voice interactions |
| `gemini-live-2.5-flash-preview` | Gemini Live API | Half-Cascade | ✅ | Production reliability |
| `gemini-live-2.5-flash` | Vertex AI Live API | Half-Cascade | ✅ | Enterprise deployments |

!!! note "Platform Compatibility: Audio Architectures"

    **Architecture availability varies by platform:**

    **Gemini Live API:**
    - ✅ Native Audio architecture available (`gemini-2.5-flash-native-audio-preview-09-2025`)
    - ✅ Half-Cascade architecture available (`gemini-live-2.5-flash-preview`)

    **Vertex AI Live API:**
    - ❌ Native Audio architecture not currently available
    - ✅ Half-Cascade architecture available (`gemini-live-2.5-flash`)

    **Platform-specific difference**: Native audio models with advanced features (proactivity, affective dialog, more natural speech) are currently exclusive to Gemini Live API. Vertex AI Live API only offers half-cascade models, which provide better tool execution reliability but less natural speech patterns.

**In ADK**: You select the architecture implicitly by choosing the model name in your Agent configuration. ADK doesn't expose architecture-specific configuration—the model handles it internally.

## Audio Transcription

The Live API provides built-in audio transcription capabilities that automatically convert speech to text for both user input and model output. This eliminates the need for external transcription services and enables real-time captions, conversation logging, and accessibility features. ADK exposes these capabilities through `RunConfig`, allowing you to enable transcription for either or both audio directions.

> 📖 **Source**: [Gemini Live API - Audio transcriptions](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcriptions)

Enable automatic transcription of audio streams without external services:

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    # Transcribe user's spoken input
    input_audio_transcription=types.AudioTranscriptionConfig(enabled=True),

    # Transcribe model's spoken output
    output_audio_transcription=types.AudioTranscriptionConfig(enabled=True)
)
```

**Event Structure**:

Transcriptions are delivered as `types.Transcription` objects on the `Event` object:

```python
from google.genai import types

@dataclass
class Event:
    content: Optional[Content]  # Audio/text content
    input_transcription: Optional[types.Transcription]  # User speech → text
    output_transcription: Optional[types.Transcription]  # Model speech → text
    # ... other fields
```

> 💡 **Learn More**: For complete Event structure, see [Part 3: Understanding Events](part3_run_live.md#event-structure).

Each `Transcription` object has two attributes:
- **`.text`**: The transcribed text (string)
- **`.finished`**: Boolean indicating if transcription is complete (True) or partial (False)

**How Transcriptions Are Delivered**:

Transcriptions arrive as separate fields in the event stream, not as content parts. Always use defensive null checking when accessing transcription data:

```python
from google.adk.runners import Runner

# ... runner setup code ...

async for event in runner.run_live(...):
    # User's speech transcription (from input audio)
    if event.input_transcription:  # First check: transcription object exists
        # Access the transcription text and status
        user_text = event.input_transcription.text
        is_finished = event.input_transcription.finished

        # Second check: text is not None or empty
        # This handles cases where transcription is in progress or empty
        if user_text and user_text.strip():
            print(f"User said: {user_text} (finished: {is_finished})")

            # Update live captions UI (may be partial transcription)
            update_caption(user_text, is_user=True, is_final=is_finished)

    # Model's speech transcription (from output audio)
    if event.output_transcription:  # First check: transcription object exists
        model_text = event.output_transcription.text
        is_finished = event.output_transcription.finished

        # Second check: text is not None or empty
        # This handles cases where transcription is in progress or empty
        if model_text and model_text.strip():
            print(f"Model said: {model_text} (finished: {is_finished})")

            # Update live captions UI (may be partial transcription)
            update_caption(model_text, is_user=False, is_final=is_finished)
```

!!! tip "Best Practice for Transcription Null Checking"

    Always use two-level null checking for transcriptions:

    1. Check if the transcription object exists (`if event.input_transcription`)
    2. Check if the text is not empty (`if user_text and user_text.strip()`)

    This pattern prevents errors from `None` values and handles partial transcriptions that may be empty.

**Common Pattern: Accumulating Transcriptions**:

Many applications need to distinguish between partial (live captions) and final (logged) transcriptions. Here's a recommended pattern:

```python
from google.adk.runners import Runner

# Track finalized transcriptions for logging/storage
user_transcript_log = []
model_transcript_log = []

async for event in runner.run_live(...):
    # User's speech transcription (from input audio)
    if event.input_transcription:
        user_text = event.input_transcription.text
        is_finished = event.input_transcription.finished

        if user_text and user_text.strip():
            if is_finished:
                # Final transcription - log it permanently
                user_transcript_log.append(user_text)
                print(f"User (final): {user_text}")
                update_caption(user_text, is_user=True, is_final=True)
            else:
                # Partial transcription - update live UI only, don't log
                print(f"User (partial): {user_text}")
                update_caption(user_text, is_user=True, is_final=False)

    # Model's speech transcription (from output audio)
    if event.output_transcription:
        model_text = event.output_transcription.text
        is_finished = event.output_transcription.finished

        if model_text and model_text.strip():
            if is_finished:
                # Final transcription - log it permanently
                model_transcript_log.append(model_text)
                print(f"Model (final): {model_text}")
                update_caption(model_text, is_user=False, is_final=True)
            else:
                # Partial transcription - update live UI only, don't log
                print(f"Model (partial): {model_text}")
                update_caption(model_text, is_user=False, is_final=False)
```

This pattern provides:
- **Real-time feedback**: Partial transcriptions update the UI immediately
- **Accurate logging**: Only final transcriptions are stored
- **Better UX**: Users see live captions that may be revised before finalization

**Timing and Accuracy**:

- **Streaming delivery**: Transcriptions arrive in real-time as audio is processed
- **May be partial**: Early transcriptions can be revised as more audio context is available
- **Separate from audio**: Transcription events are independent of audio output events
- **Language support**: Automatically detects language from audio content without requiring explicit language configuration. The Live API supports transcription for 100+ languages including English, Spanish, French, German, Japanese, Chinese, Korean, Hindi, Arabic, and many more. For the complete list of supported languages, see the [Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcriptions)

!!! note "Platform Compatibility: Audio Transcription"

    Audio transcription capabilities are **platform-agnostic** and work identically on both:
    - ✅ **Gemini Live API**: Full transcription support (100+ languages)
    - ✅ **Vertex AI Live API**: Full transcription support (100+ languages)

    **No platform-specific differences** in:
    - Language support or detection
    - Transcription accuracy or timing
    - API configuration (`AudioTranscriptionConfig` usage)
    - Event structure or delivery mechanism

**Use cases:**

- **Accessibility**: Provide captions for hearing-impaired users
- **Logging**: Store text transcripts of voice conversations
- **Analytics**: Analyze conversation content without audio processing
- **Debugging**: Verify what the model heard vs. what it generated

**Troubleshooting:** If audio is not being transcribed, ensure `input_audio_transcription` (and/or `output_audio_transcription`) is enabled in `RunConfig`, and confirm audio MIME type and chunking are correct (`audio/pcm`, short contiguous chunks).

> 💡 **Learn More**: For complete event handling, see [Part 3: Transcription Events](part3_run_live.md#transcription-events).

## Voice Configuration (Speech Config)

The Live API provides voice configuration capabilities that allow you to customize how the model sounds when generating audio responses. Using `speech_config` in RunConfig, you can select from a variety of prebuilt voices and specify the language for speech synthesis, creating a more personalized and contextually appropriate voice experience for your application.

> 📖 **Source**: [Gemini Live API - Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide)

### Configuration Structure

The `speech_config` parameter uses a nested structure to specify voice and language settings:

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"
            )
        ),
        language_code="en-US"
    )
)
```

### Configuration Parameters

**`voice_config`**: Specifies which prebuilt voice to use for audio generation
- Configured through nested `VoiceConfig` and `PrebuiltVoiceConfig` objects
- `voice_name`: String identifier for the prebuilt voice (e.g., "Kore", "Puck", "Charon")

**`language_code`**: ISO 639 language code for speech synthesis (e.g., "en-US", "ja-JP")
- Determines the language and regional accent for synthesized speech
- **Model-specific behavior:**
  - **Half-Cascade models**: Use the specified `language_code` for TTS output
  - **Native audio models**: May ignore `language_code` and automatically determine language from conversation context. Consult model-specific documentation for support.

### Available Voices

The available voices vary by model architecture. To verify which voices are available for your specific model:
- Check the [Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live-guide) for the complete list
- Test voice configurations in development before deploying to production
- If a voice is not supported, the Live API will return an error

**Half-cascade models** support these voices:
- Puck
- Charon
- Kore
- Fenrir
- Aoede
- Leda
- Orus
- Zephyr

**Native audio models** support a longer list of voices identical to the Text-to-Speech (TTS) model list. Refer to the [Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live-guide) for the complete list of supported voices.

### Platform Availability

!!! note "Platform Compatibility: Voice Configuration"

    **Voice configuration is supported on both platforms**, but voice availability may vary:

    **Gemini Live API:**
    - ✅ Fully supported with documented voice options
    - ✅ Half-cascade models: 8 voices (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr)
    - ✅ Native audio models: Extended voice list (see [documentation](https://ai.google.dev/gemini-api/docs/live-guide))

    **Vertex AI Live API:**
    - ✅ Voice configuration supported
    - ⚠️ **Platform-specific difference**: Voice availability may differ from Gemini Live API
    - ⚠️ **Verification required**: Check [Vertex AI documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api) for the current list of supported voices

    **Best practice**: Always test your chosen voice configuration on your target platform during development. If a voice is not supported on your platform/model combination, the Live API will return an error at connection time.

### Use Cases

**Personalization**: Select voices that match your brand identity or application context

- Professional business applications might use formal-sounding voices
- Educational apps might use friendly, approachable voices
- Entertainment apps might use expressive, dynamic voices

**Localization**: Combine voice selection with language codes for regional experiences

- Match voice characteristics to cultural expectations
- Provide consistent voice personas across different language markets

**Accessibility**: Offer voice options to accommodate user preferences and needs

- Allow users to select voices they find easier to understand
- Provide variety for long-form content to reduce listening fatigue

### Important Notes

- **Model compatibility**: Voice configuration is only available for Live API models with audio output capabilities
- **Default behavior**: If `speech_config` is not specified, the Live API uses a default voice
- **Native audio models**: Automatically determine language based on conversation context; explicit `language_code` may not be supported
- **Voice availability**: Specific voice names may vary by model; refer to the current Live API documentation for supported voices on your chosen model

> 💡 **Learn More**: For complete RunConfig reference, see [Part 4: Understanding RunConfig](part4_run_config.md).

## Voice Activity Detection (VAD)

Voice Activity Detection (VAD) is a Live API feature that automatically detects when users start and stop speaking, enabling natural turn-taking without manual control. VAD is **enabled by default** on all Live API models, allowing the model to automatically manage conversation turns based on detected speech activity.

> 📖 **Source**: [Gemini Live API - Voice Activity Detection](https://ai.google.dev/gemini-api/docs/live-guide#voice-activity-detection-vad)

### How VAD Works

When VAD is enabled (the default), the Live API automatically:

1. **Detects speech start**: Identifies when a user begins speaking
2. **Detects speech end**: Recognizes when a user stops speaking (natural pauses)
3. **Manages turn-taking**: Allows the model to respond when the user finishes speaking
4. **Handles interruptions**: Enables natural conversation flow with back-and-forth exchanges

This creates a hands-free, natural conversation experience where users don't need to manually signal when they're speaking or done speaking.

!!! note "Platform Compatibility: Voice Activity Detection"

    VAD functionality is **platform-agnostic** and works identically on both:
    - ✅ **Gemini Live API**: Automatic VAD enabled by default
    - ✅ **Vertex AI Live API**: Automatic VAD enabled by default

    **No platform-specific differences** in:
    - VAD accuracy or detection sensitivity
    - Configuration options (`RealtimeInputConfig` usage)
    - Manual activity signal support (`ActivityStart`/`ActivityEnd`)

!!! note "Default VAD Behavior"

    VAD is enabled by default on all Live API models in two scenarios:

    1. When you **omit the `realtime_input_config` parameter entirely**, OR
    2. When you explicitly set `automatic_activity_detection.disabled=False`

    You don't need any configuration for hands-free conversation. Only configure `realtime_input_config.automatic_activity_detection.disabled=True` if you want to **disable** VAD for push-to-talk implementations.

### When to Disable VAD

You should disable automatic VAD in these scenarios:

- **Push-to-talk implementations**: Your application manually controls when audio should be sent (e.g., audio interaction apps in noisy environments or rooms with cross-talk)
- **Client-side voice detection**: Your application uses client-side VAD that sends activity signals to your server to reduce CPU and network overhead from continuous audio streaming
- **Specific UX patterns**: Your design requires users to manually indicate when they're done speaking

When you disable VAD (which is enabled by default), you must use manual activity signals (`ActivityStart`/`ActivityEnd`) to control conversation turns. See [Part 2: Activity Signals](part2_live_request_queue.md#activity-signals) for details on manual turn control.

### VAD Configurations

**Default behavior (VAD enabled, no configuration needed):**

```python
from google.adk.agents.run_config import RunConfig

# VAD is enabled by default - no explicit configuration needed
run_config = RunConfig(
    response_modalities=["AUDIO"]
)
```

**Disable automatic VAD (enables manual turn control):**

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    response_modalities=["AUDIO"],
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(
            disabled=True  # Disable automatic VAD
        )
    )
)
```

### Client-side VAD Example

When building voice-enabled applications, you may want to implement client-side Voice Activity Detection (VAD) to reduce CPU and network overhead. This pattern combines browser-based VAD with manual activity signals to control when audio is sent to the server.

**The architecture:**

1. **Client-side**: Browser detects voice activity using Web Audio API (AudioWorklet with RMS-based VAD)
2. **Signal coordination**: Send `activity_start` when voice detected, `activity_end` when voice stops
3. **Audio streaming**: Send audio chunks only during active speech periods
4. **Server configuration**: Disable automatic VAD since client handles detection

#### Server-side Configuration

First, disable automatic VAD in your RunConfig and set up the FastAPI endpoint:

```python
from fastapi import FastAPI, WebSocket
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.genai import types

# Configure RunConfig to disable automatic VAD
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,
    response_modalities=["AUDIO"],
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(
            disabled=True  # Client handles VAD
        )
    )
)
```

#### WebSocket Upstream Task

The upstream task receives both audio data and activity signals from the client:

```python
async def upstream_task(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Receives audio and activity signals from client."""
    try:
        while True:
            # Receive JSON message from WebSocket
            message = await websocket.receive_json()

            if message.get("type") == "activity_start":
                # Client detected voice - signal the model
                live_request_queue.send_activity_start()

            elif message.get("type") == "activity_end":
                # Client detected silence - signal the model
                live_request_queue.send_activity_end()

            elif message.get("type") == "audio":
                # Stream audio chunk to the model
                import base64
                audio_data = base64.b64decode(message["data"])
                audio_blob = types.Blob(
                    mime_type="audio/pcm;rate=16000",
                    data=audio_data
                )
                live_request_queue.send_realtime(audio_blob)

    except WebSocketDisconnect:
        live_request_queue.close()
```

#### Client-side VAD Implementation

On the client side, use AudioWorklet to implement RMS-based voice detection:

```javascript
// vad-processor.js - AudioWorklet processor for voice detection
class VADProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.threshold = 0.05;  // Adjust based on environment
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input.length > 0) {
            const channelData = input[0];
            let sum = 0;

            // Calculate RMS (Root Mean Square)
            for (let i = 0; i < channelData.length; i++) {
                sum += channelData[i] ** 2;
            }
            const rms = Math.sqrt(sum / channelData.length);

            // Signal voice detection status
            this.port.postMessage({
                voice: rms > this.threshold,
                rms: rms
            });
        }
        return true;
    }
}
registerProcessor('vad-processor', VADProcessor);
```

#### Client-side Coordination

Coordinate VAD signals with audio streaming and activity signals:

```javascript
// Main application logic
let isSilence = true;
let lastVoiceTime = 0;
const SILENCE_TIMEOUT = 2000;  // 2 seconds of silence before sending activity_end

// Set up VAD processor
const vadNode = new AudioWorkletNode(audioContext, 'vad-processor');
vadNode.port.onmessage = (event) => {
    const { voice, rms } = event.data;

    if (voice) {
        // Voice detected
        if (isSilence) {
            // Transition from silence to speech - send activity_start
            websocket.send(JSON.stringify({ type: "activity_start" }));
            isSilence = false;
        }
        lastVoiceTime = Date.now();
    } else {
        // No voice detected - check if silence timeout exceeded
        if (!isSilence && Date.now() - lastVoiceTime > SILENCE_TIMEOUT) {
            // Sustained silence - send activity_end
            websocket.send(JSON.stringify({ type: "activity_end" }));
            isSilence = true;
        }
    }
};

// Set up audio recorder to stream chunks
audioRecorderNode.port.onmessage = (event) => {
    const audioData = event.data;  // Float32Array

    // Only send audio when voice is detected
    if (!isSilence) {
        // Convert to PCM16 and send to server
        const pcm16 = convertFloat32ToPCM(audioData);
        const base64Audio = arrayBufferToBase64(pcm16);

        websocket.send(JSON.stringify({
            type: "audio",
            mime_type: "audio/pcm;rate=16000",
            data: base64Audio
        }));
    }
};
```

#### Benefits of Client-side VAD

This pattern provides several advantages:

- **Reduced CPU and network overhead**: Only send audio during active speech, not continuous silence
- **Faster response**: Immediate local detection without server round-trip
- **Better control**: Fine-tune VAD sensitivity based on client environment

!!! warning "Activity Signal Timing"

    When using manual activity signals with client-side VAD:

    - Always send `activity_start` **before** sending the first audio chunk
    - Always send `activity_end` **after** sending the last audio chunk
    - The model will only process audio between `activity_start` and `activity_end` signals
    - Incorrect timing may cause the model to ignore audio or produce unexpected behavior

## Proactivity and Affective Dialog

The Live API offers advanced conversational features that enable more natural and context-aware interactions. **Proactive audio** allows the model to intelligently decide when to respond, offer suggestions without explicit prompts, or ignore irrelevant input. **Affective dialog** enables the model to detect and adapt to emotional cues in voice tone and content, adjusting its response style for more empathetic interactions. These features are currently supported only on native audio models.

> 📖 **Source**: [Gemini Live API - Proactive audio](https://ai.google.dev/gemini-api/docs/live-guide#proactive-audio) | [Affective dialog](https://ai.google.dev/gemini-api/docs/live-guide#affective-dialog)

Enable the model to be proactive and emotionally aware:

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    # Model can initiate responses without explicit prompts
    proactivity=types.ProactivityConfig(proactive_audio=True),

    # Model adapts to user emotions
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

**Practical Example - Customer Service Bot**:

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

# Configure for empathetic customer service
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI,

    # Model can proactively offer help
    proactivity=types.ProactivityConfig(proactive_audio=True),

    # Model adapts to customer emotions
    enable_affective_dialog=True
)

# Example interaction (illustrative - actual model behavior may vary):
# Customer: "I've been waiting for my order for three weeks..."
# [Model may detect frustration in tone and adapt response]
# Model: "I'm really sorry to hear about this delay. Let me check your order
#        status right away. Can you provide your order number?"
#
# [Proactivity in action]
# Model: "I see you previously asked about shipping updates. Would you like
#        me to set up notifications for future orders?"
#
# Note: Proactive and affective behaviors are probabilistic. The model's
# emotional awareness and proactive suggestions will vary based on context,
# conversation history, and inherent model variability.
```

!!! note "Platform Compatibility: Proactivity and Affective Dialog"

    These features are **model-specific** and have platform implications:

    **Gemini Live API:**
    - ✅ Supported on `gemini-2.5-flash-native-audio-preview-09-2025` (native audio model)
    - ❌ Not supported on `gemini-live-2.5-flash-preview` (half-cascade model)

    **Vertex AI Live API:**
    - ❌ Not currently supported on `gemini-live-2.5-flash` (half-cascade model)
    - ⚠️ **Platform-specific difference**: Proactivity and affective dialog require native audio models, which are currently only available on Gemini Live API

    **Key insight**: If your application requires proactive audio or affective dialog features, you must use Gemini Live API with a native audio model. Half-cascade models on either platform do not support these features.

> 💡 **Learn More**: For latest feature compatibility, see [Part 4: Feature Support Matrix](part4_run_config.md#feature-support-matrix).

**Testing Proactivity**:

To verify proactive behavior is working:

1. **Create open-ended context**: Provide information without asking questions
   ```text
   User: "I'm planning a trip to Japan next month."
   Expected: Model offers suggestions, asks follow-up questions
   ```

2. **Test emotional response**:
   ```text
   User: [frustrated tone] "This isn't working at all!"
   Expected: Model acknowledges emotion, adjusts response style
   ```

3. **Monitor for unprompted responses**:
   - Model should occasionally offer relevant information
   - Should ignore truly irrelevant input
   - Should anticipate user needs based on context

**When to Disable**:

Consider disabling proactivity/affective dialog for:
- **Formal/professional contexts** where emotional adaptation is inappropriate
- **High-precision tasks** where predictability is critical
- **Accessibility applications** where consistent behavior is expected
- **Testing/debugging** where deterministic behavior is needed
