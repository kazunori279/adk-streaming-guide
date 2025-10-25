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

## Session Limits and Planning

⚠️ **Critical Constraint**: Live API sessions have strict duration limits that differ between Gemini Live API and Vertex AI Live API. Understanding these limits is essential for planning audio and video implementations.

**Quick Reference**:

- **Gemini Live API**: 15 minutes (audio-only) or 2 minutes (audio+video)
- **Vertex AI Live API**: 10 minutes (all sessions)

> 📖 **For detailed session management**: See [Part 4: Session Management](part4_run_config.md#session-management) for comprehensive guidance on session limits, monitoring, resumption strategies, and production planning examples

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

**Use cases:**

- **Accessibility**: Provide captions for hearing-impaired users
- **Logging**: Store text transcripts of voice conversations
- **Analytics**: Analyze conversation content without audio processing
- **Debugging**: Verify what the model heard vs. what it generated

**Troubleshooting:** If audio is not being transcribed, ensure `input_audio_transcription` (and/or `output_audio_transcription`) is enabled in `RunConfig`, and confirm audio MIME type and chunking are correct (`audio/pcm`, short contiguous chunks).

> 📖 **For complete event handling**: See [Part 6: Events - Transcription Events](part6_events.md#transcription-events)

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

**Troubleshooting VAD**:

**Problem**: Model doesn't respond to speech
- **Check**: Ensure audio is `audio/pcm;rate=16000` format
- **Check**: Audio chunks are contiguous (no gaps)
- **Check**: Microphone volume is adequate (test with audio visualization)

**Problem**: Model responds too quickly (cutting off speech)
- **Possible cause**: VAD sensitivity too high for environment
- **Solution**: Consider disabling VAD and using push-to-talk

**Problem**: Model waits too long before responding
- **Possible cause**: Ambient noise causing VAD to detect continuous speech
- **Solution**: Improve audio input quality or use push-to-talk

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

## Live Audio Best Practices

### Audio Format and Chunking

- **Use PCM audio**: Always use `mime_type="audio/pcm;rate=16000"` with consistent sample rate across chunks
- **Optimal chunk size**: Send audio in 50-100ms chunks (800-1600 bytes at 16kHz)
- **Maintain continuity**: Ensure chunks are contiguous with no gaps to avoid audio artifacts
- **Consistent timing**: Use a fixed interval timer (e.g., 100ms) for chunk delivery

```python
# Example: Sending audio in optimal chunks
CHUNK_SIZE = 1600  # 100ms @ 16kHz = 1600 bytes
async def stream_audio(audio_stream):
    while True:
        chunk = await audio_stream.read(CHUNK_SIZE)
        if not chunk:
            break
        live_request_queue.send_realtime(Blob(
            mime_type="audio/pcm;rate=16000",
            data=base64.b64encode(chunk).decode()
        ))
        await asyncio.sleep(0.1)  # 100ms interval
```

### Error Handling

```python
from google.genai.errors import LiveAPIError

try:
    async for event in runner.run_live(...):
        # Process events
        pass
except LiveAPIError as e:
    # Handle Live API-specific errors
    logger.error(f"Live API error: {e}")
    # Implement retry logic or graceful degradation
except Exception as e:
    # Handle unexpected errors
    logger.exception("Unexpected error during live session")
```

### Performance Optimization

**Audio Input**:
- **Pre-process audio**: Normalize volume, remove silence, apply noise reduction before sending
- **Monitor queue depth**: Check `LiveRequestQueue` buffer size to avoid memory issues
- **Adaptive bitrate**: Consider reducing quality in poor network conditions

**Audio Output**:
- **Buffer output audio**: Maintain a small playback buffer (200-500ms) for smooth playback
- **Handle late packets**: Implement jitter buffer to handle network variability
- **Quality monitoring**: Track audio dropouts and adjust buffering strategy

### Testing Strategies

**Unit Testing**:
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_audio_streaming():
    # Mock LiveRequestQueue
    mock_queue = Mock()
    mock_queue.send_realtime = Mock()

    # Send test audio chunk
    test_chunk = b'\x00' * 1600  # 100ms silence
    mock_queue.send_realtime(Blob(
        mime_type="audio/pcm;rate=16000",
        data=base64.b64encode(test_chunk).decode()
    ))

    # Verify chunk was sent
    assert mock_queue.send_realtime.called
```

**Integration Testing**:
- **Test with real audio**: Use recorded audio samples for consistent testing
- **Test VAD behavior**: Verify speech detection with various audio inputs
- **Test interruption handling**: Send audio while model is speaking
- **Test edge cases**: Silence, background noise, multiple speakers

### Production Deployment Considerations

**Monitoring**:
- **Track latency**: Monitor time from user speech to model response
- **Audio quality metrics**: Track sample rate, bit depth, packet loss
- **Session metrics**: Monitor session duration, interruption rate, error rate
- **User experience**: Collect feedback on audio clarity and responsiveness

**Scaling**:
- **Connection pooling**: Reuse WebSocket connections when possible
- **Load balancing**: Distribute sessions across multiple servers
- **Session management**: Implement graceful session cleanup and resumption
- **Resource limits**: Set max concurrent sessions per instance

**Security**:
- **Audio encryption**: Ensure audio data is encrypted in transit (TLS/SSL)
- **User authentication**: Verify user identity before starting sessions
- **Rate limiting**: Prevent abuse with per-user session limits
- **Content filtering**: Consider filtering sensitive audio content

### Common Pitfalls

**❌ Don't**:
- Send large audio chunks (>1 second) - increases latency
- Mix sample rates within a session - causes audio artifacts
- Send audio without proper error handling - crashes on network issues
- Ignore VAD recommendations - leads to poor user experience
- Skip audio normalization - causes inconsistent behavior

**✅ Do**:
- Send consistent 50-100ms chunks for optimal latency
- Use fixed sample rate (16kHz) throughout the session
- Implement comprehensive error handling and retry logic
- Enable VAD for hands-free interactions
- Pre-process audio for consistent volume and quality

**Response Modalities and Audio**:

When configuring audio sessions, you must choose between TEXT or AUDIO response modality—never both. This is a fundamental Live API constraint:

```python
# Audio-only responses (most common for voice applications)
run_config = RunConfig(
    response_modalities=["AUDIO"],
    streaming_mode=StreamingMode.BIDI
)

# Text-only responses (for chat with audio input)
run_config = RunConfig(
    response_modalities=["TEXT"],
    streaming_mode=StreamingMode.BIDI
)
```

If you need both audio output and text transcripts, use `output_audio_transcription` (see [Audio Transcription](#audio-transcription)) rather than mixing modalities.

> 📖 **For detailed explanation**: See [Part 4: Response Modalities](part4_run_config.md#response-modalities)

## Troubleshooting Audio and Video Issues

### Common Audio Issues

#### No Audio Output Received

**Symptoms**: Model responds with text but no audio is generated

**Possible Causes**:
1. Response modality not set to `AUDIO`
2. Model doesn't support audio output
3. Audio generation failed silently

**Solutions**:
```python
# ✅ Ensure response_modalities is set correctly
run_config = RunConfig(
    response_modalities=["AUDIO"],  # Not ["TEXT"]
    streaming_mode=StreamingMode.BIDI
)

# ✅ Check event for audio data
async for event in runner.run_live(...):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data:
                print(f"Audio MIME: {part.inline_data.mime_type}")
                print(f"Audio size: {len(part.inline_data.data)} bytes")
```

#### Distorted or Garbled Audio Output

**Symptoms**: Audio plays but sounds distorted, choppy, or garbled

**Possible Causes**:
1. Incorrect playback sample rate (using 16kHz instead of 24kHz)
2. Missing or incorrect base64 decoding
3. Audio buffer underrun

**Solutions**:
```python
# ✅ Use correct sample rate for playback
import base64
import pyaudio

p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=24000,  # ⚠️ Output is 24kHz, not 16kHz!
    output=True
)

async for event in runner.run_live(...):
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
                # ✅ Decode base64 before playback
                audio_bytes = base64.b64decode(part.inline_data.data)
                stream.write(audio_bytes)
```

#### Model Doesn't Respond to Speech

**Symptoms**: Audio input sent but model doesn't respond

**Possible Causes**:
1. Incorrect audio format (wrong sample rate, bit depth, or encoding)
2. Audio chunks too large or too small
3. VAD not detecting speech
4. Activity signals not sent (when VAD disabled)

**Solutions**:
```python
# ✅ Verify audio format
assert audio_format == "audio/pcm;rate=16000"
assert sample_rate == 16000
assert bit_depth == 16
assert channels == 1  # mono

# ✅ Send appropriately sized chunks
CHUNK_DURATION_MS = 100  # 100ms
SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes
CHUNK_SIZE = (CHUNK_DURATION_MS * SAMPLE_RATE * BYTES_PER_SAMPLE) // 1000
# CHUNK_SIZE = 1600 bytes

# ✅ Enable VAD or use activity signals
run_config = RunConfig(
    realtime_input_config=RealtimeInputConfig(
        voice_activity_detection=VoiceActivityDetectionConfig(enabled=True)
    )
)

# Or with VAD disabled:
live_request_queue.send_activity_start()
# ... send audio ...
live_request_queue.send_activity_end()
```

#### Audio Transcription Not Working

**Symptoms**: Audio is processed but transcription is empty or missing

**Possible Causes**:
1. Transcription not enabled in `RunConfig`
2. Audio quality too poor for transcription
3. Language not supported

**Solutions**:
```python
# ✅ Enable transcription
run_config = RunConfig(
    input_audio_transcription=AudioTranscriptionConfig(enabled=True),
    output_audio_transcription=AudioTranscriptionConfig(enabled=True)
)

# ✅ Check for transcription in events
async for event in runner.run_live(...):
    if event.input_transcription:
        print(f"User transcription: {event.input_transcription}")
    if event.output_transcription:
        print(f"Model transcription: {event.output_transcription}")

# ✅ Improve audio quality
# - Reduce background noise
# - Ensure clear speech (not mumbling)
# - Check microphone positioning and volume
```

### Common Video Issues

#### Video Frames Not Processed

**Symptoms**: Video frames sent but not acknowledged or processed

**Possible Causes**:

1. Incorrect MIME type
2. Frame size too large
3. Frame rate exceeds 1 FPS
4. Session duration limit exceeded (Gemini: 2 min for audio+video; Vertex: 10 min default)

**Solutions**:
```python
import time
from PIL import Image
import io
import base64

# ✅ Ensure correct format and frame rate
last_frame_time = 0
FRAME_INTERVAL = 1.0  # 1 second = 1 FPS

def send_video_frame(image_path):
    global last_frame_time

    # Enforce 1 FPS limit
    now = time.time()
    if now - last_frame_time < FRAME_INTERVAL:
        return  # Skip frame
    last_frame_time = now

    # ✅ Resize to recommended resolution
    img = Image.open(image_path)
    img = img.resize((768, 768))

    # ✅ Convert to JPEG
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    jpeg_bytes = buffer.getvalue()

    # ✅ Send with correct MIME type
    live_request_queue.send_realtime(Blob(
        mime_type="image/jpeg",  # Not "video/jpeg"!
        data=base64.b64encode(jpeg_bytes).decode()
    ))

# ✅ Monitor session duration for audio+video
session_start = time.time()
# Gemini Live API: 2 minutes for audio+video
# Vertex AI Live API: 10 minutes default
MAX_DURATION = 120  # 2 minutes (Gemini) or 600 (Vertex)

while time.time() - session_start < MAX_DURATION:
    send_video_frame(frame_path)
    await asyncio.sleep(1)  # 1 FPS
```

#### Poor Video Understanding Quality

**Symptoms**: Model processes frames but misunderstands content

**Possible Causes**:
1. Image resolution too low
2. Poor lighting or image quality
3. Too much motion between frames
4. Ambiguous visual content

**Solutions**:
- **Use recommended resolution**: 768x768 pixels
- **Improve image quality**: Good lighting, focus, contrast
- **Stabilize camera**: Reduce motion blur and shake
- **Add context**: Use text prompts to clarify what model should look for
- **Consider frame rate**: 1 FPS means 1-second intervals; critical moments might be missed

### Performance Issues

#### High Latency (Slow Responses)

**Symptoms**: Long delay between user input and model response

**Possible Causes**:
1. Large audio/video chunks
2. Network latency
3. Server overload
4. Inefficient audio processing

**Solutions**:
```python
# ✅ Use optimal chunk sizes
AUDIO_CHUNK_SIZE = 1600  # 100ms @ 16kHz
VIDEO_FRAME_INTERVAL = 1.0  # 1 second

# ✅ Monitor latency
import time

input_timestamp = time.time()
live_request_queue.send_realtime(audio_chunk)

async for event in runner.run_live(...):
    if event.content:
        latency = time.time() - input_timestamp
        print(f"Response latency: {latency:.2f}s")

        # ✅ Alert if latency exceeds threshold
        if latency > 2.0:
            logger.warning(f"High latency detected: {latency:.2f}s")
```

#### Session Disconnects or Timeouts

**Symptoms**: Sessions terminate unexpectedly

**Possible Causes**:

1. Session duration limit exceeded:
   - Gemini Live API: 15 min (audio-only) or 2 min (audio+video)
   - Vertex AI Live API: 10 min default
2. Network interruption
3. Idle timeout (no activity)
4. Server-side error

**Solutions**:

```python
# ✅ Track session duration
import time

session_start = time.time()

# For Gemini Live API:
MAX_AUDIO_DURATION = 15 * 60  # 15 minutes (audio-only)
MAX_VIDEO_DURATION = 2 * 60   # 2 minutes (audio+video)

# For Vertex AI Live API:
# MAX_DURATION = 10 * 60  # 10 minutes default

while True:
    elapsed = time.time() - session_start

    # Gemini Live API limits
    if using_video and elapsed > MAX_VIDEO_DURATION - 10:
        print("⚠️ Approaching 2-minute limit for audio+video (Gemini)")
        # Prepare to gracefully end session
        break
    elif not using_video and elapsed > MAX_AUDIO_DURATION - 60:
        print("⚠️ Approaching 15-minute limit for audio-only (Gemini)")
        break

    # Vertex AI Live API limits
    # if elapsed > MAX_DURATION - 60:
    #     print("⚠️ Approaching 10-minute limit (Vertex)")
    #     # Gracefully end session
    #     break

    # Continue processing...

# ✅ Implement session resumption
try:
    async for event in runner.run_live(...):
        # Process events
        pass
except Exception as e:
    logger.error(f"Session error: {e}")
    # Attempt to resume or start new session
    await resume_session()
```

### Debugging Strategies

**Enable Verbose Logging**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("google.adk")
logger.setLevel(logging.DEBUG)
```

**Inspect Event Stream**:
```python
async for event in runner.run_live(...):
    print(f"Event type: {type(event)}")
    print(f"Event content: {event.content}")
    print(f"Event transcription: {event.input_transcription}, {event.output_transcription}")
    print(f"Event metadata: {event}")
```

**Validate Audio Data**:
```python
# Check audio chunk properties
import struct

def validate_audio_chunk(audio_bytes):
    # Check size (should be even for 16-bit)
    assert len(audio_bytes) % 2 == 0, "Audio chunk size not aligned to 16-bit samples"

    # Check for silence (all zeros)
    if audio_bytes == b'\x00' * len(audio_bytes):
        logger.warning("Audio chunk is complete silence")

    # Check amplitude range
    samples = struct.unpack(f'{len(audio_bytes)//2}h', audio_bytes)
    max_amplitude = max(abs(s) for s in samples)
    if max_amplitude < 100:
        logger.warning(f"Very low audio amplitude: {max_amplitude}")

    return True
```

**Test with Known-Good Data**:
```python
# Use pre-recorded audio for consistent testing
with open("test_audio_16khz_mono.pcm", "rb") as f:
    test_audio = f.read()

# Send in chunks
CHUNK_SIZE = 1600
for i in range(0, len(test_audio), CHUNK_SIZE):
    chunk = test_audio[i:i+CHUNK_SIZE]
    live_request_queue.send_realtime(Blob(
        mime_type="audio/pcm;rate=16000",
        data=base64.b64encode(chunk).decode()
    ))
    await asyncio.sleep(0.1)
```

> 📖 **For more troubleshooting**: See [Part 3: run_live()](part3_run_live.md#troubleshooting) and [Part 6: Events](part6_events.md#troubleshooting)
