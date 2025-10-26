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

> 📖 **Source**: [Gemini Live API - Audio formats](https://ai.google.dev/gemini-api/docs/live-guide)
>
> The Live API uses different sample rates for input (16kHz) and output (24kHz). The higher output rate provides better audio quality and more natural-sounding speech synthesis. When receiving audio output, you'll need to configure your audio playback system for 24kHz sample rate.

### Audio Processing Flow in ADK

Understanding how audio moves through the system helps you implement efficient streaming:

**Input Flow**: Your App → `send_realtime(Blob)` → `LiveRequestQueue` → `run_live()` → Live API → Model
**Output Flow**: Model → Live API → `run_live()` events → Your App → Audio Playback

**Sending Audio Input:**

```python
from google.genai.types import Blob

# Send audio data to the model
live_request_queue.send_realtime(
    Blob(data=audio_bytes, mime_type="audio/pcm")
)
```

**Receiving Audio Output:**

When `response_modalities=["AUDIO"]` is configured, the model returns audio data in the event stream as `inline_data` parts.

> **Important**: The Live API wire protocol transmits audio data as base64-encoded strings, but **the underlying SDK automatically decodes it**. When you access `part.inline_data.data`, you receive ready-to-use bytes—no manual base64 decoding needed.

```python
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

For complete audio streaming examples, see the [Custom Audio Streaming app documentation](https://google.github.io/adk-docs/streaming/custom-streaming-ws/).

## How to Use Video

Rather than typical video streaming using HLS, mp4, or H.264, video in ADK Bidi-streaming is processed through a straightforward frame-by-frame image processing approach. These specifications apply universally to all Live API models on both Gemini Live API and Vertex AI Live API platforms:

- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 frame per second (1 FPS) recommended maximum
- **Resolution**: 768x768 pixels (recommended)

**Performance Characteristics**:

The 1 FPS (frame per second) recommended maximum reflects the current design focus:
- Live API video is optimized for **periodic visual context**, not real-time video analysis
- Each frame is treated as a high-quality image input (768x768 recommended)
- Processing overhead: Image understanding is computationally intensive

**Typical Use Cases**:
- Security camera monitoring (periodic frame analysis)
- Document/whiteboard sharing in tutoring sessions
- Product inspection workflows
- Accessibility features (describing visual scenes periodically)

**Not Suitable For**:
- Real-time video action recognition
- High-frame-rate video analysis
- Video streaming applications requiring smooth playback

Video frames are sent to ADK via `LiveRequestQueue` using the same `send_realtime()` method as audio, but with `image/jpeg` MIME type.

**Complete Example: Capture and Stream Video from Webcam**

```python
import cv2
import asyncio
from google.genai.types import Blob

async def stream_video_frames(live_request_queue):
    """Capture and stream video frames at recommended 1 FPS."""
    cap = cv2.VideoCapture(0)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize to recommended resolution (768x768)
            frame = cv2.resize(frame, (768, 768))

            # Encode as JPEG
            success, jpeg_buffer = cv2.imencode('.jpg', frame)
            if success:
                jpeg_frame_bytes = jpeg_buffer.tobytes()

                # Send to Live API
                live_request_queue.send_realtime(
                    Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
                )

            # Respect 1 FPS recommendation
            await asyncio.sleep(1.0)
    finally:
        cap.release()
```

**Basic Usage**:

```python
from google.genai.types import Blob

# Send a video frame (JPEG image) to ADK
live_request_queue.send_realtime(
    Blob(data=jpeg_frame_bytes, mime_type="image/jpeg")
)
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

**In ADK**: You select the architecture implicitly by choosing the model name in your Agent configuration. ADK doesn't expose architecture-specific configuration—the model handles it internally.

## Audio Transcription

The Live API provides built-in audio transcription capabilities that automatically convert speech to text for both user input and model output. This eliminates the need for external transcription services and enables real-time captions, conversation logging, and accessibility features. ADK exposes these capabilities through `RunConfig`, allowing you to enable transcription for either or both audio directions.

> 📖 **Source**: [Gemini Live API - Audio transcriptions](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcriptions)

Enable automatic transcription of audio streams without external services:

```python
run_config = RunConfig(
    # Transcribe user's spoken input
    input_audio_transcription=AudioTranscriptionConfig(enabled=True),

    # Transcribe model's spoken output
    output_audio_transcription=AudioTranscriptionConfig(enabled=True)
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

> 📖 **For complete Event structure**: See [Part 3: Understanding Events](part3_run_live.md#event-structure) for all Event fields and their descriptions.

Each `Transcription` object has two attributes:
- **`.text`**: The transcribed text (string)
- **`.finished`**: Boolean indicating if transcription is complete (True) or partial (False)

**How Transcriptions Are Delivered**:

Transcriptions arrive as separate fields in the event stream, not as content parts:

```python
async for event in runner.run_live(...):
    # User's speech transcription (from input audio)
    if event.input_transcription:
        # Access the transcription text and status
        user_text = event.input_transcription.text
        is_finished = event.input_transcription.finished

        print(f"User said: {user_text} (finished: {is_finished})")

        # Update live captions UI (may be partial transcription)
        update_caption(user_text, is_user=True, is_final=is_finished)

    # Model's speech transcription (from output audio)
    if event.output_transcription:
        model_text = event.output_transcription.text
        is_finished = event.output_transcription.finished

        print(f"Model said: {model_text} (finished: {is_finished})")

        # Update live captions UI (may be partial transcription)
        update_caption(model_text, is_user=False, is_final=is_finished)
```

**Timing and Accuracy**:

- **Streaming delivery**: Transcriptions arrive in real-time as audio is processed
- **May be partial**: Early transcriptions can be revised as more audio context is available
- **Separate from audio**: Transcription events are independent of audio output events
- **Language support**: Automatically detects language from audio content without requiring explicit language configuration. The Live API supports transcription for 100+ languages including English, Spanish, French, German, Japanese, Chinese, Korean, Hindi, Arabic, and many more. For the complete list of supported languages, see the [Gemini Live API documentation](https://ai.google.dev/gemini-api/docs/live-guide#audio-transcriptions)

**Use cases:**

- **Accessibility**: Provide captions for hearing-impaired users
- **Logging**: Store text transcripts of voice conversations
- **Analytics**: Analyze conversation content without audio processing
- **Debugging**: Verify what the model heard vs. what it generated

**Troubleshooting:** If audio is not being transcribed, ensure `input_audio_transcription` (and/or `output_audio_transcription`) is enabled in `RunConfig`, and confirm audio MIME type and chunking are correct (`audio/pcm`, short contiguous chunks).

> 📖 **For complete event handling**: See [Part 3: Transcription Events](part3_run_live.md#transcription-events)

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

The available voices vary by model architecture:

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

### Complete Example

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.agents.llm_agent import LlmAgent

# Create agent
agent = LlmAgent(
    name="voice_assistant",
    model="gemini-2.5-flash-native-audio-preview-09-2025"
)

# Configure with custom voice
run_config = RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"  # Choose from available voices
            )
        ),
        language_code="en-US"  # Specify language and region
    ),
    streaming_mode=StreamingMode.BIDI
)

# Run with voice configuration
runner = Runner(agent=agent)
async for event in runner.run_live(
    user_id="user123",
    session_id="session456",
    run_config=run_config
):
    # Process events with custom voice audio
    if event.content:
        # Audio output will use the "Kore" voice
        process_audio(event.content)
```

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

> 📖 **For RunConfig reference**: See [Part 4: Understanding RunConfig](part4_run_config.md) for complete configuration options

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

> **💡 Default Behavior**: VAD is enabled by default on all Live API models. You don't need any configuration for hands-free conversation. Only configure `realtime_input_config.automatic_activity_detection` if you want to **disable** VAD for push-to-talk implementations.

### When to Disable VAD

You should disable automatic VAD in these scenarios:

- **Push-to-talk implementations**: Your application manually controls when audio should be sent
- **Custom speech detection logic**: You have your own VAD implementation
- **Manual turn control requirements**: You need explicit control over conversation turns
- **Specific UX patterns**: Your design requires users to manually indicate when they're done speaking

When you disable VAD (which is enabled by default), you must use manual activity signals (`ActivityStart`/`ActivityEnd`) to control conversation turns. See [Part 2: Activity Signals](part2_live_request_queue.md#activity-signals) for details on manual turn control.

### Configuration

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

**Enable automatic VAD (default behavior - explicit configuration):**

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

run_config = RunConfig(
    response_modalities=["AUDIO"],
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(
            disabled=False  # Explicitly enable automatic VAD (default)
        )
    )
)
```

**Default behavior (VAD enabled, no configuration needed):**

```python
from google.adk.agents.run_config import RunConfig

# VAD is enabled by default - no explicit configuration needed
run_config = RunConfig(
    response_modalities=["AUDIO"]
)
```

### VAD vs Manual Activity Signals

Understanding the difference between automatic VAD and manual activity signals is crucial for implementing the right conversation control pattern:

| Aspect | Automatic VAD (Default) | Manual Activity Signals |
|--------|------------------------|------------------------|
| **Detection** | Automatic by Live API | Manual by your application |
| **Configuration** | Enabled by default | Requires disabling VAD + `ActivityStart`/`ActivityEnd` via LiveRequestQueue |
| **Use case** | Natural, hands-free conversations | Push-to-talk, custom UX patterns |
| **Turn control** | Live API manages turns | Application manages turns |
| **User experience** | Seamless, natural flow | Explicit user interaction required |

**Example: Using manual activity signals with VAD disabled:**

```python
from google.genai import types
from google.adk.agents.run_config import RunConfig

# Configure with VAD disabled for manual turn control
run_config = RunConfig(
    response_modalities=["AUDIO"],
    realtime_input_config=types.RealtimeInputConfig(
        automatic_activity_detection=types.AutomaticActivityDetection(
            disabled=True
        )
    )
)

# In your application code, manually control turns:
async for event in runner.run_live(
    user_id="user123",
    session_id="session456",
    run_config=run_config
):
    # When user starts speaking (e.g., button press)
    event.live_request_queue.send_activity_start()

    # Send audio chunks while user is speaking
    event.live_request_queue.send_realtime(audio_chunk)

    # When user stops speaking (e.g., button release)
    event.live_request_queue.send_activity_end()
```

> 💡 **Best Practice**: Use automatic VAD (default) for most voice applications. Only disable VAD when you have specific UX requirements that demand manual turn control, such as push-to-talk interfaces or custom speech detection logic.

> 📖 **RunConfig Reference**: For how VAD configuration fits into the overall RunConfig, see [Part 4: Understanding RunConfig](part4_run_config.md)

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

# Example interaction:
# Customer: "I've been waiting for my order for three weeks..."
# [Model detects frustration in tone]
# Model: "I'm really sorry to hear about this delay. Let me check your order
#        status right away. Can you provide your order number?"
#
# [Proactivity in action]
# Model: "I see you previously asked about shipping updates. Would you like
#        me to set up notifications for future orders?"
```

**Model Compatibility**:

Not all models support these features. Currently available on:
- ✅ `gemini-2.5-flash-native-audio-preview-09-2025` (Gemini Live API)
- ❌ `gemini-live-2.5-flash-preview` (not supported)
- ❌ `gemini-2.0-flash-live-001` (not supported)

> 📖 **Check latest compatibility**: See [Part 4: Feature Support Matrix](part4_run_config.md#feature-support-matrix)

**Testing Proactivity**:

To verify proactive behavior is working:

1. **Create open-ended context**: Provide information without asking questions
   ```
   User: "I'm planning a trip to Japan next month."
   Expected: Model offers suggestions, asks follow-up questions
   ```

2. **Test emotional response**:
   ```
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
