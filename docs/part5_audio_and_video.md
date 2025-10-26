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

When `response_modalities=["AUDIO"]` is configured, the model returns audio data in the event stream as `inline_data` parts. The audio is base64-encoded and must be decoded before playback or storage.

```python
import base64

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
                # The audio data is base64-encoded
                audio_bytes = base64.b64decode(part.inline_data.data)

                # Process audio (e.g., stream to client, play back, save to file)
                await stream_audio_to_client(audio_bytes)

                # Or save to file
                # with open("output.pcm", "ab") as f:
                #     f.write(audio_bytes)
```

**Best Practices**:

1. **Chunked Streaming**: Send audio in small chunks (10-100ms) for low latency. Use consistent chunk sizes (e.g., 100ms @ 16kHz = 3200 bytes) for optimal performance.
2. **Automatic Buffering**: ADK's `LiveRequestQueue` buffers chunks and sends them efficiently. Don't wait for model responses before sending next chunks.
3. **Continuous Processing**: The model processes audio continuously, not turn-by-turn. With automatic VAD enabled, just stream continuously and let the API detect speech.
4. **Activity Signals**: Use `send_activity_start()` / `send_activity_end()` only when VAD is disabled for manual turn-taking control.

For complete audio streaming examples, see the [Custom Audio Streaming app documentation](https://google.github.io/adk-docs/streaming/custom-streaming-ws/).

## How to Use Video

Rather than typical video streaming using HLS, mp4, or H.264, video in ADK Bidi-streaming is processed through a straightforward frame-by-frame image processing approach. These specifications apply universally to all Live API models on both Gemini Live API and Vertex AI Live API platforms:

- **Format**: JPEG (`image/jpeg`)
- **Frame rate**: 1 frame per second (1 FPS)
- **Resolution**: 768x768 pixels (recommended)

**Performance Characteristics**:

The 1 FPS (frame per second) limit reflects the current design focus:
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

Video frames are sent to ADK via `LiveRequestQueue` using the same `send_realtime()` method as audio, but with `image/jpeg` MIME type:

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

Transcriptions are delivered as string fields on the `Event` object:

```python
@dataclass
class Event:
    content: Optional[Content]  # Audio/text content
    input_transcription: Optional[str]  # User speech → text
    output_transcription: Optional[str]  # Model speech → text
    # ... other fields
```

**How Transcriptions Are Delivered**:

Transcriptions arrive as separate fields in the event stream, not as content parts:

```python
async for event in runner.run_live(...):
    # User's speech transcription (from input audio)
    if event.input_transcription:
        # Streaming transcription - may be partial
        user_text = event.input_transcription
        print(f"User said: {user_text}")

        # Update live captions UI
        update_caption(user_text, is_user=True)

    # Model's speech transcription (from output audio)
    if event.output_transcription:
        model_text = event.output_transcription
        print(f"Model said: {model_text}")

        # Update live captions UI
        update_caption(model_text, is_user=False)
```

**Timing and Accuracy**:

- **Streaming delivery**: Transcriptions arrive in real-time as audio is processed
- **May be partial**: Early transcriptions can be revised as more audio context is available
- **Separate from audio**: Transcription events are independent of audio output events
- **Language support**: Automatically detects language (supports 100+ languages)

**Use cases:**

- **Accessibility**: Provide captions for hearing-impaired users
- **Logging**: Store text transcripts of voice conversations
- **Analytics**: Analyze conversation content without audio processing
- **Debugging**: Verify what the model heard vs. what it generated

**Troubleshooting:** If audio is not being transcribed, ensure `input_audio_transcription` (and/or `output_audio_transcription`) is enabled in `RunConfig`, and confirm audio MIME type and chunking are correct (`audio/pcm`, short contiguous chunks).

> 📖 **For complete event handling**: See [Part 6: Events - Transcription Events](part6_events.md#transcription-events)

## Voice Activity Detection (VAD)

Voice Activity Detection (VAD) is a critical feature for natural voice interactions that automatically recognizes when a user is speaking. By analyzing the audio stream in real-time, VAD enables the model to detect speech boundaries, respond at appropriate moments, and handle interruptions gracefully—eliminating the need for push-to-talk buttons and creating seamless, hands-free conversational experiences.

> 📖 **Source**: [Gemini Live API - Voice Activity Detection](https://ai.google.dev/gemini-api/docs/live-guide#voice-activity-detection-vad)

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

**Advanced VAD Configuration**:

VAD behavior can be customized for different use cases:

```python
# Default: Automatic VAD enabled (recommended)
run_config = RunConfig(
    realtime_input_config=RealtimeInputConfig(
        voice_activity_detection=VoiceActivityDetectionConfig(enabled=True)
    )
)

# Disable VAD for manual control (push-to-talk)
run_config = RunConfig(
    realtime_input_config=RealtimeInputConfig(
        voice_activity_detection=VoiceActivityDetectionConfig(enabled=False)
    )
)
```

**When VAD is Disabled**:

With VAD disabled, you must manually signal turn boundaries using activity signals:

```python
# User presses "talk" button
live_request_queue.send_activity_start()

# Stream audio while button is pressed
while user_holding_button:
    live_request_queue.send_realtime(Blob(
        mime_type="audio/pcm;rate=16000",
        data=base64.b64encode(audio_chunk).decode()
    ))

# User releases button
live_request_queue.send_activity_end()
```

> 📖 **Activity Signals**: See [Part 2: Activity Signals](part2_live_request_queue.md#activity-signals) for detailed explanation

**VAD vs. Activity Signals**:

| Mode | VAD Enabled | Activity Signals | Use Case |
|------|-------------|-----------------|----------|
| **Automatic (default)** | ✅ Yes | ❌ Not needed | Hands-free voice interaction |
| **Push-to-talk** | ❌ No | ✅ Required | Manual control, high-noise environments |

## Proactivity and Affective Dialog

The Live API offers advanced conversational features that enable more natural and context-aware interactions. **Proactive audio** allows the model to intelligently decide when to respond, offer suggestions without explicit prompts, or ignore irrelevant input. **Affective dialog** enables the model to detect and adapt to emotional cues in voice tone and content, adjusting its response style for more empathetic interactions. These features are currently supported only on native audio models.

> 📖 **Source**: [Gemini Live API - Proactive audio](https://ai.google.dev/gemini-api/docs/live-guide#proactive-audio) | [Affective dialog](https://ai.google.dev/gemini-api/docs/live-guide#affective-dialog)

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

**Practical Example - Customer Service Bot**:

```python
# Configure for empathetic customer service
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI,

    # Model can proactively offer help
    proactivity=ProactivityConfig(enabled=True),

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
