# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **bidirectional streaming documentation project** for Google's Agent Development Kit (ADK) Python library. It contains:

1. **ADK Python Package** (`/adk-python/`) - Complete Google ADK codebase (v1.3.0)
2. **Streaming Documentation** (`/adk-docs/`) - MkDocs-formatted streaming programming guide  
3. **Live Examples** (`/adk-docs/adk-streaming/`) - Working FastAPI streaming application

## Development Commands

### Documentation Development (MkDocs)
```bash
# Navigate to docs directory
cd adk-docs

# Install dependencies (if needed)
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

### Streaming Example Application
```bash
# Navigate to streaming app
cd adk-docs/adk-streaming/app

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI streaming application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### ADK Python Development
```bash
# Navigate to ADK package
cd adk-python

# Run agent samples
python -m google.adk.cli run contributing/samples/hello_world

# Run agent with development UI
adk run contributing/samples/hello_world

# Evaluate agent
adk eval contributing/samples/hello_world contributing/samples/hello_world/test.evalset.json

# Create new agent template
adk create my_new_agent

# Run unit tests
pytest tests/unittests/

# Run integration tests  
pytest tests/integration/
```

## Architecture

### Core ADK Components
- **Agents**: Main orchestration units (`LlmAgent`, `SequentialAgent`, `ParallelAgent`)
- **Tools**: Function integrations (Google Search, BigQuery, OpenAPI, MCP tools)
- **Runners**: Execution engines (`InMemoryRunner` for development, `VertexAiRunner` for production)
- **Sessions**: State management across conversations
- **Flows**: LLM processing pipelines with streaming support

### Streaming Architecture
The streaming system uses:
- **LiveRequestQueue**: Bidirectional communication channel
- **Server-Sent Events (SSE)**: Real-time data streaming to clients
- **Audio Processing**: PCM encoding for voice streaming
- **WebSocket Support**: Alternative transport layer

### Key Patterns

#### Basic Agent Definition
```python
from google.adk.agents import Agent
from google.adk.tools import google_search

agent = Agent(
    name="agent_name",
    model="gemini-2.0-flash",
    instruction="Agent behavior instructions",
    tools=[google_search],
    sub_agents=[child_agents]  # For multi-agent systems
)
```

#### Streaming Setup
```python
from google.adk.agents import LiveRequestQueue
from google.adk.runners import InMemoryRunner

live_request_queue = LiveRequestQueue()
live_events = runner.run_live(
    session=session,
    live_request_queue=live_request_queue,
    run_config=run_config
)
```

## Documentation Format

- **Format**: MkDocs with Material theme
- **Diagrams**: Mermaid diagrams for architecture visualization
- **Code Examples**: Organized in `/src` with chapter/section numbering (e.g., `1-1-1_hello_world.py`)
- **Style**: Readable programming guide format with minimal inline code blocks

## Environment Setup

### Required Environment Variables
```bash
# Core requirement for Gemini models
GOOGLE_API_KEY=your_gemini_api_key

# Optional for Google Cloud features
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Dependencies
- **Core**: `google-adk`, `fastapi`, `uvicorn`
- **Development**: `pytest`, `python-dotenv`
- **Documentation**: `mkdocs`, `mkdocs-material`

## File Structure

```
/adk-python/               # Main ADK Python package
├── src/google/adk/        # Core ADK modules
├── contributing/samples/  # Example agents
└── tests/                # Unit and integration tests

/adk-docs/                # Documentation project
├── streaming/            # Streaming guide content
├── adk-streaming/app/    # Live streaming example
└── src/                  # Code examples for guide

/README.md               # Project requirements and overview
```

## Development Notes

- **Code-First Philosophy**: Agents defined in Python, not configuration
- **Model Agnostic**: Supports Gemini (optimized), Anthropic, LiteLLM, Ollama
- **Testing**: Comprehensive unit tests with `.evalset.json` evaluation files
- **Multi-Agent**: Hierarchical agent systems with A2A protocol support
- **Tool Integration**: Rich ecosystem of pre-built tools for Google services