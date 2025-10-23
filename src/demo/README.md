# ADK Bidi-streaming demo app

This sample demonstrates the core ADK Bidi-streaming APIs.

## What's included

### Application Package (`app/`)
- **`app/main.py`**: FastAPI application with WebSocket and SSE endpoints
  - WebSocket endpoint at `/ws` for real-time two-way communication
  - SSE endpoint at `/sse` for interactive streaming with bidirectional communication
  - POST endpoints `/sse-send` and `/sse-close` for sending messages and closing SSE sessions
  - Dynamic credential configuration (Gemini API or Vertex AI)
  - Serves static UI from `app/static/index.html`
  - Mutual exclusivity: WebSocket and SSE connections cannot be active simultaneously
- **`app/bidi_streaming.py`**: ADK bidirectional streaming session management
  - Handles all ADK streaming API interactions (LiveRequestQueue, Runner.run_live())
  - Session management and RunConfig creation
  - Clean separation of ADK logic from FastAPI transport layer
- **`app/agent/agent.py`**: Modular agent definition with Google Search integration
  - `create_streaming_agent()` function to instantiate the agent
  - Built-in Google Search tool for real-time web search capabilities
  - Clean separation of agent logic from application code
- **`app/static/index.html`**: Interactive web UI for testing bidirectional streaming
  - WebSocket and SSE connection management with mutual exclusivity
  - LiveRequestQueue controls: `send_content()` and `close()` buttons work with both WebSocket and SSE
  - Live streaming response viewer with color-coded event types
  - RunConfig toggles (transcription, VAD, proactivity, affective dialog, session resumption)
  - Support for both Gemini API and Vertex AI backends
  - Model selection dropdown with Live-capable models

## Project Structure

```
src/demo/
├── app/
│   ├── __init__.py          # App package initialization
│   ├── agent/
│   │   ├── __init__.py      # Agent module initialization
│   │   └── agent.py         # Agent definition with Google Search tool
│   ├── static/
│   │   └── index.html       # Web UI for testing streaming
│   ├── main.py              # FastAPI application with WebSocket/SSE endpoints
│   └── bidi_streaming.py    # ADK streaming API interactions
├── run.sh                   # Automated setup and run script
└── README.md                # This file
```

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

## Using the web interface

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
