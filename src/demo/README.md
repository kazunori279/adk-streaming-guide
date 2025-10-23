ADK Bidi-streaming demo app

This sample demonstrates the core ADK Bidi-streaming APIs.

## What's included

### Application Files
- **`streaming_app.py`**: FastAPI app with WebSocket and SSE endpoints for bidirectional streaming
  - WebSocket endpoint at `/ws` for real-time two-way communication
  - SSE endpoint at `/sse` for interactive streaming with bidirectional communication
  - POST endpoints `/sse-send` and `/sse-close` for sending messages and closing SSE sessions
  - Dynamic credential configuration (Gemini API or Vertex AI)
  - Serves static UI from `static/index.html`
  - Mutual exclusivity: WebSocket and SSE connections cannot be active simultaneously

### Agent Module
- **`agent/agent.py`**: Modular agent definition with Google Search integration
  - `create_streaming_agent()` function to instantiate the agent
  - Built-in Google Search tool for real-time web search capabilities
  - Clean separation of agent logic from application code

### User Interface
- **`static/index.html`**: Interactive web UI for testing bidirectional streaming
  - WebSocket and SSE connection management with mutual exclusivity
  - LiveRequestQueue controls: `send_content()` and `close()` buttons work with both WebSocket and SSE
  - Live streaming response viewer with color-coded event types
  - RunConfig toggles (transcription, VAD, proactivity, affective dialog, session resumption)
  - Support for both Gemini API and Vertex AI backends
  - Model selection dropdown with Live-capable models

## Project Structure

```
src/demo/
├── agent/
│   ├── __init__.py          # Agent module initialization
│   └── agent.py             # Agent definition with Google Search tool
├── static/
│   └── index.html           # Web UI for testing streaming
├── streaming_app.py         # FastAPI application with WebSocket/SSE endpoints
├── run.sh                   # Automated setup and run script
└── README.md                # This file
```

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
4. **Choose connection type:**
   - **WebSocket:** Click "Connect" under WebSocket URL for real-time bidirectional streaming
   - **SSE (Server-Sent Events):** Click "Connect" under SSE URL for interactive streaming
   - Note: WebSocket and SSE are mutually exclusive - only one can be active at a time
5. Type a message and click "send_content()" to send it. Try these examples:
   - "Hello! Can you explain what ADK streaming is?"
   - "Search for the latest news about Google's Agent Development Kit" (uses Google Search tool)
   - "What's the weather like today?" (uses Google Search tool)
6. Watch the streaming responses in the log area
7. Click "close()" to gracefully terminate the session

**What to observe:**
- **Tool Execution:** When the agent needs information, it automatically invokes the Google Search tool
  - Look for `executableCode` showing the search query
  - `codeExecutionResult` shows the search execution outcome
- **Streaming Events:**
  - Partial events (`"partial": true`) show text chunks in real-time
  - Each event contains metadata (invocationId, author, timestamp, actions)
  - Final event has `"role": "model"` with complete response
  - Turn completion signal (`"turnComplete": true`) marks the end

## Features

### Interactive SSE Support
The SSE endpoint (`/sse`) now supports bidirectional communication:
- **GET `/sse`**: Opens an SSE connection and streams events from the agent
- **POST `/sse-send`**: Send messages to an active SSE session via `LiveRequestQueue.send_content()`
  - Request body: `{"session_id": "demo-session", "message": "your message"}`
- **POST `/sse-close`**: Gracefully close an active SSE session via `LiveRequestQueue.close()`
  - Request body: `{"session_id": "demo-session"}`

This enables interactive communication over SSE, similar to WebSocket, but using standard HTTP POST requests for sending messages.

### Google Search Tool Integration
The agent is equipped with the built-in `google_search` tool, enabling it to:
- Retrieve real-time information from the web
- Answer questions requiring current data
- Provide up-to-date facts and statistics
- Search for specific topics or latest news

The tool is automatically invoked when the agent determines it needs external information to answer your query.

### Modular Architecture
- **Agent Module:** The agent definition is cleanly separated in `agent/agent.py`, making it easy to:
  - Modify agent behavior independently
  - Add or remove tools
  - Reuse the agent in other applications
  - Test agent logic separately

- **Static UI:** The HTML interface is served from `static/index.html`, providing:
  - Easier frontend modifications
  - Better separation of concerns
  - Reduced Python file size
  - Standard web development workflow

## Notes

- The server uses `InMemorySessionService` and creates a demo session (`user_id=demo-user`, `session_id=demo-session`).
- By default, the sample uses text-only responses. You can toggle transcription, VAD, proactivity, affective dialog, and session resumption using the UI checkboxes.
- The WebSocket accepts either plain text (converted to `Content`) or JSON that matches `LiveRequest` (for activity signals/blobs/close).
- **Connection mutual exclusivity:** WebSocket and SSE connections cannot be active simultaneously. The UI enforces this by disabling the connect buttons when one type is active.
- **LiveRequestQueue controls:** The `send_content()` and `close()` buttons work with both WebSocket (direct send) and SSE (via POST endpoints).

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
