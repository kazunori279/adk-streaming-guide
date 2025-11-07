# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a comprehensive technical guide for building real-time, bidirectional streaming AI applications using Google's Agent Development Kit (ADK). The repository contains detailed documentation covering ADK's streaming architecture and a working demo application showcasing bidirectional communication with Gemini models.

## Project Structure

```text
adk-streaming-guide/
├── .github/                       # GitHub configuration
│   ├── workflows/                # Automated workflows
│   │   ├── adk-version-monitor.yml    # Monitor ADK releases
│   │   └── claude-code-reviewer.yml   # Automated doc reviews
│   ├── current_adk_version.txt   # Tracked ADK version
│   └── WORKFLOWS.md              # Workflow documentation
├── docs/                          # Multi-part documentation guide
│   ├── part1_intro.md            # Introduction to ADK Bidi-streaming
│   ├── part2_live_request_queue.md  # Unified message processing
│   ├── part3_run_live.md         # Event handling with run_live()
│   ├── part4_run_config.md       # RunConfig configuration
│   ├── part5_audio_and_video.md  # Multimodal features
│   └── reviews/                  # Documentation review reports
├── src/bidi-demo/                # Working demo application
│   ├── app/
│   │   ├── main.py              # FastAPI WebSocket server
│   │   ├── static/              # Frontend HTML/JS/CSS
│   │   └── .env                 # Environment configuration
│   └── pyproject.toml           # Python dependencies
├── tests/e2e/                    # End-to-end tests with Chrome DevTools
├── STYLES.md                     # Documentation and code style guide
└── AGENTS.md                     # Claude Code agent configuration
```

## Key Architecture Concepts

This guide covers ADK's bidirectional streaming architecture, which consists of four key phases:

1. **Application Initialization** (once at startup): Create `Agent`, `SessionService`, and `Runner`
2. **Session Initialization** (per user connection): Get/create `Session`, create `RunConfig` and `LiveRequestQueue`, start `run_live()` event loop
3. **Bidi-streaming** (active communication): Concurrent upstream (client → queue) and downstream (events → client) tasks
4. **Termination**: Close `LiveRequestQueue`, disconnect from Live API session

The upstream/downstream concurrent task pattern is fundamental to all streaming applications in this codebase.

## Documentation Standards

**CRITICAL**: All documentation must follow the comprehensive style guidelines in `STYLES.md`.

## Running the Demo Application

The `src/bidi-demo/` directory contains a working FastAPI application demonstrating ADK bidirectional streaming.

### Setup

```bash
# Navigate to demo directory
cd src/bidi-demo

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment variables
# Edit app/.env and set:
# - GOOGLE_API_KEY (for Gemini Live API) OR
# - GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION (for Vertex AI Live API)
# - GOOGLE_GENAI_USE_VERTEXAI (TRUE for Vertex AI, FALSE or unset for Gemini Live API)
```

### Running the Server

```bash
# From src/bidi-demo/ directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open <http://localhost:8000> in your browser.

### Key Demo Features

- **WebSocket endpoint**: `/ws/{user_id}/{session_id}` for bidirectional streaming
- **Concurrent tasks**: Upstream (WebSocket → LiveRequestQueue) and downstream (run_live() → WebSocket)
- **Multimodal support**: Text and audio input/output
- **Audio transcription**: Real-time transcription of both input and output
- **Session resumption**: Configured via RunConfig

## Testing

**Test Documentation:**

- **Detailed E2E Procedures**: `src/bidi-demo/tests/test_bidi_demo_e2e.md`
- **Manual Test Procedures**: `src/bidi-demo/tests/test_bidi_demo.md` (manual testing workflow for Claude Code)
- **Test Reports**: `src/bidi-demo/tests/test_log_*.md` (timestamped test artifacts)

All test artifacts including server logs, screenshots, and test reports are preserved in timestamped directories for review and analysis.

## GitHub Actions Workflows

This repository includes automated workflows for maintaining documentation compatibility with ADK updates:

### ADK Version Monitor

- **Schedule**: Runs every 12 hours to check for new ADK releases on PyPI
- **What it does**: When a new version is detected, creates a parent issue and 5 sub-issues (one per documentation part)
- **Location**: `.github/workflows/adk-version-monitor.yml`

### Claude Code Reviewer

- **Trigger**: Automatically responds to issues with the `adk-version-update` label that mention `@claude`
- **What it does**: Uses the `adk-reviewer` agent to analyze documentation for compatibility issues and posts findings
- **Location**: `.github/workflows/claude-code-reviewer.yml`

### Setup Required

To enable these workflows:

1. Install the [Claude GitHub App](https://github.com/apps/claude-code) on this repository
2. Add `ANTHROPIC_API_KEY` to repository secrets (Settings → Secrets and variables → Actions)
3. The workflows will automatically run on schedule and when triggered by issue creation

See `.github/WORKFLOWS.md` for complete setup instructions and workflow details.

## Claude Code Skills

This repository provides specialized knowledge through skill configuration files in `.claude/skills/`:

- **`bidi`** (`.claude/skills/bidi/SKILL.md`): Expert in ADK Bidi-streaming documentation and implementation
- **`docs-lint`**: Documentation consistency and style reviewer (if implemented)

### Using Skills

To activate a skill, reference it directly:

- **For bidi expertise**: Say "use bidi skill" or "access the bidi skill"
- **For documentation review**: Say "use docs-lint skill"

The skills are implemented through repository documentation and configuration files that Claude reads directly.

## Common Tasks

### Adding Documentation Content

1. Read STYLES.md completely to understand all style requirements
2. Identify the correct part file (part1-part5)
3. Follow the section hierarchy and ordering patterns
4. Use consistent terminology (e.g., "Live API" for both platforms, "bidirectional streaming")
5. Add code examples with appropriate commenting level (teaching vs production)
6. Include cross-references to related sections
7. Use the docs-lint skill to review changes

### Modifying Demo Application

1. The demo app follows the 4-phase lifecycle pattern
2. Maintain upstream/downstream task separation
3. Ensure proper error handling in `try/finally` blocks
4. Always close `LiveRequestQueue` in the `finally` block
5. Test with both text and audio modalities
6. Verify WebSocket connection handling

### Running Documentation Reviews

Use the `docs-lint` skill to perform comprehensive documentation reviews:

```python
# The skill will analyze structure, style, cross-references, code examples, and more
# Review reports are saved in docs/reviews/
```

## Reference Documentation

- **ADK Documentation**: <https://google.github.io/adk-docs/>
- **Gemini Live API**: <https://ai.google.dev/gemini-api/docs/live>
- **Vertex AI Live API**: <https://cloud.google.com/vertex-ai/generative-ai/docs/live-api>
- **ADK Python Repository**: <https://github.com/google/adk-python>

## Git Workflow

This repository follows conventional commits. When creating commits, use the format specified in AGENTS.md with types: `feat`, `fix`, `docs`, `refactor`, `chore`.
