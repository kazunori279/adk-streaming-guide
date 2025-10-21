Simple ADK Streaming App (Part 2 Demo)

This sample demonstrates the core streaming APIs from Part 2:

- `LiveRequestQueue`: Sync producers → async consumer, unified message model
- `Runner.run_live(...)`: Async generator of `Event` objects
- `RunConfig`: Modalities, transcription, VAD, and other streaming settings

What’s included
- `streaming_app.py`: FastAPI app with a WebSocket endpoint that bridges client messages to ADK and streams back Events in real time.
- Inline HTML UI at `/` to manually test text streaming from a browser.
- SSE endpoint at `/sse` for one-shot streaming via Server-Sent Events.

Prerequisites
- Python 3.10+
- Install dependencies (at minimum):
  - `google-adk` (ADK core)
  - `fastapi`, `uvicorn`
- Auth and platform selection:
  - Gemini API (Google AI Studio):
    - `export GOOGLE_GENAI_USE_VERTEXAI=FALSE`
    - `export GOOGLE_API_KEY=...`
  - Vertex AI Live API (Google Cloud):
    - `export GOOGLE_GENAI_USE_VERTEXAI=TRUE`
    - `export GOOGLE_CLOUD_PROJECT=your_project_id`
    - `export GOOGLE_CLOUD_LOCATION=us-central1`

Quick start
1) Install packages:
   pip install google-adk fastapi uvicorn

2) Set your model and credentials (examples):
   # Choose one backend above, then pick a Live-capable model.
   # Gemini API examples:
   export GOOGLE_API_KEY=your_key_here
   export ADK_MODEL_NAME=gemini-2.0-flash-live-001
   # or for native audio preview:
   # export ADK_MODEL_NAME=gemini-2.5-flash-native-audio-preview-09-2025

   # Vertex AI examples:
   # export ADK_MODEL_NAME=gemini-live-2.5-flash-preview
   # or native audio:
   # export ADK_MODEL_NAME=gemini-live-2.5-flash-preview-native-audio

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
   g. You can also try SSE: keep the SSE URL as `http://localhost:8000/sse`, type a message, then click "Send via SSE" to stream a one-shot response.

6) Observe the streaming behavior:
   - Partial events (`"partial": true`) show text chunks arriving in real-time
   - Each event contains metadata (invocationId, author, timestamp, actions)
   - Final event has `"role": "model"` with complete response
   - Turn completion signal (`"turnComplete": true`) marks the end
   - If session resumption is enabled, `liveSessionResumptionUpdate` events will appear in the log

Notes
- The server uses `InMemorySessionService` and creates a demo session (`user_id=demo-user`, `session_id=demo-session`).
- By default, the sample uses text-only responses. You can toggle transcription, VAD, proactivity, affective dialog, and session resumption using the UI checkboxes.
- The WebSocket accepts either plain text (converted to `Content`) or JSON that matches `LiveRequest` (for activity signals/blobs/close).
- Use Live-capable model IDs. For Gemini API, prefer `gemini-2.0-flash-live-001` or native audio preview models. For Vertex AI, prefer `gemini-live-2.5-flash-preview` variants. Non-Live models (e.g., `gemini-2.5-flash`) will fail for bidi streaming.

SSE via curl (optional)
- Basic one-shot stream with a query message:
  curl -N "http://localhost:8000/sse?q=Hello&text_only=true"

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
