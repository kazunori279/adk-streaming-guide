Simple ADK Streaming App (Part 2 Demo)

This sample demonstrates the core streaming APIs from Part 2:

- `LiveRequestQueue`: Sync producers → async consumer, unified message model
- `Runner.run_live(...)`: Async generator of `Event` objects
- `RunConfig`: Modalities, transcription, VAD, and other streaming settings

What’s included
- `streaming_app.py`: FastAPI app with a WebSocket endpoint that bridges client messages to ADK and streams back Events in real time.
- Inline HTML UI at `/` to manually test text streaming from a browser.

Prerequisites
- Python 3.10+
- Install dependencies (at minimum):
  - `google-adk` (ADK core)
  - `fastapi`, `uvicorn`
- Auth for Gemini (one of):
  - Set `GOOGLE_API_KEY` env var, or
  - Use Application Default Credentials (ADC)

Quick start
1) Install packages:
   pip install google-adk fastapi uvicorn

2) Set your model and credentials (examples):
   export GOOGLE_API_KEY=your_key_here
   export ADK_MODEL_NAME=gemini-2.0-flash-exp

3) Run the server:
   uvicorn src.part2.streaming_app:app --reload --port 8000

4) Open http://localhost:8000 in your browser

5) Use the web interface:
   a. The WebSocket URL field should be pre-filled with `ws://localhost:8000/ws`
   b. Click the "Connect" button to establish the WebSocket connection
   c. You should see "WS open" in the log area
   d. Type a message in the text input field (e.g., "Hello! Can you explain what ADK streaming is?")
   e. Click the "Send" button to send your message
   f. Watch the log area for streaming `Event` JSONs with partial and complete responses

6) Observe the streaming behavior:
   - Partial events (`"partial": true`) show text chunks arriving in real-time
   - Each event contains metadata (invocationId, author, timestamp, actions)
   - Final event has `"role": "model"` with complete response
   - Turn completion signal (`"turnComplete": true`) marks the end

Notes
- The server uses `InMemorySessionService` and creates a demo session (`user_id=demo-user`, `session_id=demo-session`).
- By default, the sample uses text-only responses. You can switch to audio/text via the `RunConfig` in the code.
- The WebSocket accepts either plain text (converted to `Content`) or JSON that matches `LiveRequest` (for activity signals/blobs/close).
- **Important**: Use `gemini-2.0-flash-exp` or another model that supports bidirectional streaming. Models like `gemini-2.5-flash` do not support `bidiGenerateContent` and will return a policy violation error.

Examples (WebSocket payloads)
- Plain text (turn-based):
  Hello there

- Graceful close:
  {"close": true}

- Activity signals (when constructing JSON yourself):
  {"activity_start": {}}
  {"activity_end": {}}

- Audio blob (base64-encoded PCM):
  {
    "blob": {
      "mime_type": "audio/pcm;rate=16000",
      "data": "<base64 chunk>"
    }
  }
