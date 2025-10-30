# Part 5: How to Use Audio, Image and Video

> 📖 **Source Reference**: Live API models support multimodal interactions via [Gemini Live API](https://ai.google.dev/gemini-api/docs/live) and [Vertex AI Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

This section covers audio, image and video capabilities in ADK's Live API integration, including supported models, audio model architectures, specifications, and best practices for implementing voice and video features.

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
> The Live API uses different sample rates for input (16kHz) and output (24kHz). When receiving audio output, you'll need to configure your audio playback system for 24kHz sample rate.

### Sending Audio Input

**Sending Audio Input:**

```python
from google.genai.types import Blob

# Send audio data to the model
live_request_queue.send_realtime(
    Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
)
```

#### Best Practices for Sending Audio Input

1. **Chunked Streaming**: Send audio in small chunks for low latency. Choose chunk size based on your latency requirements:
   - **Ultra-low latency** (real-time conversation): 10-20ms chunks (~320-640 bytes @ 16kHz)
   - **Balanced** (recommended): 50-100ms chunks (~1600-3200 bytes @ 16kHz)
   - **Lower overhead**: 100-200ms chunks (~3200-6400 bytes @ 16kHz)

   Use consistent chunk sizes throughout the session for optimal performance. Example: 100ms @ 16kHz = 16000 samples/sec × 0.1 sec × 2 bytes/sample = 3200 bytes.
2. **Automatic Buffering**: ADK's `LiveRequestQueue` buffers chunks and sends them efficiently. Don't wait for model responses before sending next chunks.
3. **Continuous Processing**: The model processes audio continuously, not turn-by-turn. With automatic VAD enabled (the default), just stream continuously and let the API detect speech.
4. **Activity Signals**: Use `send_activity_start()` / `send_activity_end()` only when you explicitly disable VAD for manual turn-taking control. VAD is enabled by default, so activity signals are not needed for most applications.

### Receiving Audio Output

When `response_modalities=["AUDIO"]` is configured, the model returns audio data in the event stream as `inline_data` parts.

**Receiving Audio Output:**

```python
from google.adk.agents.run_config import RunConfig, StreamingMode

# Configure for audio output
run_config = RunConfig(
    response_modalities=["AUDIO"],  # Required for audio responses
    streaming_mode=StreamingMode.BIDI
)

# Process audio output from the model
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

> ⚠️ **Important**: The Live API wire protocol transmits audio data as base64-encoded strings, but **the underlying SDK automatically decodes it**. When you access `part.inline_data.data`, you receive ready-to-use bytes—no manual base64 decoding needed.


## How to Use Image and Video

Both images and video in ADK Bidi-streaming are processed as JPEG frames. Rather than typical video streaming using HLS, mp4, or H.264, ADK uses a straightforward frame-by-frame image processing approach where both static images and video frames are sent as individual JPEG images.

**Image/Video Specifications:**

- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 frame per second (1 FPS) recommended maximum
- **Resolution**: 768x768 pixels (recommended)

**Sending Image/Video Input**:

```python
from google.genai.types import Blob

# Send a JPEG image to ADK
live_request_queue.send_realtime(
    Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
)
```

**Not Suitable For**:
- **Real-time video action recognition** - 1 FPS is too slow to capture rapid movements or actions
- **Live sports analysis or motion tracking** - Insufficient temporal resolution for fast-moving subjects

**Example Use Case for Image Processing**:
In the [Shopper's Concierge demo](https://youtu.be/LwHPYyw7u6U?si=lG9gl9aSIuu-F4ME&t=40), the application uses `send_realtime()` to send the user-uploaded image. The agent recognizes the context from the image and searches for relevant items on the e-commerce site.

<div class="video-grid">
  <div class="video-item">
    <div class="video-container">
<iframe width="560" height="315" src="https://www.youtube.com/embed/LwHPYyw7u6U?si=lG9gl9aSIuu-F4ME&amp;start=40" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    </div>
  </div>
</div>

### Custom video streaming tools support

ADK provides special tool support for processing video frames during streaming sessions. Unlike regular tools that execute synchronously, streaming tools can yield video frames asynchronously while the model continues to generate responses. This enables use cases where the agent needs to capture and analyze video frames on-demand during conversations—such as taking a snapshot when requested, monitoring a camera feed, or processing sequential frames for visual analysis.

For implementing custom video streaming tools that process and yield video frames to the model, see the [Streaming Tools documentation](https://google.github.io/adk-docs/streaming/streaming-tools/).

## Understanding Audio Model Architectures

When building voice applications with the Live API, one of the most important decisions is selecting the right audio model architecture. The Live API supports two fundamentally different type of models for audio processing: **Native Audio** and **Half-Cascade**. These model architectures differ in how they process audio input and generate audio output, which directly impacts response naturalness, tool execution reliability, latency characteristics, and overall use case suitability.

Understanding these architectures helps you make informed model selection decisions based on your application's requirements—whether you prioritize natural conversational AI, production reliability, or specific feature availability.

!!! warning "Model Availability Disclaimer"

    Model availability and architecture support are subject to change. The information in this section represents a snapshot at the time of writing. For the most current model information and availability:

    - **Gemini Live API**: Check the [official Gemini API models documentation](https://ai.google.dev/gemini-api/docs/models)
    - **Vertex AI Live API**: Check the [official Vertex AI models documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/models/)

Both Gemini Live API and Vertex AI Live API support these two distinct audio model architectures:

### Native Audio models

A fully integrated end-to-end audio model architecture where the model processes audio input and generates audio output directly, without intermediate text conversion. This approach enables more human-like speech with natural prosody.

| Audio Model Architecture | Platform | Model | Notes |
|-------------------|----------|-------|-------|
| Native Audio | Gemini Live API | [gemini-2.5-flash-native-audio-preview-09-2025](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash-live) |Publicly available|
| Native Audio | Vertex AI Live API | [gemini-live-2.5-flash-preview-native-audio-09-2025](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api) | Public preview |

**Key Characteristics:**

- **End-to-end audio processing**: Processes audio input and generates audio output directly without converting to text intermediately
- **Natural prosody**: Produces more human-like speech patterns, intonation, and emotional expressiveness
- **Extended voice library**: Supports all half-cascade voices plus additional voices from Text-to-Speech (TTS) service
- **Automatic language detection**: Determines language from conversation context without explicit configuration
- **Advanced conversational features**:
  - **[Affective dialog](#proactivity-and-affective-dialog)**: Adapts response style to input expression and tone, detecting emotional cues
  - **[Proactive audio](#proactivity-and-affective-dialog)**: Can proactively decide when to respond, offer suggestions, or ignore irrelevant input
  - **Dynamic thinking**: Supports thought summaries and dynamic thinking budgets
- **AUDIO-only response modality**: Does not support TEXT response modality with `RunConfig`, resulting in slower initial response times

### Half-Cascade (Cascaded) models

A hybrid architecture that combines native audio input processing with text-to-speech (TTS) output generation. Audio input is processed natively, but responses are first generated as text then converted to speech. This separation provides better reliability and more robust tool execution in production environments.

| Audio Model Architecture | Platform | Model | Notes |
|-------------------|----------|-------|-------|
| Half-Cascade | Gemini Live API | [gemini-2.0-flash-live-001](https://ai.google.dev/gemini-api/docs/models#gemini-2.0-flash-live) | Will be deprecated on December 09, 2025 |
| Half-Cascade | Vertex AI Live API | [gemini-live-2.5-flash](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash#2.5-flash) | Private GA, not publicly available |

**Key Characteristics:**

- **Hybrid architecture**: Combines native audio input processing with TTS-based audio output generation
- **TEXT response modality support**: Supports TEXT response modality  with `RunConfig` in addition to AUDIO, enabling much faster responses for text-only use cases
- **Explicit language control**: Supports manual language code configuration via `speech_config.language_code`
- **Established TTS quality**: Leverages proven text-to-speech technology for consistent audio output
- **Supported voices**: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr (8 prebuilt voices)

### Live API models compatibility and availability

For detailed compativility and availability test results of Live API models with the latest ADK version, see this [third-party test report](https://github.com/kazunori279/adk-streaming-test/blob/main/test_report.md).

> ⚠️ **Note**: This is a third-party resource maintained independently and is not officially endorsed. Always verify findings with the official documentation and your own testing.

## Audio Transcription

The Live API provides built-in audio transcription capabilities that automatically convert speech to text for both user input and model output. This eliminates the need for external transcription services and enables real-time captions, conversation logging, and accessibility features. ADK exposes these capabilities through `RunConfig`, allowing you to enable transcription for either or both audio directions.

> 📖 **Source**: [Gemini Live API - Audio transcriptions](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcriptions)

**Configuration:**

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

**Processing Transcriptions:**

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

## Voice Configuration (Speech Config)

The Live API provides voice configuration capabilities that allow you to customize how the model sounds when generating audio responses. Using `speech_config` in RunConfig, you can select from a variety of prebuilt voices and specify the language for speech synthesis, creating a more personalized and contextually appropriate voice experience for your application.

> 📖 **Source**: [Gemini Live API - Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide)

### Configuration Structure

**Configuration:**

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

**Native audio models** support an extended voice list that includes all half-cascade voices plus additional voices from the Text-to-Speech (TTS) service. For the complete list of voices supported by native audio models:
- See the [Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live-guide#available-voices)
- Or check the [Text-to-Speech voice list](https://cloud.google.com/text-to-speech/docs/voices) which native audio models also support

The extended voice list provides more options for voice characteristics, accents, and languages compared to half-cascade models.

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

**Configuration:**

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

**Implementation:**

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

**Implementation:**

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

**Coordinating VAD Signals:**

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

**Configuration:**

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
