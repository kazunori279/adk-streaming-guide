ADK Bidi-streaming demo app

This sample demonstrates the core ADK Bidi-streaming APIs.

## What's included
- `streaming_app.py`: FastAPI app with a WebSocket endpoint that bridges client messages to ADK and streams back Events in real time.
- Inline HTML UI at `/` to manually test text streaming from a browser.
- SSE endpoint at `/sse` for one-shot streaming via Server-Sent Events.

## Supported models for voice/video streaming

In order to use voice/video streaming in ADK, you will need to use Gemini models that support the Live API. You can find the **model ID(s)** that support the Gemini Live API in the documentation:

- [Google AI Studio: Gemini Live API](https://ai.google.dev/gemini-api/docs/models#live-api)
- [Vertex AI: Gemini Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

## Quick Start

The easiest way to run this demo is using the automated script:

```bash
cd src/demo
./run.sh
```

The script will automatically:
- Create a virtual environment
- Install dependencies (google-adk==1.16.0)
- Set up SSL certificates
- Start the server with debug logging
- Open the app at http://localhost:8000

## 1. Run the application

### Using the automated script (recommended)

```bash
cd src/demo
./run.sh
```

The script will handle setup and start the server. Press `CTRL+C` to stop.

### Manual setup (alternative)

If you prefer manual control:

1. Create and activate virtual environment:
   ```bash
   cd src/demo
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade google-adk==1.16.0
   export SSL_CERT_FILE=$(python -m certifi)
   ```

3. Start the server:
   ```bash
   uvicorn streaming_app:app --reload --port 8000
   ```

### Using the web interface

1. Open http://localhost:8000 in your browser
2. **Configure credentials in the UI:**
   - **For Gemini API (Google AI Studio):**
     - Select "Gemini API" radio button
     - Enter your API key from [Google AI Studio](https://aistudio.google.com/apikey)
   - **For Vertex AI (Google Cloud):**
     - Select "Vertex AI" radio button
     - Enter your GCP Project ID and Location (e.g., us-central1)
     - Make sure you have [set up Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/start/quickstarts/quickstart-multimodal#setup-gcp) and authenticated with `gcloud auth login`
3. Select a Live-capable model from the dropdown
4. Click "Connect" to establish WebSocket connection
5. Type a message (e.g., "Hello! Can you explain what ADK streaming is?")
6. Click "Send" and watch the streaming responses in the log area

**What to observe:**
- Partial events (`"partial": true`) show text chunks in real-time
- Each event contains metadata (invocationId, author, timestamp, actions)
- Final event has `"role": "model"` with complete response
- Turn completion signal (`"turnComplete": true`) marks the end

## Notes

- The server uses `InMemorySessionService` and creates a demo session (`user_id=demo-user`, `session_id=demo-session`).
- By default, the sample uses text-only responses. You can toggle transcription, VAD, proactivity, affective dialog, and session resumption using the UI checkboxes.
- The WebSocket accepts either plain text (converted to `Content`) or JSON that matches `LiveRequest` (for activity signals/blobs/close).

## Model Compatibility

**Important:** To enable both text and audio/video input, the model must support the `generateContent` (for text) and `bidiGenerateContent` methods. Verify these capabilities by referring to the [List Models Documentation](https://ai.google.dev/api/models#method:-models.list).

Recommended Live-capable models:
- **Gemini API:** `gemini-2.0-flash-live-001` or `gemini-2.5-flash-native-audio-preview-09-2025`
- **Vertex AI:** `gemini-live-2.5-flash-preview` or `gemini-live-2.5-flash-preview-native-audio`

**Note:** Non-Live models (e.g., `gemini-2.5-flash`) will fail for bidirectional streaming.

## Troubleshooting

- **When models don't work:** If you encounter errors with model availability, try switching to an alternative Live-capable model listed in the Model Compatibility section.
- **Connection issues:** If WebSocket connection fails, ensure the server is running and check the browser console for detailed error messages.
- **SSL Certificate issues:** Make sure you've set the `SSL_CERT_FILE` environment variable as described in the installation steps.
